"""
Tests for contract CRUD operations in database/queries.py.
Tests create, update, soft-delete for customers, vendors, and bank balances.
"""
import pytest
from datetime import date
from decimal import Decimal

from database.queries import (
    create_customer_contract, update_customer_contract, delete_customer_contract,
    get_customers, get_customer_by_id,
    create_vendor_contract, update_vendor_contract, delete_vendor_contract,
    get_vendors, get_vendor_by_id,
    create_bank_balance, update_bank_balance, delete_bank_balance,
    get_all_bank_balances, get_latest_bank_balance,
)


# ═══════════════════════════════════════════════════════════════════
# CUSTOMER CONTRACT CRUD TESTS
# ═══════════════════════════════════════════════════════════════════

class TestCreateCustomerContract:
    """Tests for creating customer contracts."""

    def test_create_customer_contract_success(self, sample_customer_data):
        """Create a customer contract with valid data."""
        result = create_customer_contract(sample_customer_data)
        assert result['id'] is not None
        assert result['company_name'] == 'Test Company Inc.'
        assert result['monthly_fee'] == Decimal('50000.00')
        assert result['payment_plan'] == 'Monthly'
        assert result['entity'] == 'YAHSHUA'
        assert result['status'] == 'Active'
        assert result['source'] == 'manual'

    def test_create_customer_contract_with_source(self, sample_customer_data):
        """Create with explicit source tracking."""
        sample_customer_data['source'] = 'google_sheets'
        sample_customer_data['created_by'] = 'admin'
        result = create_customer_contract(sample_customer_data)
        assert result['source'] == 'google_sheets'

    def test_create_customer_contract_validation_error(self):
        """Reject invalid customer data."""
        with pytest.raises(ValueError, match="Validation failed"):
            create_customer_contract({
                'company_name': 'Test',
                'monthly_fee': Decimal('100'),
                'payment_plan': 'INVALID_PLAN',
                'contract_start': date(2026, 1, 1),
                'status': 'Active',
                'who_acquired': 'YOWI',
                'entity': 'YAHSHUA',
            })

    def test_create_customer_contract_missing_fields(self):
        """Reject customer data with missing required fields."""
        with pytest.raises(ValueError, match="Validation failed"):
            create_customer_contract({
                'company_name': 'Test',
            })

    def test_create_customer_contract_negative_fee(self):
        """Reject negative monthly fee."""
        with pytest.raises(ValueError, match="Validation failed"):
            create_customer_contract({
                'company_name': 'Test',
                'monthly_fee': Decimal('-100'),
                'payment_plan': 'Monthly',
                'contract_start': date(2026, 1, 1),
                'status': 'Active',
                'who_acquired': 'YOWI',
                'entity': 'YAHSHUA',
            })


class TestUpdateCustomerContract:
    """Tests for updating customer contracts."""

    def test_update_customer_contract_success(self, sample_customer_data):
        """Update a customer's monthly fee."""
        created = create_customer_contract(sample_customer_data)
        updated = update_customer_contract(created['id'], {
            'monthly_fee': Decimal('75000.00'),
        })
        assert updated['monthly_fee'] == Decimal('75000.00')
        assert updated['company_name'] == 'Test Company Inc.'

    def test_update_customer_contract_status(self, sample_customer_data):
        """Update a customer's status."""
        created = create_customer_contract(sample_customer_data)
        updated = update_customer_contract(created['id'], {
            'status': 'Inactive',
        })
        assert updated['status'] == 'Inactive'

    def test_update_customer_contract_not_found(self):
        """Raise error when customer not found."""
        with pytest.raises(ValueError, match="not found"):
            update_customer_contract(99999, {'monthly_fee': Decimal('100')})

    def test_update_customer_contract_invalid_data(self, sample_customer_data):
        """Reject invalid update data."""
        created = create_customer_contract(sample_customer_data)
        with pytest.raises(ValueError, match="Validation failed"):
            update_customer_contract(created['id'], {
                'payment_plan': 'INVALID',
            })


