"""
Permission constants and role templates for access control.
"""
from typing import List, Dict

# All available permissions with descriptions
ALL_PERMISSIONS: List[Dict[str, str]] = [
    {'key': 'view_dashboard', 'label': 'View Dashboard', 'description': 'View Home dashboard & projections'},
    {'key': 'view_contracts', 'label': 'View Contracts', 'description': 'View customer/vendor contracts'},
    {'key': 'edit_contracts', 'label': 'Edit Contracts', 'description': 'Add/edit/deactivate contracts'},
    {'key': 'view_scenarios', 'label': 'View Scenarios', 'description': 'View saved scenarios'},
    {'key': 'edit_scenarios', 'label': 'Edit Scenarios', 'description': 'Create/edit/delete scenarios'},
    {'key': 'manage_overrides', 'label': 'Manage Overrides', 'description': 'Create/delete payment overrides'},
    {'key': 'import_data', 'label': 'Import Data', 'description': 'Upload CSV data imports'},
    {'key': 'manage_settings', 'label': 'Manage Settings', 'description': 'Change payment terms & config'},
    {'key': 'delete_data', 'label': 'Delete Data', 'description': 'Use Danger Zone bulk deletes'},
    {'key': 'manage_users', 'label': 'Manage Users', 'description': 'Add/edit/delete users & permissions'},
]

PERMISSION_KEYS = [p['key'] for p in ALL_PERMISSIONS]

# Role templates — define which permissions each role gets by default
ROLE_TEMPLATES: Dict[str, List[str]] = {
    'admin': PERMISSION_KEYS,  # All permissions
    'editor': [
        'view_dashboard',
        'view_contracts',
        'edit_contracts',
        'view_scenarios',
        'edit_scenarios',
        'manage_overrides',
    ],
    'viewer': [
        'view_dashboard',
        'view_contracts',
        'view_scenarios',
    ],
}

ROLE_LABELS = {
    'admin': 'Admin',
    'editor': 'Editor',
    'viewer': 'Viewer',
}


def get_default_permissions(role: str) -> List[str]:
    """
    Get default permission keys for a role.

    Args:
        role: Role name ('admin', 'editor', 'viewer')

    Returns:
        List of permission key strings
    """
    return ROLE_TEMPLATES.get(role, ROLE_TEMPLATES['viewer'])


def get_permission_label(key: str) -> str:
    """Get human-readable label for a permission key."""
    for p in ALL_PERMISSIONS:
        if p['key'] == key:
            return p['label']
    return key
