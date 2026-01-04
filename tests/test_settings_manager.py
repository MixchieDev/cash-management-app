"""
Tests for settings_manager.py - Editable Settings Feature
Tests CRUD operations, type conversion, audit logging, and convenience functions.

Test Categories:
1. HAPPY PATH - Normal operations work correctly
2. EDGE CASES - Boundary conditions, special values
3. ERROR HANDLING - Invalid inputs, database errors
"""
import pytest
from decimal import Decimal
from datetime import date
import json

from database.settings_manager import (
    get_setting,
    set_setting,
    get_settings_by_category,
    get_all_settings,
    reset_to_defaults,
    get_audit_log,
    init_settings_tables,
    get_payroll_config,
    get_payment_terms_config,
    get_entity_mapping,
    get_alert_thresholds,
    get_google_sheets_config,
    extract_spreadsheet_id,
    _convert_value,
    _serialize_value,
    DEFAULT_SETTINGS
)


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def setup_settings_tables():
    """Ensure settings tables exist before each test."""
    init_settings_tables()
    yield


# ═══════════════════════════════════════════════════════════════════
# HAPPY PATH TESTS - CRUD Operations
# ═══════════════════════════════════════════════════════════════════

class TestGetSetting:
    """Tests for get_setting() function."""

    def test_get_existing_setting_returns_correct_value(self):
        """Getting an existing setting should return its value."""
        # This should exist from defaults
        result = get_setting('payroll_yahshua_15th')
        assert result is not None
        assert isinstance(result, Decimal)

    def test_get_setting_returns_default_when_not_found(self):
        """Getting non-existent setting should return provided default."""
        result = get_setting('nonexistent_setting_xyz', default='my_default')
        assert result == 'my_default'

    def test_get_setting_falls_back_to_default_settings(self):
        """If not in DB, should fall back to DEFAULT_SETTINGS."""
        # Payment terms has a default
        result = get_setting('invoice_lead_days')
        assert result == 15  # Default from DEFAULT_SETTINGS

    def test_get_decimal_setting_returns_decimal_type(self):
        """Decimal settings should return Decimal type."""
        result = get_setting('payroll_yahshua_15th')
        assert isinstance(result, Decimal)

    def test_get_integer_setting_returns_int_type(self):
        """Integer settings should return int type."""
        result = get_setting('invoice_lead_days')
        assert isinstance(result, int)

    def test_get_json_setting_returns_dict(self):
        """JSON settings should return dict type."""
        result = get_setting('entity_mapping')
        assert isinstance(result, dict)


class TestSetSetting:
    """Tests for set_setting() function."""

    def test_set_new_setting_succeeds(self):
        """Setting a new value should succeed and return True."""
        result = set_setting(
            key='test_setting_new',
            value='test_value',
            setting_type='string',
            category='test',
            updated_by='TestUser'
        )
        assert result is True

    def test_set_setting_can_be_retrieved(self):
        """Set setting should be retrievable with get_setting."""
        set_setting('test_retrieve', 'my_value', 'string', 'test', updated_by='Test')
        result = get_setting('test_retrieve')
        assert result == 'my_value'

    def test_set_decimal_setting_stores_correctly(self):
        """Decimal values should be stored and retrieved correctly."""
        test_amount = Decimal('1500000.50')
        set_setting('test_decimal', test_amount, 'decimal', 'test', updated_by='Test')
        result = get_setting('test_decimal')
        assert result == test_amount
        assert isinstance(result, Decimal)

    def test_set_integer_setting_stores_correctly(self):
        """Integer values should be stored and retrieved correctly."""
        set_setting('test_integer', 42, 'integer', 'test', updated_by='Test')
        result = get_setting('test_integer')
        assert result == 42
        assert isinstance(result, int)

    def test_set_json_setting_stores_correctly(self):
        """JSON values should be stored and retrieved correctly."""
        test_data = {'key1': 'value1', 'key2': 'value2'}
        set_setting('test_json', test_data, 'json', 'test', updated_by='Test')
        result = get_setting('test_json')
        assert result == test_data
        assert isinstance(result, dict)

    def test_set_boolean_setting_stores_correctly(self):
        """Boolean values should be stored and retrieved correctly."""
        set_setting('test_bool_true', True, 'boolean', 'test', updated_by='Test')
        set_setting('test_bool_false', False, 'boolean', 'test', updated_by='Test')

        assert get_setting('test_bool_true') is True
        assert get_setting('test_bool_false') is False

    def test_update_existing_setting_succeeds(self):
        """Updating an existing setting should work."""
        set_setting('test_update', 'original', 'string', 'test', updated_by='Test')
        set_setting('test_update', 'updated', 'string', 'test', updated_by='Test')
        result = get_setting('test_update')
        assert result == 'updated'


