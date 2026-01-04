"""
Settings manager for JESUS Company Cash Management System.
Provides functions to get and set application settings from database.
Falls back to config file defaults if setting not in database.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
import json

from sqlalchemy import text

from database.db_manager import db_manager


# ═══════════════════════════════════════════════════════════════════
# DEFAULT SETTINGS (Used when database has no value)
# ═══════════════════════════════════════════════════════════════════
DEFAULT_SETTINGS = {
    # Payroll Configuration
    'payroll_yahshua_15th': ('1000000', 'decimal', 'payroll'),
    'payroll_yahshua_30th': ('1000000', 'decimal', 'payroll'),
    'payroll_abba_15th': ('500000', 'decimal', 'payroll'),
    'payroll_abba_30th': ('500000', 'decimal', 'payroll'),

    # Payment Terms Configuration
    'invoice_lead_days': ('15', 'integer', 'payment_terms'),
    'payment_terms_days': ('30', 'integer', 'payment_terms'),
    'realistic_delay_days': ('10', 'integer', 'payment_terms'),
    'default_reliability': ('80', 'integer', 'payment_terms'),

    # Entity Mapping
    'entity_mapping': (
        '{"RCBC Partner": "YAHSHUA", "Globe Partner": "YAHSHUA", "YOWI": "YAHSHUA", "TAI": "ABBA", "PEI": "ABBA"}',
        'json',
        'entity_mapping'
    ),

    # Alert Thresholds
    'alert_cash_warning': ('5000000', 'decimal', 'alerts'),
    'alert_cash_critical': ('2000000', 'decimal', 'alerts'),
    'alert_days_advance': ('30', 'integer', 'alerts'),
    'alert_contract_expiry_days': ('90', 'integer', 'alerts'),

    # Google Sheets Configuration
    'google_sheets_url': (
        'https://docs.google.com/spreadsheets/d/1p8p7E6j-EhoYOfCWBCWwYMAzgaALDg9RBADDquVnwTM/edit?gid=0#gid=0',
        'string',
        'data_source'
    ),
    'sheet_name_customers': ('Customer Contracts', 'string', 'data_source'),
    'sheet_name_vendors': ('Vendor Contracts', 'string', 'data_source'),
    'sheet_name_bank_balances': ('Bank Balances', 'string', 'data_source'),
}


def _convert_value(value: str, setting_type: str) -> Any:
    """
    Convert string value to appropriate Python type.

    Args:
        value: String value from database
        setting_type: Type of setting ('string', 'integer', 'decimal', 'boolean', 'json')

    Returns:
        Converted value in appropriate type
    """
    if setting_type == 'string':
        return value
    elif setting_type == 'integer':
        return int(value)
    elif setting_type == 'decimal':
        return Decimal(value)
    elif setting_type == 'boolean':
        return value.lower() in ('true', '1', 'yes')
    elif setting_type == 'json':
        return json.loads(value)
    else:
        return value


def _serialize_value(value: Any) -> str:
    """
    Serialize Python value to string for database storage.

    Args:
        value: Python value to serialize

    Returns:
        String representation for database
    """
    if isinstance(value, dict) or isinstance(value, list):
        return json.dumps(value)
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    elif isinstance(value, Decimal):
        return str(value)
    else:
        return str(value)


def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a single setting value from database.
    Falls back to DEFAULT_SETTINGS if not in database.

    Args:
        key: Setting key name
        default: Default value if not found anywhere

    Returns:
        Setting value in appropriate type

    Example:
        >>> get_setting('payroll_yahshua_15th')
        Decimal('1000000')
        >>> get_setting('invoice_lead_days')
        15
    """
    try:
        with db_manager.engine.connect() as conn:
            result = conn.execute(
                text("SELECT setting_value, setting_type FROM app_settings WHERE setting_key = :key"),
                {'key': key}
            ).fetchone()

            if result:
                return _convert_value(result[0], result[1])
    except Exception:
        # Table might not exist yet
        pass

    # Fall back to default settings
    if key in DEFAULT_SETTINGS:
        value, setting_type, _ = DEFAULT_SETTINGS[key]
        return _convert_value(value, setting_type)

    return default


