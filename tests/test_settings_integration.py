"""
Tests for Settings Integration with other system components.
Verifies that changing settings in the database properly affects:
- Projection calculations
- Entity mapping
- Revenue calculator
- Expense scheduler

Test Categories:
1. PAYROLL INTEGRATION - Payroll settings affect expense projections
2. ENTITY MAPPING INTEGRATION - Mapping changes affect entity assignments
3. PAYMENT TERMS INTEGRATION - Terms affect revenue timing
4. VIEWER MODE - Access control works correctly
"""
import pytest
from decimal import Decimal
from datetime import date

from database.settings_manager import (
    set_setting,
    get_setting,
    reset_to_defaults,
    init_settings_tables,
    get_payroll_config,
    get_entity_mapping
)
from config.entity_mapping import assign_entity, validate_entity


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Setup tables and reset to defaults after each test."""
    init_settings_tables()
    yield
    # Reset to defaults after each test to avoid test pollution
    reset_to_defaults()


# ═══════════════════════════════════════════════════════════════════
# ENTITY MAPPING INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEntityMappingIntegration:
    """Tests for entity mapping integration with config/entity_mapping.py."""

    def test_default_rcbc_maps_to_yahshua(self):
        """RCBC Partner should map to YAHSHUA by default."""
        result = assign_entity('RCBC Partner')
        assert result == 'YAHSHUA'

    def test_default_tai_maps_to_abba(self):
        """TAI should map to ABBA by default."""
        result = assign_entity('TAI')
        assert result == 'ABBA'

    def test_changing_mapping_affects_assign_entity(self):
        """Changing entity mapping in settings should affect assign_entity()."""
        # Get current mapping
        current_mapping = get_entity_mapping()

        # Change RCBC Partner to ABBA
        current_mapping['RCBC Partner'] = 'ABBA'
        set_setting('entity_mapping', current_mapping, 'json', 'entity_mapping', updated_by='Test')

        # Now RCBC Partner should map to ABBA
        result = assign_entity('RCBC Partner')
        assert result == 'ABBA'

    def test_adding_new_source_works(self):
        """Adding a new acquisition source should work."""
        current_mapping = get_entity_mapping()
        current_mapping['New Partner'] = 'YAHSHUA'
        set_setting('entity_mapping', current_mapping, 'json', 'entity_mapping', updated_by='Test')

        # New source should work now
        result = assign_entity('New Partner')
        assert result == 'YAHSHUA'

    def test_unmapped_source_raises_error(self):
        """Unmapped acquisition source should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            assign_entity('Unknown Partner XYZ')

        assert 'Unmapped acquisition source' in str(exc_info.value)
        assert 'Unknown Partner XYZ' in str(exc_info.value)
        assert 'Settings > Entity Mapping' in str(exc_info.value)

    def test_empty_source_raises_error(self):
        """Empty acquisition source should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            assign_entity('')

        assert 'cannot be empty' in str(exc_info.value)

    def test_whitespace_source_is_trimmed(self):
        """Whitespace in acquisition source should be trimmed."""
        result = assign_entity('  RCBC Partner  ')
        assert result == 'YAHSHUA'

    def test_validate_entity_accepts_valid_entities(self):
        """validate_entity should accept YAHSHUA, ABBA, Consolidated."""
        assert validate_entity('YAHSHUA') is True
        assert validate_entity('ABBA') is True
        assert validate_entity('Consolidated') is True

    def test_validate_entity_rejects_invalid_entities(self):
        """validate_entity should reject invalid entity codes."""
        assert validate_entity('INVALID') is False
        assert validate_entity('') is False
        assert validate_entity('yahshua') is False  # Case sensitive


# ═══════════════════════════════════════════════════════════════════
# PAYROLL SETTINGS INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestPayrollSettingsIntegration:
    """Tests for payroll settings integration."""

    def test_payroll_settings_read_from_database(self):
        """get_payroll_config should read from database."""
        # Set custom payroll values
        set_setting('payroll_yahshua_15th', Decimal('1500000'), 'decimal', 'payroll', updated_by='Test')
        set_setting('payroll_yahshua_30th', Decimal('1500000'), 'decimal', 'payroll', updated_by='Test')

        config = get_payroll_config()

        assert config['YAHSHUA']['15th'] == Decimal('1500000')
        assert config['YAHSHUA']['30th'] == Decimal('1500000')

    def test_modified_payroll_affects_monthly_total(self):
        """Modified payroll should affect monthly totals."""
        # Set ABBA to ₱2M/month
        set_setting('payroll_abba_15th', Decimal('1000000'), 'decimal', 'payroll', updated_by='Test')
        set_setting('payroll_abba_30th', Decimal('1000000'), 'decimal', 'payroll', updated_by='Test')

        config = get_payroll_config()
        abba_monthly = config['ABBA']['15th'] + config['ABBA']['30th']

        assert abba_monthly == Decimal('2000000')

    def test_zero_payroll_is_valid(self):
        """Setting payroll to zero should work (for testing/pausing)."""
        set_setting('payroll_abba_15th', Decimal('0'), 'decimal', 'payroll', updated_by='Test')

        config = get_payroll_config()
        assert config['ABBA']['15th'] == Decimal('0')


# ═══════════════════════════════════════════════════════════════════
# PAYMENT TERMS INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestPaymentTermsIntegration:
    """Tests for payment terms settings integration with revenue calculator."""

    def test_revenue_calculator_uses_database_settings(self):
        """RevenueCalculator should use realistic_delay_days from database."""
        from projection_engine.revenue_calculator import RevenueCalculator

        # Set custom realistic delay
        set_setting('realistic_delay_days', 15, 'integer', 'payment_terms', updated_by='Test')

        # Create calculator (should read from database)
        calc = RevenueCalculator(scenario_type='realistic')

        # Payment uses contract start day + realistic delay
        assert calc.payment_delay_days == 15

    def test_optimistic_scenario_has_zero_delay(self):
        """Optimistic scenario should have zero payment delay."""
        from projection_engine.revenue_calculator import RevenueCalculator

        calc = RevenueCalculator(scenario_type='optimistic')
        assert calc.payment_delay_days == 0

    def test_realistic_scenario_uses_delay_setting(self):
        """Realistic scenario should use delay from settings."""
        from projection_engine.revenue_calculator import RevenueCalculator

        set_setting('realistic_delay_days', 12, 'integer', 'payment_terms', updated_by='Test')

        calc = RevenueCalculator(scenario_type='realistic')
        assert calc.payment_delay_days == 12

    def test_payment_date_uses_contract_start_day(self):
        """Payment date should be based on contract start day."""
        from projection_engine.revenue_calculator import RevenueCalculator

        # Create calculator with realistic scenario (10-day delay by default)
        set_setting('realistic_delay_days', 10, 'integer', 'payment_terms', updated_by='Test')
        calc = RevenueCalculator(scenario_type='realistic')

        # Contract started on March 5, billing for April
        contract_start = date(2026, 3, 5)
        billing_month = date(2026, 4, 1)
        payment_date = calc.calculate_payment_date(billing_month, contract_start)

        # Payment on 5th + 10 day delay = 15th
        assert payment_date == date(2026, 4, 15)

    def test_optimistic_payment_date_no_delay(self):
        """Optimistic scenario should have no delay on payment date."""
        from projection_engine.revenue_calculator import RevenueCalculator

        calc = RevenueCalculator(scenario_type='optimistic')

        # Contract started on March 5, billing for April
        contract_start = date(2026, 3, 5)
        billing_month = date(2026, 4, 1)
        payment_date = calc.calculate_payment_date(billing_month, contract_start)

        # No delay in optimistic = payment on 5th
        assert payment_date == date(2026, 4, 5)


# ═══════════════════════════════════════════════════════════════════
# ALERT THRESHOLDS INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestAlertThresholdsIntegration:
    """Tests for alert threshold settings."""

    def test_alert_thresholds_can_be_updated(self):
        """Alert thresholds should be editable."""
        from database.settings_manager import get_alert_thresholds

        # Set custom thresholds
        set_setting('alert_cash_warning', Decimal('10000000'), 'decimal', 'alerts', updated_by='Test')
        set_setting('alert_cash_critical', Decimal('5000000'), 'decimal', 'alerts', updated_by='Test')

        thresholds = get_alert_thresholds()

        assert thresholds['cash_warning'] == Decimal('10000000')
        assert thresholds['cash_critical'] == Decimal('5000000')

    def test_warning_should_be_higher_than_critical(self):
        """Business rule: warning threshold should be > critical threshold."""
        from database.settings_manager import get_alert_thresholds

        thresholds = get_alert_thresholds()

        assert thresholds['cash_warning'] > thresholds['cash_critical']


# ═══════════════════════════════════════════════════════════════════
# DATA SOURCE INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestDataSourceIntegration:
    """Tests for Google Sheets data source settings."""

    def test_google_sheets_url_can_be_changed(self):
        """Google Sheets URL should be editable."""
        from database.settings_manager import get_google_sheets_config

        new_url = 'https://docs.google.com/spreadsheets/d/NEW_SHEET_ID/edit'
        set_setting('google_sheets_url', new_url, 'string', 'data_source', updated_by='Test')

        config = get_google_sheets_config()
        assert config['url'] == new_url

    def test_sheet_names_can_be_changed(self):
        """Sheet tab names should be editable."""
        from database.settings_manager import get_google_sheets_config

        set_setting('sheet_name_customers', 'My Customers Tab', 'string', 'data_source', updated_by='Test')

        config = get_google_sheets_config()
        assert config['customers_sheet'] == 'My Customers Tab'


# ═══════════════════════════════════════════════════════════════════
# VIEWER MODE / ACCESS CONTROL TESTS
# ═══════════════════════════════════════════════════════════════════

class TestViewerModeAccessControl:
    """Tests for viewer mode access control (simulated without Streamlit)."""

    def test_check_admin_access_default_is_admin(self):
        """Without auth system, default should be admin."""
        # We can't easily test Streamlit session state without Streamlit running
        # This test documents expected behavior
        # When st.session_state has no 'user_role', check_admin_access() returns True (admin)
        pass  # Streamlit-specific, would need integration test

    def test_viewer_cannot_edit_is_business_rule(self):
        """Viewer mode should disable edits - documented requirement."""
        # Business rule: When st.session_state.user_role == 'viewer',
        # all input fields should have disabled=True
        # This is enforced in the UI layer (7_Settings.py)
        pass  # UI-specific, would need Streamlit integration test

    def test_admin_can_edit_is_business_rule(self):
        """Admin mode should enable edits - documented requirement."""
        # Business rule: When st.session_state.user_role == 'admin',
        # all input fields should have disabled=False
        # and Save buttons should be visible
        pass  # UI-specific, would need Streamlit integration test


# ═══════════════════════════════════════════════════════════════════
# SETTINGS PERSISTENCE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestSettingsPersistence:
    """Tests for settings persistence across sessions."""

    def test_settings_persist_across_function_calls(self):
        """Settings should persist across multiple function calls."""
        # Set a value
        set_setting('persist_test', 'value1', 'string', 'test', updated_by='Test')

        # Read it multiple times
        for _ in range(3):
            result = get_setting('persist_test')
            assert result == 'value1'

    def test_updated_settings_reflect_immediately(self):
        """Updated settings should be available immediately."""
        set_setting('immediate_test', 'old', 'string', 'test', updated_by='Test')
        assert get_setting('immediate_test') == 'old'

        set_setting('immediate_test', 'new', 'string', 'test', updated_by='Test')
        assert get_setting('immediate_test') == 'new'

    def test_multiple_categories_dont_interfere(self):
        """Settings in different categories should be independent."""
        # Set payroll
        set_setting('payroll_yahshua_15th', Decimal('9999999'), 'decimal', 'payroll', updated_by='Test')

        # Set alerts - shouldn't affect payroll
        set_setting('alert_cash_warning', Decimal('1'), 'decimal', 'alerts', updated_by='Test')

        # Payroll should still be 9999999
        assert get_setting('payroll_yahshua_15th') == Decimal('9999999')


# ═══════════════════════════════════════════════════════════════════
# FALLBACK BEHAVIOR TESTS
# ═══════════════════════════════════════════════════════════════════

class TestFallbackBehavior:
    """Tests for fallback to defaults when database has no value."""

    def test_new_key_returns_default_setting(self):
        """New installation should return DEFAULT_SETTINGS values."""
        # After reset, should return defaults
        reset_to_defaults(category='payroll')

        assert get_setting('payroll_yahshua_15th') == Decimal('1000000')
        assert get_setting('invoice_lead_days') == 15

    def test_missing_setting_uses_provided_default(self):
        """Non-existent setting should use provided default argument."""
        result = get_setting('completely_nonexistent_key_xyz', default='my_fallback')
        assert result == 'my_fallback'

    def test_fallback_to_default_settings_dict(self):
        """If not in DB and no default provided, use DEFAULT_SETTINGS."""
        from database.settings_manager import DEFAULT_SETTINGS

        # Check all defaults work
        for key, (value, setting_type, category) in DEFAULT_SETTINGS.items():
            result = get_setting(key)
            assert result is not None, f"{key} returned None"
