"""
Shared state management across dashboard pages.
Provides global entity selector and cross-page state persistence.
"""
import streamlit as st
from typing import List


def get_entity_options() -> List[str]:
    """Get list of entity options for selectors."""
    try:
        from database.settings_manager import get_valid_entity_codes
        codes = get_valid_entity_codes()
        return ["Consolidated"] + codes
    except Exception:
        return ["Consolidated", "YAHSHUA", "ABBA"]


def get_selected_entity() -> str:
    """
    Get the currently selected entity from session state.

    Returns:
        Entity code or 'Consolidated'
    """
    return st.session_state.get('global_entity', 'Consolidated')


def render_entity_selector(key_suffix: str = '') -> str:
    """
    Render a global entity selector that persists across pages.

    Args:
        key_suffix: Optional suffix for the widget key (for multiple selectors)

    Returns:
        Selected entity code
    """
    options = get_entity_options()
    current = get_selected_entity()

    if current not in options:
        current = options[0]

    selected = st.selectbox(
        "Entity",
        options=options,
        index=options.index(current),
        key=f"global_entity_selector{key_suffix}",
    )

    st.session_state['global_entity'] = selected
    return selected


def get_entity_for_query() -> str:
    """
    Get entity value suitable for database queries.
    Converts 'Consolidated' to None (meaning all entities).

    Returns:
        Entity code string or None
    """
    entity = get_selected_entity()
    if entity in ('Consolidated', 'All'):
        return None
    return entity