def set_setting(
    key: str,
    value: Any,
    setting_type: str,
    category: str,
    description: Optional[str] = None,
    updated_by: Optional[str] = None
) -> bool:
    """
    Save a setting to the database with audit logging.

    Args:
        key: Setting key name
        value: Setting value (any Python type)
        setting_type: Type ('string', 'integer', 'decimal', 'boolean', 'json')
        category: Category name for grouping
        description: Optional description
        updated_by: Username who made the change

    Returns:
        True if successful, False otherwise

    Example:
        >>> set_setting('payroll_yahshua_15th', Decimal('1200000'), 'decimal', 'payroll', updated_by='CFO')
        True
    """
    serialized_value = _serialize_value(value)

    try:
        with db_manager.engine.connect() as conn:
            # Get old value for audit log
            old_result = conn.execute(
                text("SELECT setting_value FROM app_settings WHERE setting_key = :key"),
                {'key': key}
            ).fetchone()
            old_value = old_result[0] if old_result else None

            # Insert or update setting
            conn.execute(
                text("""
                    INSERT INTO app_settings (setting_key, setting_value, setting_type, category, description, updated_by, updated_at)
                    VALUES (:key, :value, :type, :category, :description, :updated_by, :updated_at)
                    ON CONFLICT(setting_key) DO UPDATE SET
                        setting_value = :value,
                        setting_type = :type,
                        category = :category,
                        description = COALESCE(:description, app_settings.description),
                        updated_by = :updated_by,
                        updated_at = :updated_at
                """),
                {
                    'key': key,
                    'value': serialized_value,
                    'type': setting_type,
                    'category': category,
                    'description': description,
                    'updated_by': updated_by,
                    'updated_at': datetime.utcnow().isoformat()
                }
            )

            # Log the change
            conn.execute(
                text("""
                    INSERT INTO settings_audit_log (setting_key, old_value, new_value, changed_by, changed_at)
                    VALUES (:key, :old_value, :new_value, :changed_by, :changed_at)
                """),
                {
                    'key': key,
                    'old_value': old_value,
                    'new_value': serialized_value,
                    'changed_by': updated_by,
                    'changed_at': datetime.utcnow().isoformat()
                }
            )

            conn.commit()
            return True
    except Exception as e:
        print(f"Error setting {key}: {e}")
        return False


def get_settings_by_category(category: str) -> Dict[str, Any]:
    """
    Get all settings in a category.

    Args:
        category: Category name ('payroll', 'payment_terms', 'entity_mapping', 'alerts', 'data_source')

    Returns:
        Dictionary of setting key -> value

    Example:
        >>> get_settings_by_category('payroll')
        {'payroll_yahshua_15th': Decimal('1000000'), 'payroll_yahshua_30th': Decimal('1000000'), ...}
    """
    settings = {}

    try:
        with db_manager.engine.connect() as conn:
            results = conn.execute(
                text("SELECT setting_key, setting_value, setting_type FROM app_settings WHERE category = :category"),
                {'category': category}
            ).fetchall()

            for row in results:
                settings[row[0]] = _convert_value(row[1], row[2])
    except Exception:
        pass

    # Fill in defaults for missing settings
    for key, (value, setting_type, cat) in DEFAULT_SETTINGS.items():
        if cat == category and key not in settings:
            settings[key] = _convert_value(value, setting_type)

    return settings


def get_all_settings() -> Dict[str, Any]:
    """
    Get all settings from database.

    Returns:
        Dictionary of all settings grouped by category

    Example:
        >>> get_all_settings()
        {
            'payroll': {'payroll_yahshua_15th': Decimal('1000000'), ...},
            'payment_terms': {'invoice_lead_days': 15, ...},
            ...
        }
    """
    all_settings = {}

    try:
        with db_manager.engine.connect() as conn:
            results = conn.execute(
                text("SELECT setting_key, setting_value, setting_type, category FROM app_settings")
            ).fetchall()

            for row in results:
                key, value, setting_type, category = row
                if category not in all_settings:
                    all_settings[category] = {}
                all_settings[category][key] = _convert_value(value, setting_type)
    except Exception:
        pass

    # Fill in defaults for missing categories
    for key, (value, setting_type, category) in DEFAULT_SETTINGS.items():
        if category not in all_settings:
            all_settings[category] = {}
        if key not in all_settings[category]:
            all_settings[category][key] = _convert_value(value, setting_type)

    return all_settings


def reset_to_defaults(category: Optional[str] = None, updated_by: Optional[str] = None) -> bool:
    """
    Reset settings to default values.

    Args:
        category: Category to reset (None = reset all)
        updated_by: Username who made the reset

    Returns:
        True if successful, False otherwise

    Example:
        >>> reset_to_defaults('payroll', updated_by='CFO')
        True
        >>> reset_to_defaults()  # Reset all settings
        True
    """
    try:
        for key, (value, setting_type, cat) in DEFAULT_SETTINGS.items():
            if category is None or cat == category:
                set_setting(key, _convert_value(value, setting_type), setting_type, cat, updated_by=updated_by)
        return True
    except Exception as e:
        print(f"Error resetting settings: {e}")
        return False


