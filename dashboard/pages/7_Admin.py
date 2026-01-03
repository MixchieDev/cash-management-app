"""
Admin Page - User Management
Manage system users and permissions (admin only).
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth
from dashboard.components.styling import load_css, page_header
from dashboard.theme import COLORS

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Admin - JESUS Company",
    page_icon="👥",
    layout="wide"
)

load_css()
require_auth(required_role='admin')

page_header("User Administration", "Manage system users and permissions")

st.markdown(f'''
<div style="
    background: {COLORS['info_light']};
    border-left: 4px solid {COLORS['info']};
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    font-size: 14px;
    color: {COLORS['text_primary']};
    margin: 16px 0;
">
    <strong>User Management (Phase 1 - Simplified)</strong><br>
    Current user system uses hardcoded credentials for simplicity.
    Full user management with database storage coming in Phase 2.
</div>
''', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# CURRENT USERS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## Current Users")

import pandas as pd

users_data = [
    {
        'Username': 'admin',
        'Name': 'CFO Mich',
        'Email': 'cfo@jesuscompany.com',
        'Role': 'Admin',
        'Status': '✅ Active',
        'Password': 'admin123 (default)'
    },
    {
        'Username': 'viewer',
        'Name': 'Team Viewer',
        'Email': 'team@jesuscompany.com',
        'Role': 'Viewer',
        'Status': '✅ Active',
        'Password': 'viewer123 (default)'
    }
]

df_users = pd.DataFrame(users_data)
st.dataframe(df_users, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════
# ROLE PERMISSIONS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## Role Permissions")

permissions_data = [
    {
        'Permission': 'View Dashboard',
        'Admin': '✅',
        'Viewer': '✅'
    },
    {
        'Permission': 'Create Scenarios',
        'Admin': '✅',
        'Viewer': '❌'
    },
    {
        'Permission': 'Sync Data from Google Sheets',
        'Admin': '✅',
        'Viewer': '❌'
    },
    {
        'Permission': 'View All Pages',
        'Admin': '✅',
        'Viewer': '✅ (Read-only)'
    },
    {
        'Permission': 'Manage Users',
        'Admin': '✅',
        'Viewer': '❌'
    },
    {
        'Permission': 'Edit Configuration',
        'Admin': '✅ (via files)',
        'Viewer': '❌'
    }
]

df_permissions = pd.DataFrame(permissions_data)
st.table(df_permissions)

# ═══════════════════════════════════════════════════════════════════
# CHANGE PASSWORD (PLACEHOLDER)
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## Change Password")

st.warning("""
⚠️ **Phase 1 Limitation**

Password changes are not yet supported. To change passwords:

1. Edit `auth/authentication.py`
2. Use the `hash_password()` function to generate a new password hash
3. Update the `USERS_DB` dictionary with the new hash
4. Restart the application

**Example:**
```python
from auth.authentication import hash_password

# Generate hash for new password
new_hash = hash_password('new_password_here')
print(new_hash)

# Copy the hash to USERS_DB in auth/authentication.py
```

*Full user management with password changes coming in Phase 2.*
""")

# ═══════════════════════════════════════════════════════════════════
# ADD NEW USER (PLACEHOLDER)
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## Add New User")

with st.form("add_user_form"):
    col1, col2 = st.columns(2)

    with col1:
        new_username = st.text_input("Username", placeholder="e.g., jsmith")
        new_email = st.text_input("Email", placeholder="e.g., jsmith@company.com")
        new_password = st.text_input("Password", type="password")

    with col2:
        new_fullname = st.text_input("Full Name", placeholder="e.g., John Smith")
        new_role = st.selectbox("Role", ["viewer", "admin"])

    submitted = st.form_submit_button("Create User", type="primary")

    if submitted:
        st.warning("""
⚠️ **Phase 1 Limitation**

User creation is not yet supported in the UI. To add a new user:

1. Edit `auth/authentication.py`
2. Generate password hash: `hash_password('your_password')`
3. Add new entry to `USERS_DB` dictionary
4. Restart the application

*Full user management UI coming in Phase 2.*
        """)

# ═══════════════════════════════════════════════════════════════════
# SYSTEM INFO
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## System Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Users", "2")

with col2:
    st.metric("Admin Users", "1")

with col3:
    st.metric("Viewer Users", "1")

# ═══════════════════════════════════════════════════════════════════
# SECURITY NOTES
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Security Best Practices")

st.markdown("""
**Current Security Measures:**

- ✅ Passwords hashed with bcrypt
- ✅ Role-based access control (Admin vs Viewer)
- ✅ Session management via Streamlit
- ✅ Protected routes (authentication required)

**Recommended for Production:**

1. **Change Default Passwords** - Replace 'admin123' and 'viewer123' immediately
2. **Database Storage** - Move users from hardcoded to database
3. **Password Policies** - Enforce minimum length, complexity
4. **Session Timeout** - Auto-logout after inactivity
5. **Audit Logging** - Track user actions
6. **2FA** - Two-factor authentication for admins

*Production-ready security features coming in Phase 2.*
""")