class TestDeleteCustomerContract:
    """Tests for soft-deleting customer contracts."""

    def test_delete_customer_contract_soft_delete(self, sample_customer_data):
        """Soft delete sets status to Cancelled."""
        created = create_customer_contract(sample_customer_data)
        result = delete_customer_contract(created['id'])
        assert result is True

        # Should not appear in active customers
        active = get_customers(entity='YAHSHUA', status='Active')
        assert not any(c['id'] == created['id'] for c in active)

        # Should still exist with Cancelled status
        customer = get_customer_by_id(created['id'])
        assert customer is not None
        assert customer['status'] == 'Cancelled'

    def test_delete_customer_contract_not_found(self):
        """Return False when customer not found."""
        assert delete_customer_contract(99999) is False


# ═══════════════════════════════════════════════════════════════════
# VENDOR CONTRACT CRUD TESTS
# ═══════════════════════════════════════════════════════════════════

class TestCreateVendorContract:
    """Tests for creating vendor contracts."""

    def test_create_vendor_contract_success(self, sample_vendor_data):
        """Create a vendor contract with valid data."""
        result = create_vendor_contract(sample_vendor_data)
        assert result['id'] is not None
        assert result['vendor_name'] == 'Test Vendor LLC'
        assert result['category'] == 'Software/Tech'
        assert result['amount'] == Decimal('10000.00')
        assert result['frequency'] == 'Monthly'
        assert result['entity'] == 'YAHSHUA'
        assert result['source'] == 'manual'

    def test_create_vendor_contract_with_dates(self, sample_vendor_data):
        """Create vendor with start and end dates."""
        sample_vendor_data['start_date'] = date(2026, 3, 1)
        sample_vendor_data['end_date'] = date(2026, 12, 31)
        result = create_vendor_contract(sample_vendor_data)
        assert result['start_date'] == date(2026, 3, 1)
        assert result['end_date'] == date(2026, 12, 31)

    def test_create_vendor_contract_validation_error(self):
        """Reject invalid vendor data."""
        with pytest.raises(ValueError, match="Validation failed"):
            create_vendor_contract({
                'vendor_name': 'Test',
                'category': 'INVALID_CATEGORY',
                'amount': Decimal('100'),
                'frequency': 'Monthly',
                'due_date': date(2026, 1, 15),
                'entity': 'YAHSHUA',
            })


class TestUpdateVendorContract:
    """Tests for updating vendor contracts."""

    def test_update_vendor_contract_success(self, sample_vendor_data):
        """Update a vendor's amount."""
        created = create_vendor_contract(sample_vendor_data)
        updated = update_vendor_contract(created['id'], {
            'amount': Decimal('15000.00'),
        })
        assert updated['amount'] == Decimal('15000.00')

    def test_update_vendor_contract_not_found(self):
        """Raise error when vendor not found."""
        with pytest.raises(ValueError, match="not found"):
            update_vendor_contract(99999, {'amount': Decimal('100')})


class TestDeleteVendorContract:
    """Tests for soft-deleting vendor contracts."""

    def test_delete_vendor_contract_soft_delete(self, sample_vendor_data):
        """Soft delete sets status to Inactive."""
        created = create_vendor_contract(sample_vendor_data)
        result = delete_vendor_contract(created['id'])
        assert result is True

        vendor = get_vendor_by_id(created['id'])
        assert vendor is not None
        assert vendor['status'] == 'Inactive'

    def test_delete_vendor_contract_not_found(self):
        """Return False when vendor not found."""
        assert delete_vendor_contract(99999) is False


# ═══════════════════════════════════════════════════════════════════
# BANK BALANCE CRUD TESTS
# ═══════════════════════════════════════════════════════════════════

class TestCreateBankBalance:
    """Tests for creating bank balances."""

    def test_create_bank_balance_success(self):
        """Create a bank balance entry."""
        # Use a unique date to avoid UniqueConstraint conflicts with existing data
        data = {
            'balance_date': date(2099, 12, 31),
            'entity': 'YAHSHUA',
            'balance': Decimal('5000000.00'),
            'source': 'Manual Entry',
            'notes': 'Test balance',
        }
        result = create_bank_balance(data)
        assert result['id'] is not None
        assert result['balance'] == Decimal('5000000.00')
        assert result['entity'] == 'YAHSHUA'
        # Cleanup
        delete_bank_balance(result['id'])

    def test_create_bank_balance_validation_error(self):
        """Reject invalid bank balance data."""
        with pytest.raises(ValueError, match="Validation failed"):
            create_bank_balance({
                'balance_date': 'not-a-date',
                'entity': 'YAHSHUA',
                'balance': Decimal('100'),
            })


