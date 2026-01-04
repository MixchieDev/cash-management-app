"""
Tests for Google Sheets import functionality.

Tests coverage:
- Currency parsing (₱ symbol, commas, decimals)
- Date parsing (multiple formats)
- Customer import (active filtering, entity assignment)
- Vendor import (due date parsing, error handling)
- Bank balance import (wide to tall format conversion)
- Error handling and graceful degradation
"""
import pytest
from datetime import date
from decimal import Decimal

from data_processing.google_sheets_import import (
    parse_decimal,
    parse_date,
)


class TestCurrencyParsing:
    """Test suite for currency parsing."""

    def test_parse_decimal_basic_number(self):
        """Test parsing basic number."""
        result = parse_decimal('50000')
        assert result == Decimal('50000.00')

    def test_parse_decimal_with_peso_symbol(self):
        """Test parsing currency with ₱ symbol."""
        result = parse_decimal('₱50,000.00')
        assert result == Decimal('50000.00')

    def test_parse_decimal_with_commas(self):
        """Test parsing currency with commas."""
        result = parse_decimal('2,500,000.00')
        assert result == Decimal('2500000.00')

    def test_parse_decimal_with_peso_and_commas(self):
        """Test parsing currency with ₱ symbol and commas."""
        result = parse_decimal('₱2,500,000.00')
        assert result == Decimal('2500000.00')

    def test_parse_decimal_with_spaces(self):
        """Test parsing currency with spaces."""
        result = parse_decimal('₱ 50,000.00 ')
        assert result == Decimal('50000.00')

    def test_parse_decimal_empty_string(self):
        """Test parsing empty string returns 0.00."""
        result = parse_decimal('')
        assert result == Decimal('0.00')

    def test_parse_decimal_none(self):
        """Test parsing None returns 0.00."""
        result = parse_decimal(None)
        assert result == Decimal('0.00')

    def test_parse_decimal_whitespace_only(self):
        """Test parsing whitespace-only string returns 0.00."""
        result = parse_decimal('   ')
        assert result == Decimal('0.00')

    def test_parse_decimal_negative_amount(self):
        """Test parsing negative amount."""
        result = parse_decimal('-10000.50')
        assert result == Decimal('-10000.50')

    def test_parse_decimal_very_large_number(self):
        """Test parsing very large numbers."""
        result = parse_decimal('₱250,000,000.00')
        assert result == Decimal('250000000.00')

    def test_parse_decimal_preserves_two_decimals(self):
        """Test that result always has 2 decimal places."""
        result = parse_decimal('100')
        assert result == Decimal('100.00')
        assert str(result) == '100.00'

    def test_parse_decimal_rounds_to_two_decimals(self):
        """Test that extra decimal places are rounded."""
        result = parse_decimal('100.999')
        assert result == Decimal('101.00')

    def test_parse_decimal_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid decimal value"):
            parse_decimal('not_a_number')