class TestGetSettingsByCategory:
    """Tests for get_settings_by_category() function."""

    def test_get_payroll_category_returns_all_payroll_settings(self):
        """Getting payroll category should return all payroll settings."""
        result = get_settings_by_category('payroll')

        assert 'payroll_yahshua_15th' in result
        assert 'payroll_yahshua_30th' in result
        assert 'payroll_abba_15th' in result
        assert 'payroll_abba_30th' in result

    def test_get_payment_terms_category(self):
        """Getting payment_terms category should return all payment settings."""
        result = get_settings_by_category('payment_terms')

        assert 'invoice_lead_days' in result
        assert 'payment_terms_days' in result
        assert 'realistic_delay_days' in result
        assert 'default_reliability' in result

    def test_get_empty_category_returns_empty_dict(self):
        """Getting non-existent category should return empty dict."""
        result = get_settings_by_category('nonexistent_category_xyz')
        assert result == {}


class TestGetAllSettings:
    """Tests for get_all_settings() function."""

    def test_get_all_settings_returns_grouped_dict(self):
        """get_all_settings should return settings grouped by category."""
        result = get_all_settings()

        assert isinstance(result, dict)
        assert 'payroll' in result
        assert 'payment_terms' in result
        assert 'entity_mapping' in result
        assert 'alerts' in result
        assert 'data_source' in result


# ═══════════════════════════════════════════════════════════════════
# AUDIT LOGGING TESTS
# ═══════════════════════════════════════════════════════════════════

class TestAuditLogging:
    """Tests for settings audit logging."""

    def test_set_setting_creates_audit_log_entry(self):
        """Setting a value should create an audit log entry."""
        # Set a unique setting to ensure we can find it
        unique_key = f'audit_test_{date.today().isoformat()}'
        set_setting(unique_key, 'audit_value', 'string', 'test', updated_by='AuditTestUser')

        # Check audit log
        audit_entries = get_audit_log(key=unique_key, limit=10)

        assert len(audit_entries) >= 1
        latest_entry = audit_entries[0]
        assert latest_entry['setting_key'] == unique_key
        assert latest_entry['new_value'] == 'audit_value'
        assert latest_entry['changed_by'] == 'AuditTestUser'

    def test_update_setting_logs_old_and_new_values(self):
        """Updating a setting should log both old and new values."""
        unique_key = f'audit_update_test_{date.today().isoformat()}'

        # Set initial value
        set_setting(unique_key, 'old_value', 'string', 'test', updated_by='Test')

        # Update value
        set_setting(unique_key, 'new_value', 'string', 'test', updated_by='Test')

        # Check audit log
        audit_entries = get_audit_log(key=unique_key, limit=10)

        # Should have 2 entries (initial set + update)
        assert len(audit_entries) >= 2

        # Most recent entry should show the update
        latest = audit_entries[0]
        assert latest['old_value'] == 'old_value'
        assert latest['new_value'] == 'new_value'

    def test_get_audit_log_respects_limit(self):
        """get_audit_log should respect the limit parameter."""
        audit_entries = get_audit_log(limit=5)
        assert len(audit_entries) <= 5

    def test_get_audit_log_filters_by_key(self):
        """get_audit_log should filter by setting key when provided."""
        unique_key = f'filter_test_{date.today().isoformat()}'
        set_setting(unique_key, 'filter_value', 'string', 'test', updated_by='Test')

        audit_entries = get_audit_log(key=unique_key)

        # All entries should be for our specific key
        for entry in audit_entries:
            assert entry['setting_key'] == unique_key


# ═══════════════════════════════════════════════════════════════════
# RESET TO DEFAULTS TESTS
# ═══════════════════════════════════════════════════════════════════

