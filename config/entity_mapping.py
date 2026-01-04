"""
Entity assignment mapping for JESUS Company.
Maps customer acquisition sources to legal entities.

NOTE: Both entities and mappings are now stored in the database and editable
from the Settings page. This file provides fallback defaults and helper functions.
"""
from typing import Dict, List

# ═══════════════════════════════════════════════════════════════════
# DEFAULT ACQUISITION SOURCE → ENTITY MAPPING (Fallback)
# ═══════════════════════════════════════════════════════════════════
DEFAULT_ENTITY_MAPPING = {
    # YAHSHUA Outsourcing Worldwide Inc
    "RCBC Partner": "YAHSHUA",
    "Globe Partner": "YAHSHUA",
    "YOWI": "YAHSHUA",

    # ABBA Initiative OPC
    "TAI": "ABBA",
    "PEI": "ABBA",
}

# Default valid entities (fallback)
DEFAULT_VALID_ENTITIES = ["YAHSHUA", "ABBA", "Consolidated"]


def get_valid_entities() -> List[str]:
    """
    Get list of valid entity codes from database.
    Falls back to defaults if database unavailable.

    Returns:
        List of valid entity codes including 'Consolidated'

    Example:
        >>> get_valid_entities()
        ['YAHSHUA', 'ABBA', 'Consolidated']
    """
    try:
        from database.settings_manager import get_valid_entity_codes
        codes = get_valid_entity_codes()
        # Always include Consolidated as a special aggregate option
        if 'Consolidated' not in codes:
            codes.append('Consolidated')
        return codes
    except Exception:
        return DEFAULT_VALID_ENTITIES.copy()


# For backward compatibility - but prefer get_valid_entities() function
VALID_ENTITIES = DEFAULT_VALID_ENTITIES


def get_entity_mapping() -> Dict[str, str]:
    """
    Get entity mapping from database with fallback to defaults.

    Returns:
        Dictionary mapping acquisition sources to entities
    """
    try:
        from database.settings_manager import get_entity_mapping as db_get_mapping
        return db_get_mapping()
    except Exception:
        return DEFAULT_ENTITY_MAPPING.copy()


# For backward compatibility
ENTITY_MAPPING = get_entity_mapping()


# ═══════════════════════════════════════════════════════════════════
# ENTITY ASSIGNMENT FUNCTION
# ═══════════════════════════════════════════════════════════════════
def assign_entity(acquisition_source: str) -> str:
    """
    Assign entity based on customer acquisition source.

    Args:
        acquisition_source: Who acquired the client (from Google Sheets)

    Returns:
        Entity name (e.g., 'YAHSHUA', 'ABBA')

    Raises:
        ValueError: If acquisition source is not mapped

    Examples:
        >>> assign_entity("RCBC Partner")
        'YAHSHUA'
        >>> assign_entity("TAI")
        'ABBA'
        >>> assign_entity("Unknown Partner")
        ValueError: Unmapped acquisition source: Unknown Partner
    """
    if not acquisition_source:
        raise ValueError("Acquisition source cannot be empty")

    acquisition_source = acquisition_source.strip()

    # Get current mapping from database
    current_mapping = get_entity_mapping()

    if acquisition_source not in current_mapping:
        raise ValueError(
            f"Unmapped acquisition source: '{acquisition_source}'. "
            f"Valid sources: {list(current_mapping.keys())}. "
            f"Add this mapping in Settings > Entity Mapping."
        )

    return current_mapping[acquisition_source]


def get_entity_full_name(entity_code: str) -> str:
    """
    Get full legal name of entity from database.

    Args:
        entity_code: Entity short code (e.g., 'YAHSHUA', 'ABBA')

    Returns:
        Full legal entity name
    """
    # Special case for Consolidated
    if entity_code == 'Consolidated':
        return 'Consolidated (All Entities)'

    try:
        from database.settings_manager import get_entity_full_name_from_db
        return get_entity_full_name_from_db(entity_code)
    except Exception:
        # Fallback to hardcoded names
        fallback_names = {
            "YAHSHUA": "YAHSHUA Outsourcing Worldwide Inc",
            "ABBA": "The ABBA Initiative OPC",
        }
        return fallback_names.get(entity_code, entity_code)


def validate_entity(entity: str) -> bool:
    """
    Validate entity code is valid.

    Args:
        entity: Entity code to validate

    Returns:
        True if valid, False otherwise
    """
    valid_entities = get_valid_entities()
    return entity in valid_entities