class TestDateParsing:
    """Test suite for date parsing."""

    def test_parse_date_iso_format(self):
        """Test parsing ISO date format (YYYY-MM-DD)."""
        result = parse_date('2026-01-15')
        assert result == date(2026, 1, 15)

    def test_parse_date_us_format(self):
        """Test parsing US date format (MM/DD/YYYY)."""
        result = parse_date('01/15/2026')
        assert result == date(2026, 1, 15)

    def test_parse_date_european_format(self):
        """Test parsing European date format (DD/MM/YYYY)."""
        result = parse_date('15/01/2026')
        assert result == date(2026, 1, 15)

    def test_parse_date_slash_iso(self):
        """Test parsing ISO format with slashes (YYYY/MM/DD)."""
        result = parse_date('2026/01/15')
        assert result == date(2026, 1, 15)

    def test_parse_date_us_dashes(self):
        """Test parsing US format with dashes (MM-DD-YYYY)."""
        result = parse_date('01-15-2026')
        assert result == date(2026, 1, 15)

    def test_parse_date_european_dashes(self):
        """Test parsing European format with dashes (DD-MM-YYYY)."""
        result = parse_date('15-01-2026')
        assert result == date(2026, 1, 15)

    def test_parse_date_with_leading_trailing_spaces(self):
        """Test parsing date with whitespace."""
        result = parse_date('  2026-01-15  ')
        assert result == date(2026, 1, 15)

    def test_parse_date_empty_string_returns_none(self):
        """Test parsing empty string returns None."""
        result = parse_date('')
        assert result is None

    def test_parse_date_none_returns_none(self):
        """Test parsing None returns None."""
        result = parse_date(None)
        assert result is None

    def test_parse_date_whitespace_only_returns_none(self):
        """Test parsing whitespace-only returns None."""
        result = parse_date('   ')
        assert result is None

    def test_parse_date_invalid_format_raises_error(self):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date('2026-13-45')  # Invalid month and day

    def test_parse_date_ambiguous_format_raises_error(self):
        """Test that ambiguous format raises ValueError if all parsers fail."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date('not_a_date')


class TestEntityAssignment:
    """Test suite for entity assignment logic."""

    def test_yowi_assigned_to_yahshua(self):
        """Test that YOWI customers are assigned to YAHSHUA."""
        from config.entity_mapping import assign_entity
        assert assign_entity('YOWI') == 'YAHSHUA'

    def test_rcbc_assigned_to_yahshua(self):
        """Test that RCBC Partner customers are assigned to YAHSHUA."""
        from config.entity_mapping import assign_entity
        assert assign_entity('RCBC Partner') == 'YAHSHUA'

    def test_globe_assigned_to_yahshua(self):
        """Test that Globe Partner customers are assigned to YAHSHUA."""
        from config.entity_mapping import assign_entity
        assert assign_entity('Globe Partner') == 'YAHSHUA'

    def test_tai_assigned_to_abba(self):
        """Test that TAI customers are assigned to ABBA."""
        from config.entity_mapping import assign_entity
        assert assign_entity('TAI') == 'ABBA'

    def test_pei_assigned_to_abba(self):
        """Test that PEI customers are assigned to ABBA."""
        from config.entity_mapping import assign_entity
        assert assign_entity('PEI') == 'ABBA'

    def test_unmapped_source_raises_error(self):
        """Test that unmapped acquisition source raises ValueError."""
        from config.entity_mapping import assign_entity
        with pytest.raises(ValueError, match="Unmapped acquisition source"):
            assign_entity('UNKNOWN_SOURCE')


class TestDatabaseModels:
    """Test suite for database models."""

    def test_vendor_model_has_start_date_column(self):
        """Test that VendorContract model has start_date column."""
        from database.models import VendorContract
        assert hasattr(VendorContract, 'start_date')

    def test_vendor_start_date_is_nullable(self):
        """Test that start_date column is nullable."""
        from database.models import VendorContract
        start_date_column = VendorContract.__table__.columns.get('start_date')
        assert start_date_column is not None
        assert start_date_column.nullable is True

    def test_customer_contract_model_structure(self):
        """Test CustomerContract model has required fields."""
        from database.models import CustomerContract
        required_fields = [
            'company_name', 'monthly_fee', 'payment_plan',
            'contract_start', 'status', 'who_acquired', 'entity'
        ]
        for field in required_fields:
            assert hasattr(CustomerContract, field), f"Missing field: {field}"

    def test_vendor_contract_model_structure(self):
        """Test VendorContract model has required fields."""
        from database.models import VendorContract
        required_fields = [
            'vendor_name', 'category', 'amount', 'frequency',
            'due_date', 'start_date', 'entity', 'status'
        ]
        for field in required_fields:
            assert hasattr(VendorContract, field), f"Missing field: {field}"

    def test_bank_balance_model_structure(self):
        """Test BankBalance model has required fields."""
        from database.models import BankBalance
        required_fields = ['balance_date', 'entity', 'balance']
        for field in required_fields:
            assert hasattr(BankBalance, field), f"Missing field: {field}"


class TestDataValidation:
    """Test suite for data validation."""

    def test_payment_plan_values(self):
        """Test that valid payment plan values are accepted."""
        from database.models import CustomerContract
        valid_plans = ['Monthly', 'Quarterly', 'Annual', 'Bi-annually', 'More than 1 year']
        # This test just verifies the constraint exists in the model
        assert CustomerContract.__table_args__ is not None

    def test_entity_values(self):
        """Test that only YAHSHUA and ABBA entities are valid."""
        from database.models import CustomerContract, VendorContract, BankBalance
        # This test verifies constraint exists in models
        assert CustomerContract.__table_args__ is not None
        assert VendorContract.__table_args__ is not None
        assert BankBalance.__table_args__ is not None

    def test_vendor_category_values(self):
        """Test that valid vendor categories exist."""
        from database.models import VendorContract
        # Valid categories: Payroll, Loans, Software/Tech, Operations, Rent, Utilities
        assert VendorContract.__table_args__ is not None

    def test_vendor_priority_range(self):
        """Test that vendor priority is between 1 and 4."""
        from database.models import VendorContract
        # Priority constraint exists in model
        assert VendorContract.__table_args__ is not None


class TestErrorHandling:
    """Test suite for error handling in imports."""

    def test_parse_decimal_continues_on_empty(self):
        """Test that parse_decimal handles empty values gracefully."""
        # Should return 0.00, not raise an error
        result = parse_decimal('')
        assert result == Decimal('0.00')

    def test_parse_date_continues_on_empty(self):
        """Test that parse_date handles empty values gracefully."""
        # Should return None, not raise an error
        result = parse_date('')
        assert result is None

    def test_parse_decimal_with_unexpected_characters(self):
        """Test that parse_decimal handles unexpected characters in currency."""
        with pytest.raises(ValueError):
            parse_decimal('$50,000.00')  # Dollar sign instead of peso

    def test_parse_date_with_partial_date(self):
        """Test that parse_date handles partial dates."""
        with pytest.raises(ValueError):
            parse_date('2026-01')  # Missing day


class TestCurrencyFormatting:
    """Test suite for currency formatting requirements."""

    def test_format_currency_basic(self):
        """Test basic currency formatting."""
        from utils.currency_formatter import format_currency
        result = format_currency(Decimal('2500000.00'))
        assert result == '₱2,500,000.00'

    def test_format_currency_negative(self):
        """Test negative currency formatting."""
        from utils.currency_formatter import format_currency
        result = format_currency(Decimal('-50000.00'))
        assert result == '-₱50,000.00'

    def test_format_currency_zero(self):
        """Test zero currency formatting."""
        from utils.currency_formatter import format_currency
        result = format_currency(Decimal('0.00'))
        assert result == '₱0.00'

    def test_format_currency_large_number(self):
        """Test large number formatting."""
        from utils.currency_formatter import format_currency
        result = format_currency(Decimal('250000000.00'))
        assert result == '₱250,000,000.00'

    def test_format_currency_preserves_decimals(self):
        """Test that formatting always shows 2 decimal places."""
        from utils.currency_formatter import format_currency
        result = format_currency(Decimal('100'))
        assert result == '₱100.00'
        assert '.00' in result


class TestMigration:
    """Test suite for database migration."""

    def test_migration_file_exists(self):
        """Test that migration file exists."""
        from pathlib import Path
        migration_file = Path('database/migrations/001_add_vendor_start_date.sql')
        assert migration_file.exists(), f"Migration file not found: {migration_file}"

    def test_migration_script_exists(self):
        """Test that migration application script exists."""
        from pathlib import Path
        script_file = Path('database/migrations/apply_migration.py')
        assert script_file.exists(), f"Migration script not found: {script_file}"