def get_audit_log(
    key: Optional[str] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Get settings audit log.

    Args:
        key: Filter by setting key (optional)
        limit: Maximum number of records to return

    Returns:
        List of audit log entries

    Example:
        >>> get_audit_log('payroll_yahshua_15th', limit=10)
        [{'setting_key': 'payroll_yahshua_15th', 'old_value': '1000000', 'new_value': '1200000', ...}]
    """
    audit_entries = []

    try:
        with db_manager.engine.connect() as conn:
            if key:
                results = conn.execute(
                    text("""
                        SELECT setting_key, old_value, new_value, changed_by, changed_at
                        FROM settings_audit_log
                        WHERE setting_key = :key
                        ORDER BY changed_at DESC
                        LIMIT :limit
                    """),
                    {'key': key, 'limit': limit}
                ).fetchall()
            else:
                results = conn.execute(
                    text("""
                        SELECT setting_key, old_value, new_value, changed_by, changed_at
                        FROM settings_audit_log
                        ORDER BY changed_at DESC
                        LIMIT :limit
                    """),
                    {'limit': limit}
                ).fetchall()

            for row in results:
                audit_entries.append({
                    'setting_key': row[0],
                    'old_value': row[1],
                    'new_value': row[2],
                    'changed_by': row[3],
                    'changed_at': row[4]
                })
    except Exception:
        pass

    return audit_entries


def init_settings_tables() -> bool:
    """
    Initialize settings tables if they don't exist.

    Returns:
        True if successful, False otherwise
    """
    try:
        with db_manager.engine.connect() as conn:
            # Create app_settings table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    setting_type VARCHAR(20) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(100)
                )
            """))

            # Create settings_audit_log table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS settings_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key VARCHAR(100) NOT NULL,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    changed_by VARCHAR(100),
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_settings_key ON app_settings(setting_key)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_settings_category ON app_settings(category)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_key ON settings_audit_log(setting_key)"))

            conn.commit()

            # Initialize default values
            for key, (value, setting_type, category) in DEFAULT_SETTINGS.items():
                result = conn.execute(
                    text("SELECT 1 FROM app_settings WHERE setting_key = :key"),
                    {'key': key}
                ).fetchone()

                if not result:
                    conn.execute(
                        text("""
                            INSERT INTO app_settings (setting_key, setting_value, setting_type, category)
                            VALUES (:key, :value, :type, :category)
                        """),
                        {'key': key, 'value': value, 'type': setting_type, 'category': category}
                    )

            conn.commit()
            return True
    except Exception as e:
        print(f"Error initializing settings tables: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS FOR SPECIFIC SETTINGS
# ═══════════════════════════════════════════════════════════════════

def get_payroll_config() -> Dict[str, Dict[str, Decimal]]:
    """
    Get payroll configuration for both entities.

    Returns:
        Dictionary with entity payroll amounts

    Example:
        >>> get_payroll_config()
        {
            'YAHSHUA': {'15th': Decimal('1000000'), '30th': Decimal('1000000')},
            'ABBA': {'15th': Decimal('500000'), '30th': Decimal('500000')}
        }
    """
    return {
        'YAHSHUA': {
            '15th': get_setting('payroll_yahshua_15th', Decimal('1000000')),
            '30th': get_setting('payroll_yahshua_30th', Decimal('1000000'))
        },
        'ABBA': {
            '15th': get_setting('payroll_abba_15th', Decimal('500000')),
            '30th': get_setting('payroll_abba_30th', Decimal('500000'))
        }
    }


def get_payment_terms_config() -> Dict[str, int]:
    """
    Get payment terms configuration.

    Returns:
        Dictionary with payment timing settings

    Example:
        >>> get_payment_terms_config()
        {'invoice_lead_days': 15, 'payment_terms_days': 30, 'realistic_delay_days': 10, 'default_reliability': 80}
    """
    return {
        'invoice_lead_days': get_setting('invoice_lead_days', 15),
        'payment_terms_days': get_setting('payment_terms_days', 30),
        'realistic_delay_days': get_setting('realistic_delay_days', 10),
        'default_reliability': get_setting('default_reliability', 80)
    }


def get_entity_mapping() -> Dict[str, str]:
    """
    Get entity mapping (acquisition source -> entity).

    Returns:
        Dictionary mapping acquisition sources to entities

    Example:
        >>> get_entity_mapping()
        {'RCBC Partner': 'YAHSHUA', 'Globe Partner': 'YAHSHUA', 'TAI': 'ABBA', ...}
    """
    default_mapping = {
        'RCBC Partner': 'YAHSHUA',
        'Globe Partner': 'YAHSHUA',
        'YOWI': 'YAHSHUA',
        'TAI': 'ABBA',
        'PEI': 'ABBA'
    }
    return get_setting('entity_mapping', default_mapping)


def get_alert_thresholds() -> Dict[str, Union[Decimal, int]]:
    """
    Get alert threshold configuration.

    Returns:
        Dictionary with alert thresholds

    Example:
        >>> get_alert_thresholds()
        {'cash_warning': Decimal('5000000'), 'cash_critical': Decimal('2000000'), ...}
    """
    return {
        'cash_warning': get_setting('alert_cash_warning', Decimal('5000000')),
        'cash_critical': get_setting('alert_cash_critical', Decimal('2000000')),
        'days_advance': get_setting('alert_days_advance', 30),
        'contract_expiry_days': get_setting('alert_contract_expiry_days', 90)
    }


def get_google_sheets_config() -> Dict[str, str]:
    """
    Get Google Sheets configuration.

    Returns:
        Dictionary with Google Sheets settings

    Example:
        >>> get_google_sheets_config()
        {'url': 'https://docs.google.com/...', 'customers_sheet': 'Customer Contracts', ...}
    """
    return {
        'url': get_setting('google_sheets_url', ''),
        'customers_sheet': get_setting('sheet_name_customers', 'Customer Contracts'),
        'vendors_sheet': get_setting('sheet_name_vendors', 'Vendor Contracts'),
        'bank_balances_sheet': get_setting('sheet_name_bank_balances', 'Bank Balances')
    }


def extract_spreadsheet_id(url: str) -> str:
    """
    Extract spreadsheet ID from Google Sheets URL.

    Args:
        url: Google Sheets URL

    Returns:
        Spreadsheet ID

    Example:
        >>> extract_spreadsheet_id('https://docs.google.com/spreadsheets/d/abc123/edit')
        'abc123'
    """
    try:
        return url.split("/d/")[1].split("/")[0]
    except (IndexError, AttributeError):
        return ''


# ═══════════════════════════════════════════════════════════════════
# ENTITY MANAGEMENT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def init_entities_table() -> bool:
    """
    Initialize entities table if it doesn't exist.

    Returns:
        True if successful, False otherwise
    """
    try:
        with db_manager.engine.connect() as conn:
            # Create entities table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    short_code VARCHAR(50) UNIQUE NOT NULL,
                    full_name VARCHAR(200) NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Create indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_entities_active ON entities(is_active)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_entities_order ON entities(display_order)"))

            # Seed default entities if table is empty
            result = conn.execute(text("SELECT COUNT(*) FROM entities")).fetchone()
            if result[0] == 0:
                conn.execute(text("""
                    INSERT INTO entities (short_code, full_name, display_order) VALUES
                        ('YAHSHUA', 'YAHSHUA Outsourcing Worldwide Inc', 1),
                        ('ABBA', 'The ABBA Initiative OPC', 2)
                """))

            conn.commit()
            return True
    except Exception as e:
        print(f"Error initializing entities table: {e}")
        return False


def get_all_entities(include_inactive: bool = False) -> List[Dict]:
    """
    Get all entities from database.

    Args:
        include_inactive: Whether to include inactive entities

    Returns:
        List of entity dictionaries

    Example:
        >>> get_all_entities()
        [{'short_code': 'YAHSHUA', 'full_name': 'YAHSHUA Outsourcing Worldwide Inc', ...}]
    """
    try:
        # Ensure table exists
        init_entities_table()

        with db_manager.engine.connect() as conn:
            if include_inactive:
                query = text("SELECT id, short_code, full_name, is_active, display_order FROM entities ORDER BY display_order")
            else:
                query = text("SELECT id, short_code, full_name, is_active, display_order FROM entities WHERE is_active = 1 ORDER BY display_order")

            results = conn.execute(query).fetchall()

            return [
                {
                    'id': row[0],
                    'short_code': row[1],
                    'full_name': row[2],
                    'is_active': bool(row[3]),
                    'display_order': row[4]
                }
                for row in results
            ]
    except Exception as e:
        print(f"Error getting entities: {e}")
        # Return defaults
        return [
            {'id': 1, 'short_code': 'YAHSHUA', 'full_name': 'YAHSHUA Outsourcing Worldwide Inc', 'is_active': True, 'display_order': 1},
            {'id': 2, 'short_code': 'ABBA', 'full_name': 'The ABBA Initiative OPC', 'is_active': True, 'display_order': 2}
        ]


def get_entity_by_code(short_code: str) -> Optional[Dict]:
    """
    Get a single entity by short code.

    Args:
        short_code: Entity short code (e.g., 'YAHSHUA')

    Returns:
        Entity dictionary or None if not found
    """
    try:
        with db_manager.engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, short_code, full_name, is_active, display_order FROM entities WHERE short_code = :code"),
                {'code': short_code}
            ).fetchone()

            if result:
                return {
                    'id': result[0],
                    'short_code': result[1],
                    'full_name': result[2],
                    'is_active': bool(result[3]),
                    'display_order': result[4]
                }
    except Exception:
        pass
    return None