class TestGetAllBankBalances:
    """Tests for listing bank balances."""

    def test_get_all_bank_balances(self):
        """Get all bank balances for an entity."""
        balances = get_all_bank_balances(entity='YAHSHUA')
        assert len(balances) >= 1
        assert all(b['entity'] == 'YAHSHUA' for b in balances)


class TestUpdateBankBalance:
    """Tests for updating bank balances."""

    def test_update_bank_balance_success(self):
        """Update a bank balance amount."""
        data = {
            'balance_date': date(2099, 11, 30),
            'entity': 'YAHSHUA',
            'balance': Decimal('5000000.00'),
            'source': 'Manual Entry',
        }
        created = create_bank_balance(data)
        updated = update_bank_balance(created['id'], {
            'balance': Decimal('6000000.00'),
        })
        assert updated['balance'] == Decimal('6000000.00')
        # Cleanup
        delete_bank_balance(created['id'])

    def test_update_bank_balance_not_found(self):
        """Raise error when balance not found."""
        with pytest.raises(ValueError, match="not found"):
            update_bank_balance(99999, {'balance': Decimal('100')})


class TestDeleteBankBalance:
    """Tests for deleting bank balances."""

    def test_delete_bank_balance_success(self):
        """Hard delete a bank balance."""
        data = {
            'balance_date': date(2099, 10, 31),
            'entity': 'YAHSHUA',
            'balance': Decimal('5000000.00'),
            'source': 'Manual Entry',
        }
        created = create_bank_balance(data)
        result = delete_bank_balance(created['id'])
        assert result is True

    def test_delete_bank_balance_not_found(self):
        """Return False when balance not found."""
        assert delete_bank_balance(99999) is False


# ═══════════════════════════════════════════════════════════════════
# STRUCTURED VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestStructuredValidation:
    """Tests for structured validation with field-level errors."""

    def test_customer_structured_validation_valid(self, sample_customer_data):
        """Valid data returns no errors."""
        from data_processing.data_validator import DataValidator
        is_valid, errors = DataValidator.validate_customer_contract_structured(sample_customer_data)
        assert is_valid is True
        assert errors == []

    def test_customer_structured_validation_missing_fields(self):
        """Missing fields return field-level error details."""
        from data_processing.data_validator import DataValidator
        is_valid, errors = DataValidator.validate_customer_contract_structured({})
        assert is_valid is False
        assert len(errors) > 0
        assert all('field' in e and 'message' in e for e in errors)

    def test_vendor_structured_validation_valid(self, sample_vendor_data):
        """Valid vendor data returns no errors."""
        from data_processing.data_validator import DataValidator
        is_valid, errors = DataValidator.validate_vendor_contract_structured(sample_vendor_data)
        assert is_valid is True
        assert errors == []

    def test_vendor_structured_validation_invalid_category(self):
        """Invalid category returns field-level error."""
        from data_processing.data_validator import DataValidator
        is_valid, errors = DataValidator.validate_vendor_contract_structured({
            'vendor_name': 'Test',
            'category': 'INVALID',
            'amount': Decimal('100'),
            'frequency': 'Monthly',
            'due_date': date(2026, 1, 1),
            'entity': 'YAHSHUA',
        })
        assert is_valid is False
        category_errors = [e for e in errors if e['field'] == 'category']
        assert len(category_errors) == 1

    def test_bank_balance_structured_validation_valid(self, sample_bank_balance):
        """Valid bank balance returns no errors."""
        from data_processing.data_validator import DataValidator
        is_valid, errors = DataValidator.validate_bank_balance_structured(sample_bank_balance)
        assert is_valid is True
        assert errors == []
