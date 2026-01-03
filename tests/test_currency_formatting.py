"""
Test suite for currency formatting.
Ensures all currency displays are ₱X,XXX.XX format.
"""
import pytest
from decimal import Decimal
from utils.currency_formatter import (
    format_currency,
    parse_currency,
    format_currency_compact,
    validate_currency_format
)


class TestCurrencyFormatting:
    """Test currency formatting functions."""

    def test_format_currency_basic(self):
        """Test basic currency formatting."""
        assert format_currency(Decimal('2500000')) == '₱2,500,000.00'
        assert format_currency(Decimal('0')) == '₱0.00'
        assert format_currency(Decimal('1234567.89')) == '₱1,234,567.89'

    def test_format_currency_negative(self):
        """Test formatting negative amounts."""
        assert format_currency(Decimal('-150000.50')) == '-₱150,000.50'
        assert format_currency(Decimal('-1000')) == '-₱1,000.00'

    def test_format_currency_rounding(self):
        """Test decimal rounding to 2 places."""
        assert format_currency(Decimal('1234.567')) == '₱1,234.57'  # Rounds up
        assert format_currency(Decimal('1234.561')) == '₱1,234.56'  # Rounds down
        assert format_currency(Decimal('999.995')) == '₱1,000.00'  # Rounds up

    def test_format_currency_from_float(self):
        """Test formatting from float (with precision handling)."""
        assert format_currency(2500000.00) == '₱2,500,000.00'
        assert format_currency(123.45) == '₱123.45'

    def test_format_currency_from_int(self):
        """Test formatting from integer."""
        assert format_currency(1000) == '₱1,000.00'
        assert format_currency(0) == '₱0.00'

    def test_format_currency_large_amounts(self):
        """Test formatting very large amounts."""
        assert format_currency(Decimal('250000000')) == '₱250,000,000.00'
        assert format_currency(Decimal('1000000000')) == '₱1,000,000,000.00'

    def test_format_currency_small_amounts(self):
        """Test formatting small amounts."""
        assert format_currency(Decimal('0.01')) == '₱0.01'
        assert format_currency(Decimal('1.00')) == '₱1.00'
        assert format_currency(Decimal('99.99')) == '₱99.99'

    def test_parse_currency(self):
        """Test parsing formatted currency back to Decimal."""
        assert parse_currency('₱2,500,000.00') == Decimal('2500000.00')
        assert parse_currency('₱0.00') == Decimal('0.00')
        assert parse_currency('-₱150,000.50') == Decimal('-150000.50')

    def test_format_currency_compact_thousands(self):
        """Test compact formatting for thousands."""
        assert format_currency_compact(Decimal('50000')) == '₱50.00K'
        assert format_currency_compact(Decimal('1500')) == '₱1.50K'

    def test_format_currency_compact_millions(self):
        """Test compact formatting for millions."""
        assert format_currency_compact(Decimal('2500000')) == '₱2.50M'
        assert format_currency_compact(Decimal('50000000')) == '₱50.00M'

    def test_format_currency_compact_billions(self):
        """Test compact formatting for billions."""
        assert format_currency_compact(Decimal('1500000000')) == '₱1.50B'
        assert format_currency_compact(Decimal('250000000000')) == '₱250.00B'

    def test_format_currency_compact_small_amounts(self):
        """Test compact formatting falls back to regular format for small amounts."""
        assert format_currency_compact(Decimal('999')) == '₱999.00'
        assert format_currency_compact(Decimal('500')) == '₱500.00'

    def test_validate_currency_format_valid(self):
        """Test validation of correctly formatted currency."""
        assert validate_currency_format('₱2,500,000.00') is True
        assert validate_currency_format('₱0.00') is True
        assert validate_currency_format('-₱150,000.50') is True
        assert validate_currency_format('₱1,234,567.89') is True

    def test_validate_currency_format_invalid(self):
        """Test validation rejects incorrectly formatted currency."""
        assert validate_currency_format('2500000') is False  # No symbol
        assert validate_currency_format('₱2,500,000') is False  # No decimals
        assert validate_currency_format('₱2500000.00') is False  # No commas
        assert validate_currency_format('₱2,500,000.0') is False  # Only 1 decimal
        assert validate_currency_format('P2,500,000.00') is False  # Wrong symbol

    def test_currency_precision_in_calculations(self):
        """Test that currency calculations maintain precision."""
        amount1 = Decimal('1234.56')
        amount2 = Decimal('7890.12')
        total = amount1 + amount2

        formatted = format_currency(total)
        assert formatted == '₱9,124.68'

        # Round-trip test
        parsed = parse_currency(formatted)
        assert parsed == total

    def test_payroll_amount_formatting(self):
        """Test formatting of critical payroll amounts."""
        assert format_currency(Decimal('1000000')) == '₱1,000,000.00'
        assert format_currency(Decimal('2000000')) == '₱2,000,000.00'

    def test_revenue_goal_formatting(self):
        """Test formatting of revenue goals."""
        assert format_currency(Decimal('50000000')) == '₱50,000,000.00'  # Starting
        assert format_currency(Decimal('250000000')) == '₱250,000,000.00'  # Target


class TestCurrencyEdgeCases:
    """Test edge cases and special scenarios."""

    def test_zero_amount(self):
        """Test zero amount formatting."""
        assert format_currency(Decimal('0')) == '₱0.00'
        assert format_currency(0) == '₱0.00'

    def test_very_small_fractional_amounts(self):
        """Test amounts smaller than 0.01."""
        # Should round to 0.01
        assert format_currency(Decimal('0.001')) == '₱0.00'
        assert format_currency(Decimal('0.009')) == '₱0.01'

    def test_negative_zero(self):
        """Test negative zero edge case."""
        assert format_currency(Decimal('-0.00')) == '₱0.00'

    def test_multiple_format_and_parse_cycles(self):
        """Test multiple format/parse cycles maintain precision."""
        original = Decimal('1234567.89')

        # Cycle 1
        formatted1 = format_currency(original)
        parsed1 = parse_currency(formatted1)

        # Cycle 2
        formatted2 = format_currency(parsed1)
        parsed2 = parse_currency(formatted2)

        # Should be identical
        assert parsed1 == parsed2 == original
        assert formatted1 == formatted2

    def test_consistency_across_input_types(self):
        """Test that Decimal, float, and int give same result."""
        amount = 50000

        from_decimal = format_currency(Decimal('50000'))
        from_float = format_currency(50000.00)
        from_int = format_currency(50000)

        assert from_decimal == from_float == from_int == '₱50,000.00'
