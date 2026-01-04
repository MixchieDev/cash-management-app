"""
Entity assignment mapping for JESUS Company.
Maps customer acquisition sources to legal entities.

YAHSHUA Outsourcing Worldwide Inc = Customers from RCBC, Globe, YOWI
ABBA Initiative OPC = Customers from TAI, PEI

NOTE: Entity mappings are now stored in the database and editable from the
Settings page. This file provides fallback defaults and helper functions.
"""
from typing import Dict

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

# ═══════════════════════════════════════════════════════════════════
# VALID ENTITIES
# ═══════════════════════════════════════════════════════════════════
VALID_ENTITIES = ["YAHSHUA", "ABBA", "Consolidated"]


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
        Entity name ('YAHSHUA' or 'ABBA')

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
    Get full legal name of entity.

    Args:
        entity_code: 'YAHSHUA' or 'ABBA'

    Returns:
        Full legal entity name
    """
    entity_names = {
        "YAHSHUA": "YAHSHUA Outsourcing Worldwide Inc",
        "ABBA": "The ABBA Initiative OPC",
        "Consolidated": "Consolidated (Both Entities)"
    }
    return entity_names.get(entity_code, entity_code)


def validate_entity(entity: str) -> bool:
    """
    Validate entity code is valid.

    Args:
        entity: Entity code to validate

    Returns:
        True if valid, False otherwise
    """
    return entity in VALID_ENTITIES or entity in ["YAHSHUA", "ABBA"]