def create_entity(
    short_code: str,
    full_name: str,
    display_order: int = 0,
    updated_by: Optional[str] = None
) -> bool:
    """
    Create a new entity.

    Args:
        short_code: Unique short code (e.g., 'NEWCO')
        full_name: Full legal name
        display_order: Display order in UI
        updated_by: Username who created the entity

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure table exists
        init_entities_table()

        with db_manager.engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO entities (short_code, full_name, display_order)
                    VALUES (:code, :name, :order)
                """),
                {'code': short_code.upper(), 'name': full_name, 'order': display_order}
            )
            conn.commit()

            # Initialize default payroll settings for new entity
            code_lower = short_code.lower()
            set_setting(f'payroll_{code_lower}_15th', Decimal('0'), 'decimal', 'payroll', updated_by=updated_by)
            set_setting(f'payroll_{code_lower}_30th', Decimal('0'), 'decimal', 'payroll', updated_by=updated_by)

            return True
    except Exception as e:
        print(f"Error creating entity: {e}")
        return False


def update_entity(
    short_code: str,
    full_name: Optional[str] = None,
    is_active: Optional[bool] = None,
    display_order: Optional[int] = None,
    updated_by: Optional[str] = None
) -> bool:
    """
    Update an existing entity.

    Args:
        short_code: Entity short code to update
        full_name: New full name (optional)
        is_active: New active status (optional)
        display_order: New display order (optional)
        updated_by: Username who made the update

    Returns:
        True if successful, False otherwise
    """
    try:
        updates = []
        params = {'code': short_code}

        if full_name is not None:
            updates.append("full_name = :name")
            params['name'] = full_name

        if is_active is not None:
            updates.append("is_active = :active")
            params['active'] = 1 if is_active else 0

        if display_order is not None:
            updates.append("display_order = :order")
            params['order'] = display_order

        if not updates:
            return True  # Nothing to update

        updates.append("updated_at = datetime('now')")

        query = f"UPDATE entities SET {', '.join(updates)} WHERE short_code = :code"

        with db_manager.engine.connect() as conn:
            conn.execute(text(query), params)
            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating entity: {e}")
        return False