class TestResetToDefaults:
    """Tests for reset_to_defaults() function."""

    def test_reset_single_category_only_affects_that_category(self):
        """Resetting a category should only affect that category."""
        # Modify a payroll setting
        original = get_setting('payroll_yahshua_15th')
        set_setting('payroll_yahshua_15th', Decimal('9999999'), 'decimal', 'payroll', updated_by='Test')

        # Modify an alerts setting
        set_setting('alert_days_advance', 999, 'integer', 'alerts', updated_by='Test')

        # Reset only payroll
        result = reset_to_defaults(category='payroll', updated_by='ResetTest')
        assert result is True

        # Payroll should be reset
        assert get_setting('payroll_yahshua_15th') == Decimal('1000000')

        # Alerts should NOT be reset
        assert get_setting('alert_days_advance') == 999

    def test_reset_all_resets_all_categories(self):
        """Resetting without category should reset everything."""
        # Modify settings across categories
        set_setting('payroll_yahshua_15th', Decimal('8888888'), 'decimal', 'payroll', updated_by='Test')
        set_setting('invoice_lead_days', 99, 'integer', 'payment_terms', updated_by='Test')

        # Reset all
        result = reset_to_defaults(updated_by='ResetTest')
        assert result is True

        # Both should be reset
        assert get_setting('payroll_yahshua_15th') == Decimal('1000000')
        assert get_setting('invoice_lead_days') == 15


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestPayrollConfig:
    """Tests for get_payroll_config() convenience function."""

    def test_payroll_config_returns_correct_structure(self):
        """get_payroll_config should return nested dict with entity keys."""
        config = get_payroll_config()

        assert 'YAHSHUA' in config
        assert 'ABBA' in config
        assert '15th' in config['YAHSHUA']
        assert '30th' in config['YAHSHUA']
        assert '15th' in config['ABBA']
        assert '30th' in config['ABBA']

    def test_payroll_config_returns_decimal_values(self):
        """Payroll amounts should be Decimal type."""
        config = get_payroll_config()

        assert isinstance(config['YAHSHUA']['15th'], Decimal)
        assert isinstance(config['YAHSHUA']['30th'], Decimal)
        assert isinstance(config['ABBA']['15th'], Decimal)
        assert isinstance(config['ABBA']['30th'], Decimal)

    def test_default_yahshua_payroll_is_2m_monthly(self):
        """Default YAHSHUA payroll should be 2M/month (1M on 15th, 1M on 30th)."""
        # Reset to defaults first
        reset_to_defaults(category='payroll')
        config = get_payroll_config()

        yahshua_total = config['YAHSHUA']['15th'] + config['YAHSHUA']['30th']
        assert yahshua_total == Decimal('2000000')

    def test_default_abba_payroll_is_1m_monthly(self):
        """Default ABBA payroll should be 1M/month (500K on 15th, 500K on 30th)."""
        reset_to_defaults(category='payroll')
        config = get_payroll_config()

        abba_total = config['ABBA']['15th'] + config['ABBA']['30th']
        assert abba_total == Decimal('1000000')


class TestPaymentTermsConfig:
    """Tests for get_payment_terms_config() convenience function."""

    def test_payment_terms_returns_correct_keys(self):
        """get_payment_terms_config should return all expected keys."""
        config = get_payment_terms_config()

        assert 'invoice_lead_days' in config
        assert 'payment_terms_days' in config
        assert 'realistic_delay_days' in config
        assert 'default_reliability' in config

    def test_payment_terms_returns_integer_values(self):
        """Payment terms values should be integers."""
        config = get_payment_terms_config()

        assert isinstance(config['invoice_lead_days'], int)
        assert isinstance(config['payment_terms_days'], int)
        assert isinstance(config['realistic_delay_days'], int)
        assert isinstance(config['default_reliability'], int)

    def test_default_payment_terms(self):
        """Default payment terms should match business rules."""
        reset_to_defaults(category='payment_terms')
        config = get_payment_terms_config()

        assert config['invoice_lead_days'] == 15
        assert config['payment_terms_days'] == 30
        assert config['realistic_delay_days'] == 10
        assert config['default_reliability'] == 80


class TestEntityMapping:
    """Tests for get_entity_mapping() convenience function."""

    def test_entity_mapping_returns_dict(self):
        """get_entity_mapping should return a dictionary."""
        mapping = get_entity_mapping()
        assert isinstance(mapping, dict)

    def test_default_entity_mapping_has_all_sources(self):
        """Default mapping should include all acquisition sources."""
        reset_to_defaults(category='entity_mapping')
        mapping = get_entity_mapping()

        # Check YAHSHUA sources
        assert mapping.get('RCBC Partner') == 'YAHSHUA'
        assert mapping.get('Globe Partner') == 'YAHSHUA'
        assert mapping.get('YOWI') == 'YAHSHUA'

        # Check ABBA sources
        assert mapping.get('TAI') == 'ABBA'
        assert mapping.get('PEI') == 'ABBA'

    def test_entity_mapping_can_be_updated(self):
        """Entity mapping should be editable."""
        # Add a new source
        current_mapping = get_entity_mapping()
        current_mapping['New Partner'] = 'YAHSHUA'

        set_setting('entity_mapping', current_mapping, 'json', 'entity_mapping', updated_by='Test')

        updated_mapping = get_entity_mapping()
        assert updated_mapping.get('New Partner') == 'YAHSHUA'


