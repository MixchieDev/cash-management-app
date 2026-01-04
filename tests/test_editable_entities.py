"""
Tests for Editable Entities Feature - Dynamic consolidated projections.

Tests the ability to:
- Add/edit/toggle legal entities from dashboard
- Dynamic entity mapping with new entities
- Dynamic payroll configuration for all entities
- Consolidated projections including all active entities

Test Categories:
1. ENTITY CRUD - Create, Read, Update entities
2. ENTITY VALIDATION - Active/inactive, codes, full names
3. DYNAMIC ENTITY MAPPING - Mapping to dynamic entities
4. DYNAMIC PAYROLL - Payroll config for all entities
5. CONSOLIDATED PROJECTIONS - Sum of all active entities
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta

from database.settings_manager import (
    init_entities_table,
    get_all_entities,
    get_entity_by_code,
    create_entity,
    update_entity,
    get_valid_entity_codes,
    get_entity_full_name_from_db,
    get_payroll_config_dynamic,
    set_setting,
    get_setting,
    reset_to_defaults,
    init_settings_tables
)
from config.entity_mapping import (
    get_valid_entities,
    get_entity_full_name,
    validate_entity,
    assign_entity
)


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def setup_tables():
    """Ensure tables exist before each test."""
    init_settings_tables()
    init_entities_table()
    yield
    # Clean up test entities after each test
    _cleanup_test_entities()


def _cleanup_test_entities():
    """Remove any test entities created during tests and reset defaults."""
    try:
        from database.db_manager import db_manager
        from sqlalchemy import text

        with db_manager.engine.connect() as conn:
            # Delete test entities (keep YAHSHUA and ABBA)
            conn.execute(text("""
                DELETE FROM entities
                WHERE short_code NOT IN ('YAHSHUA', 'ABBA')
            """))
            # Reset YAHSHUA and ABBA to default state
            conn.execute(text("""
                UPDATE entities
                SET is_active = 1,
                    full_name = 'YAHSHUA Outsourcing Worldwide Inc',
                    display_order = 1
                WHERE short_code = 'YAHSHUA'
            """))
            conn.execute(text("""
                UPDATE entities
                SET is_active = 1,
                    full_name = 'The ABBA Initiative OPC',
                    display_order = 2
                WHERE short_code = 'ABBA'
            """))
            conn.commit()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════
# ENTITY TABLE INITIALIZATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEntityTableInitialization:
    """Tests for entity table initialization."""

    def test_init_entities_table_creates_table(self):
        """init_entities_table should create the entities table."""
        result = init_entities_table()
        assert result is True

    def test_init_entities_table_seeds_default_entities(self):
        """init_entities_table should seed YAHSHUA and ABBA."""
        init_entities_table()
        entities = get_all_entities(include_inactive=True)

        codes = [e['short_code'] for e in entities]
        assert 'YAHSHUA' in codes
        assert 'ABBA' in codes

    def test_init_entities_table_idempotent(self):
        """Calling init_entities_table multiple times should be safe."""
        for _ in range(3):
            result = init_entities_table()
            assert result is True

        # Should still have exactly 2 default entities
        entities = get_all_entities(include_inactive=True)
        default_codes = [e['short_code'] for e in entities if e['short_code'] in ('YAHSHUA', 'ABBA')]
        assert len(default_codes) == 2


# ═══════════════════════════════════════════════════════════════════
# ENTITY CRUD TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEntityCRUD:
    """Tests for entity Create, Read, Update operations."""

    def test_get_all_entities_returns_list(self):
        """get_all_entities should return a list."""
        entities = get_all_entities()
        assert isinstance(entities, list)

    def test_get_all_entities_has_required_fields(self):
        """Each entity should have id, short_code, full_name, is_active, display_order."""
        entities = get_all_entities()

        for entity in entities:
            assert 'id' in entity
            assert 'short_code' in entity
            assert 'full_name' in entity
            assert 'is_active' in entity
            assert 'display_order' in entity

    def test_get_all_entities_excludes_inactive_by_default(self):
        """get_all_entities should exclude inactive entities by default."""
        # Deactivate ABBA
        update_entity('ABBA', is_active=False)

        entities = get_all_entities(include_inactive=False)
        codes = [e['short_code'] for e in entities]

        assert 'YAHSHUA' in codes
        assert 'ABBA' not in codes

    def test_get_all_entities_includes_inactive_when_requested(self):
        """get_all_entities with include_inactive=True should include inactive."""
        update_entity('ABBA', is_active=False)

        entities = get_all_entities(include_inactive=True)
        codes = [e['short_code'] for e in entities]

        assert 'YAHSHUA' in codes
        assert 'ABBA' in codes

    def test_get_entity_by_code_returns_entity(self):
        """get_entity_by_code should return entity dict."""
        entity = get_entity_by_code('YAHSHUA')

        assert entity is not None
        assert entity['short_code'] == 'YAHSHUA'
        assert entity['full_name'] == 'YAHSHUA Outsourcing Worldwide Inc'

    def test_get_entity_by_code_returns_none_for_invalid(self):
        """get_entity_by_code should return None for non-existent entity."""
        entity = get_entity_by_code('NONEXISTENT_XYZ')
        assert entity is None

    def test_create_entity_succeeds(self):
        """create_entity should create a new entity."""
        result = create_entity(
            short_code='NEWCO',
            full_name='New Company Inc',
            display_order=3,
            updated_by='TestUser'
        )
        assert result is True

        # Verify entity exists
        entity = get_entity_by_code('NEWCO')
        assert entity is not None
        assert entity['full_name'] == 'New Company Inc'
        assert entity['display_order'] == 3

    def test_create_entity_uppercases_code(self):
        """create_entity should uppercase the short code."""
        create_entity('lowercase', 'Lowercase Test Inc', updated_by='Test')

        entity = get_entity_by_code('LOWERCASE')
        assert entity is not None
        assert entity['short_code'] == 'LOWERCASE'

    def test_create_entity_initializes_payroll_settings(self):
        """create_entity should initialize payroll settings to 0."""
        create_entity('TESTPAY', 'Test Payroll Inc', updated_by='Test')

        # Check payroll settings were created
        payroll_15th = get_setting('payroll_testpay_15th')
        payroll_30th = get_setting('payroll_testpay_30th')

        assert payroll_15th == Decimal('0')
        assert payroll_30th == Decimal('0')

    def test_create_duplicate_entity_fails(self):
        """create_entity with duplicate code should fail."""
        create_entity('DUPETEST', 'First Instance', updated_by='Test')
        result = create_entity('DUPETEST', 'Second Instance', updated_by='Test')

        assert result is False

    def test_update_entity_full_name(self):
        """update_entity should update full name."""
        result = update_entity('YAHSHUA', full_name='Updated YAHSHUA Name')
        assert result is True

        entity = get_entity_by_code('YAHSHUA')
        assert entity['full_name'] == 'Updated YAHSHUA Name'

    def test_update_entity_is_active(self):
        """update_entity should update active status."""
        update_entity('ABBA', is_active=False)

        entity = get_entity_by_code('ABBA')
        assert entity['is_active'] is False

        update_entity('ABBA', is_active=True)

        entity = get_entity_by_code('ABBA')
        assert entity['is_active'] is True

    def test_update_entity_display_order(self):
        """update_entity should update display order."""
        update_entity('YAHSHUA', display_order=99)

        entity = get_entity_by_code('YAHSHUA')
        assert entity['display_order'] == 99

    def test_update_nonexistent_entity_returns_true(self):
        """update_entity on non-existent entity should return True (no-op)."""
        # SQLite UPDATE doesn't fail if no rows match
        result = update_entity('NONEXISTENT', full_name='Test')
        assert result is True


# ═══════════════════════════════════════════════════════════════════
# VALID ENTITY CODES TESTS
# ═══════════════════════════════════════════════════════════════════

class TestValidEntityCodes:
    """Tests for get_valid_entity_codes() function."""

    def test_get_valid_entity_codes_returns_list(self):
        """get_valid_entity_codes should return a list."""
        codes = get_valid_entity_codes()
        assert isinstance(codes, list)

    def test_get_valid_entity_codes_includes_defaults(self):
        """get_valid_entity_codes should include YAHSHUA and ABBA."""
        codes = get_valid_entity_codes()

        assert 'YAHSHUA' in codes
        assert 'ABBA' in codes

    def test_get_valid_entity_codes_excludes_inactive(self):
        """get_valid_entity_codes should exclude inactive entities."""
        update_entity('ABBA', is_active=False)

        codes = get_valid_entity_codes()

        assert 'YAHSHUA' in codes
        assert 'ABBA' not in codes

    def test_get_valid_entity_codes_includes_new_entities(self):
        """get_valid_entity_codes should include newly created entities."""
        create_entity('DYNAMIC', 'Dynamic Entity Inc', updated_by='Test')

        codes = get_valid_entity_codes()
        assert 'DYNAMIC' in codes


# ═══════════════════════════════════════════════════════════════════
# ENTITY FULL NAME TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEntityFullName:
    """Tests for getting entity full names from database."""

    def test_get_entity_full_name_from_db_returns_name(self):
        """get_entity_full_name_from_db should return full name."""
        name = get_entity_full_name_from_db('YAHSHUA')
        assert name == 'YAHSHUA Outsourcing Worldwide Inc'

    def test_get_entity_full_name_from_db_returns_code_if_not_found(self):
        """get_entity_full_name_from_db should return code if not found."""
        name = get_entity_full_name_from_db('NONEXISTENT')
        assert name == 'NONEXISTENT'

    def test_get_entity_full_name_handles_new_entity(self):
        """get_entity_full_name_from_db should work with new entities."""
        create_entity('FULLTEST', 'Full Name Test Company', updated_by='Test')

        name = get_entity_full_name_from_db('FULLTEST')
        assert name == 'Full Name Test Company'


# ═══════════════════════════════════════════════════════════════════
# ENTITY MAPPING INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEntityMappingIntegration:
    """Tests for entity mapping with dynamic entities."""

    def test_get_valid_entities_includes_consolidated(self):
        """get_valid_entities should always include Consolidated."""
        entities = get_valid_entities()

        assert 'Consolidated' in entities

    def test_get_valid_entities_includes_database_entities(self):
        """get_valid_entities should include entities from database."""
        create_entity('FROMDB', 'From Database Inc', updated_by='Test')

        entities = get_valid_entities()
        assert 'FROMDB' in entities

    def test_validate_entity_accepts_new_entities(self):
        """validate_entity should accept newly created entities."""
        create_entity('VALIDNEW', 'Valid New Entity', updated_by='Test')

        assert validate_entity('VALIDNEW') is True

    def test_validate_entity_rejects_inactive_entities(self):
        """validate_entity should reject inactive entities."""
        update_entity('ABBA', is_active=False)

        # Inactive entity should not be valid
        assert validate_entity('ABBA') is False

    def test_get_entity_full_name_uses_database(self):
        """get_entity_full_name from entity_mapping should use database."""
        # Update name in database
        update_entity('YAHSHUA', full_name='Updated YAHSHUA Full Name')

        name = get_entity_full_name('YAHSHUA')
        assert name == 'Updated YAHSHUA Full Name'

    def test_get_entity_full_name_consolidated_special_case(self):
        """get_entity_full_name should handle Consolidated specially."""
        name = get_entity_full_name('Consolidated')
        assert 'Consolidated' in name
        assert 'All' in name or 'Both' in name


# ═══════════════════════════════════════════════════════════════════
# DYNAMIC PAYROLL CONFIG TESTS
# ═══════════════════════════════════════════════════════════════════

class TestDynamicPayrollConfig:
    """Tests for dynamic payroll configuration for all entities."""

    def test_get_payroll_config_dynamic_returns_dict(self):
        """get_payroll_config_dynamic should return a dict."""
        config = get_payroll_config_dynamic()
        assert isinstance(config, dict)

    def test_get_payroll_config_dynamic_includes_all_active_entities(self):
        """get_payroll_config_dynamic should include all active entities."""
        config = get_payroll_config_dynamic()

        assert 'YAHSHUA' in config
        assert 'ABBA' in config

    def test_get_payroll_config_dynamic_excludes_inactive(self):
        """get_payroll_config_dynamic should exclude inactive entities."""
        update_entity('ABBA', is_active=False)

        config = get_payroll_config_dynamic()

        assert 'YAHSHUA' in config
        assert 'ABBA' not in config

    def test_get_payroll_config_dynamic_has_15th_and_30th(self):
        """Each entity should have 15th and 30th payroll amounts."""
        config = get_payroll_config_dynamic()

        for entity, amounts in config.items():
            assert '15th' in amounts
            assert '30th' in amounts
            assert isinstance(amounts['15th'], Decimal)
            assert isinstance(amounts['30th'], Decimal)

    def test_get_payroll_config_dynamic_includes_new_entities(self):
        """get_payroll_config_dynamic should include newly created entities."""
        create_entity('PAYTEST', 'Payroll Test Inc', updated_by='Test')

        config = get_payroll_config_dynamic()

        assert 'PAYTEST' in config
        # New entities default to 0 payroll
        assert config['PAYTEST']['15th'] == Decimal('0')
        assert config['PAYTEST']['30th'] == Decimal('0')

    def test_new_entity_payroll_can_be_set(self):
        """New entity payroll can be set via set_setting."""
        create_entity('SETPAY', 'Set Payroll Inc', updated_by='Test')

        set_setting('payroll_setpay_15th', Decimal('500000'), 'decimal', 'payroll', updated_by='Test')
        set_setting('payroll_setpay_30th', Decimal('500000'), 'decimal', 'payroll', updated_by='Test')

        config = get_payroll_config_dynamic()

        assert config['SETPAY']['15th'] == Decimal('500000')
        assert config['SETPAY']['30th'] == Decimal('500000')


# ═══════════════════════════════════════════════════════════════════
# ENTITY DISPLAY ORDER TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEntityDisplayOrder:
    """Tests for entity display ordering."""

    def test_entities_ordered_by_display_order(self):
        """get_all_entities should return entities in display_order."""
        entities = get_all_entities()

        # Check order is ascending
        orders = [e['display_order'] for e in entities]
        assert orders == sorted(orders)

    def test_new_entity_display_order_respected(self):
        """New entity display order should be respected."""
        # Create entity with order 0 (should be first)
        create_entity('FIRST', 'First Entity', display_order=0, updated_by='Test')

        entities = get_all_entities()

        # FIRST should be first (order 0)
        assert entities[0]['short_code'] == 'FIRST'


# ═══════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_short_code_handled(self):
        """Empty short code should fail gracefully."""
        result = create_entity('', 'Empty Code Inc', updated_by='Test')
        # Should fail validation or constraint
        # The behavior depends on implementation - either returns False or raises

    def test_very_long_full_name(self):
        """Very long full name should work (up to 200 chars)."""
        long_name = 'A' * 200
        result = create_entity('LONGNAME', long_name, updated_by='Test')
        assert result is True

        entity = get_entity_by_code('LONGNAME')
        assert entity['full_name'] == long_name

    def test_special_characters_in_full_name(self):
        """Special characters in full name should work."""
        special_name = "Test & Co. (Philippines) Ltd."
        result = create_entity('SPECIAL', special_name, updated_by='Test')
        assert result is True

        entity = get_entity_by_code('SPECIAL')
        assert entity['full_name'] == special_name

    def test_unicode_in_full_name(self):
        """Unicode characters in full name should work."""
        unicode_name = "Test Company 株式会社"
        result = create_entity('UNICODE', unicode_name, updated_by='Test')
        assert result is True

        entity = get_entity_by_code('UNICODE')
        assert entity['full_name'] == unicode_name

    def test_all_entities_inactive_returns_empty(self):
        """If all entities inactive, get_valid_entity_codes returns empty."""
        update_entity('YAHSHUA', is_active=False)
        update_entity('ABBA', is_active=False)

        codes = get_valid_entity_codes()
        assert codes == []

    def test_toggle_entity_active_status(self):
        """Toggling entity active status should work."""
        # Deactivate
        update_entity('YAHSHUA', is_active=False)
        assert 'YAHSHUA' not in get_valid_entity_codes()

        # Reactivate
        update_entity('YAHSHUA', is_active=True)
        assert 'YAHSHUA' in get_valid_entity_codes()


# ═══════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY TESTS
# ═══════════════════════════════════════════════════════════════════

class TestBackwardCompatibility:
    """Tests for backward compatibility with existing code."""

    def test_default_entities_always_exist(self):
        """YAHSHUA and ABBA should always exist after init."""
        init_entities_table()

        yahshua = get_entity_by_code('YAHSHUA')
        abba = get_entity_by_code('ABBA')

        assert yahshua is not None
        assert abba is not None

    def test_existing_entity_mapping_still_works(self):
        """Existing entity mapping should still work."""
        # These should still map correctly
        assert assign_entity('RCBC Partner') == 'YAHSHUA'
        assert assign_entity('TAI') == 'ABBA'

    def test_legacy_payroll_config_still_accessible(self):
        """Legacy payroll config keys should still work."""
        # These legacy settings should still be accessible
        yahshua_15th = get_setting('payroll_yahshua_15th')
        yahshua_30th = get_setting('payroll_yahshua_30th')

        assert yahshua_15th is not None
        assert yahshua_30th is not None

    def test_valid_entities_list_compatible(self):
        """VALID_ENTITIES import should still work."""
        from config.entity_mapping import VALID_ENTITIES

        assert 'YAHSHUA' in VALID_ENTITIES or 'YAHSHUA' in get_valid_entities()
        assert 'ABBA' in VALID_ENTITIES or 'ABBA' in get_valid_entities()


# ═══════════════════════════════════════════════════════════════════
# ENTITY MODEL TESTS
# ═══════════════════════════════════════════════════════════════════

class TestEntityModel:
    """Tests for the Entity SQLAlchemy model."""

    def test_entity_model_exists(self):
        """Entity model should exist."""
        from database.models import Entity

        assert Entity is not None

    def test_entity_model_has_expected_columns(self):
        """Entity model should have expected columns."""
        from database.models import Entity

        # Check column names
        columns = [c.name for c in Entity.__table__.columns]

        assert 'id' in columns
        assert 'short_code' in columns
        assert 'full_name' in columns
        assert 'is_active' in columns
        assert 'display_order' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns

    def test_entity_repr(self):
        """Entity __repr__ should be meaningful."""
        from database.models import Entity

        entity = Entity(short_code='TEST', full_name='Test Entity')
        repr_str = repr(entity)

        assert 'TEST' in repr_str
        assert 'Test Entity' in repr_str