def get_valid_entity_codes() -> List[str]:
    """
    Get list of active entity short codes.

    Returns:
        List of entity codes (e.g., ['YAHSHUA', 'ABBA'])
    """
    entities = get_all_entities(include_inactive=False)
    return [e['short_code'] for e in entities]


def get_entity_full_name_from_db(short_code: str) -> str:
    """
    Get full legal name for an entity from database.

    Args:
        short_code: Entity short code

    Returns:
        Full legal name or short_code if not found
    """
    entity = get_entity_by_code(short_code)
    if entity:
        return entity['full_name']
    return short_code


def get_payroll_config_dynamic() -> Dict[str, Dict[str, Decimal]]:
    """
    Get payroll configuration for ALL active entities.

    Returns:
        Dictionary with entity payroll amounts

    Example:
        >>> get_payroll_config_dynamic()
        {
            'YAHSHUA': {'15th': Decimal('1000000'), '30th': Decimal('1000000')},
            'ABBA': {'15th': Decimal('500000'), '30th': Decimal('500000')},
            'NEWCO': {'15th': Decimal('0'), '30th': Decimal('0')}
        }
    """
    config = {}
    entity_codes = get_valid_entity_codes()

    for code in entity_codes:
        code_lower = code.lower()
        config[code] = {
            '15th': get_setting(f'payroll_{code_lower}_15th', Decimal('0')),
            '30th': get_setting(f'payroll_{code_lower}_30th', Decimal('0'))
        }

    return config