class TestAlertThresholds:
    """Tests for get_alert_thresholds() convenience function."""

    def test_alert_thresholds_returns_correct_keys(self):
        """get_alert_thresholds should return all expected keys."""
        thresholds = get_alert_thresholds()

        assert 'cash_warning' in thresholds
        assert 'cash_critical' in thresholds
        assert 'days_advance' in thresholds
        assert 'contract_expiry_days' in thresholds

    def test_cash_thresholds_are_decimal(self):
        """Cash thresholds should be Decimal type."""
        thresholds = get_alert_thresholds()

        assert isinstance(thresholds['cash_warning'], Decimal)
        assert isinstance(thresholds['cash_critical'], Decimal)

    def test_default_thresholds(self):
        """Default thresholds should be reasonable."""
        reset_to_defaults(category='alerts')
        thresholds = get_alert_thresholds()

        assert thresholds['cash_warning'] == Decimal('5000000')
        assert thresholds['cash_critical'] == Decimal('2000000')
        assert thresholds['days_advance'] == 30
        assert thresholds['contract_expiry_days'] == 90


class TestGoogleSheetsConfig:
    """Tests for get_google_sheets_config() convenience function."""

    def test_google_sheets_config_returns_correct_keys(self):
        """get_google_sheets_config should return all expected keys."""
        config = get_google_sheets_config()

        assert 'url' in config
        assert 'customers_sheet' in config
        assert 'vendors_sheet' in config
        assert 'bank_balances_sheet' in config

    def test_default_sheet_names(self):
        """Default sheet names should match expected values."""
        reset_to_defaults(category='data_source')
        config = get_google_sheets_config()

        assert config['customers_sheet'] == 'Customer Contracts'
        assert config['vendors_sheet'] == 'Vendor Contracts'
        assert config['bank_balances_sheet'] == 'Bank Balances'


class TestExtractSpreadsheetId:
    """Tests for extract_spreadsheet_id() helper function."""

    def test_extract_id_from_full_url(self):
        """Should extract ID from full Google Sheets URL."""
        url = 'https://docs.google.com/spreadsheets/d/1abc123xyz/edit?gid=0#gid=0'
        result = extract_spreadsheet_id(url)
        assert result == '1abc123xyz'

    def test_extract_id_from_url_without_params(self):
        """Should extract ID from URL without query params."""
        url = 'https://docs.google.com/spreadsheets/d/1abc123xyz/edit'
        result = extract_spreadsheet_id(url)
        assert result == '1abc123xyz'

    def test_extract_id_returns_empty_for_invalid_url(self):
        """Should return empty string for invalid URL."""
        url = 'not a valid url'
        result = extract_spreadsheet_id(url)
        assert result == ''

    def test_extract_id_handles_empty_string(self):
        """Should handle empty string input."""
        result = extract_spreadsheet_id('')
        assert result == ''


# ═══════════════════════════════════════════════════════════════════
# TYPE CONVERSION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestTypeConversion:
    """Tests for type conversion helper functions."""

    def test_convert_string(self):
        """String conversion should return string as-is."""
        result = _convert_value('hello', 'string')
        assert result == 'hello'

    def test_convert_integer(self):
        """Integer conversion should return int."""
        result = _convert_value('42', 'integer')
        assert result == 42
        assert isinstance(result, int)

    def test_convert_decimal(self):
        """Decimal conversion should return Decimal."""
        result = _convert_value('1234.56', 'decimal')
        assert result == Decimal('1234.56')
        assert isinstance(result, Decimal)

    def test_convert_boolean_true(self):
        """Boolean conversion should handle 'true'."""
        assert _convert_value('true', 'boolean') is True
        assert _convert_value('True', 'boolean') is True
        assert _convert_value('1', 'boolean') is True
        assert _convert_value('yes', 'boolean') is True

    def test_convert_boolean_false(self):
        """Boolean conversion should handle 'false'."""
        assert _convert_value('false', 'boolean') is False
        assert _convert_value('0', 'boolean') is False
        assert _convert_value('no', 'boolean') is False

    def test_convert_json(self):
        """JSON conversion should parse JSON string."""
        json_str = '{"key": "value", "number": 42}'
        result = _convert_value(json_str, 'json')
        assert result == {'key': 'value', 'number': 42}

    def test_serialize_dict(self):
        """Serializing dict should return JSON string."""
        data = {'key': 'value'}
        result = _serialize_value(data)
        assert result == json.dumps(data)

    def test_serialize_bool(self):
        """Serializing boolean should return 'true' or 'false'."""
        assert _serialize_value(True) == 'true'
        assert _serialize_value(False) == 'false'

    def test_serialize_decimal(self):
        """Serializing Decimal should return string."""
        result = _serialize_value(Decimal('1234.56'))
        assert result == '1234.56'


# ═══════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_large_decimal_value(self):
        """Should handle large decimal values (₱250M+)."""
        large_amount = Decimal('250000000.00')
        set_setting('test_large', large_amount, 'decimal', 'test', updated_by='Test')
        result = get_setting('test_large')
        assert result == large_amount

    def test_zero_decimal_value(self):
        """Should handle zero decimal values."""
        set_setting('test_zero', Decimal('0'), 'decimal', 'test', updated_by='Test')
        result = get_setting('test_zero')
        assert result == Decimal('0')

    def test_negative_integer(self):
        """Should handle negative integers (for adjustments)."""
        set_setting('test_negative', -10, 'integer', 'test', updated_by='Test')
        result = get_setting('test_negative')
        assert result == -10

    def test_empty_string_value(self):
        """Should handle empty string values."""
        set_setting('test_empty', '', 'string', 'test', updated_by='Test')
        result = get_setting('test_empty')
        assert result == ''

    def test_special_characters_in_value(self):
        """Should handle special characters in string values."""
        special = "Test with 'quotes' and \"double\" and ₱ symbols"
        set_setting('test_special', special, 'string', 'test', updated_by='Test')
        result = get_setting('test_special')
        assert result == special

    def test_unicode_characters(self):
        """Should handle unicode characters."""
        unicode_str = "Company: 株式会社 - ₱100,000"
        set_setting('test_unicode', unicode_str, 'string', 'test', updated_by='Test')
        result = get_setting('test_unicode')
        assert result == unicode_str

    def test_nested_json_structure(self):
        """Should handle nested JSON structures."""
        nested = {
            'level1': {
                'level2': {
                    'value': [1, 2, 3]
                }
            }
        }
        set_setting('test_nested', nested, 'json', 'test', updated_by='Test')
        result = get_setting('test_nested')
        assert result == nested


# ═══════════════════════════════════════════════════════════════════
# DEFAULT SETTINGS VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestDefaultSettings:
    """Tests to validate DEFAULT_SETTINGS structure and values."""

    def test_all_defaults_have_three_tuple_values(self):
        """Each default should be a tuple of (value, type, category)."""
        for key, value in DEFAULT_SETTINGS.items():
            assert isinstance(value, tuple), f"{key} is not a tuple"
            assert len(value) == 3, f"{key} should have 3 elements"

    def test_all_setting_types_are_valid(self):
        """All setting types should be valid types."""
        valid_types = {'string', 'integer', 'decimal', 'boolean', 'json'}
        for key, (value, setting_type, category) in DEFAULT_SETTINGS.items():
            assert setting_type in valid_types, f"{key} has invalid type: {setting_type}"

    def test_all_categories_are_valid(self):
        """All categories should be one of the expected categories."""
        valid_categories = {'payroll', 'payment_terms', 'entity_mapping', 'alerts', 'data_source'}
        for key, (value, setting_type, category) in DEFAULT_SETTINGS.items():
            assert category in valid_categories, f"{key} has invalid category: {category}"

    def test_decimal_defaults_are_valid_decimal_strings(self):
        """Decimal defaults should be valid decimal strings."""
        for key, (value, setting_type, category) in DEFAULT_SETTINGS.items():
            if setting_type == 'decimal':
                try:
                    Decimal(value)
                except:
                    pytest.fail(f"{key} has invalid decimal value: {value}")

    def test_integer_defaults_are_valid_integer_strings(self):
        """Integer defaults should be valid integer strings."""
        for key, (value, setting_type, category) in DEFAULT_SETTINGS.items():
            if setting_type == 'integer':
                try:
                    int(value)
                except:
                    pytest.fail(f"{key} has invalid integer value: {value}")

    def test_json_defaults_are_valid_json_strings(self):
        """JSON defaults should be valid JSON strings."""
        for key, (value, setting_type, category) in DEFAULT_SETTINGS.items():
            if setting_type == 'json':
                try:
                    json.loads(value)
                except:
                    pytest.fail(f"{key} has invalid JSON value: {value}")
