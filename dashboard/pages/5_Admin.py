"""
Admin Page - User Management
Manage system users and permissions.
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_permission, check_permission
from auth.permissions import ALL_PERMISSIONS, PERMISSION_KEYS, ROLE_TEMPLATES, ROLE_LABELS, get_default_permissions
from dashboard.components.styling import load_css, page_header
from dashboard.theme import COLORS
from database.queries import (
    get_all_users, create_user, update_user, update_user_permissions,
    reset_user_password, deactivate_user, reactivate_user
)

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Admin - JESUS Company",
    page_icon="👥",
    layout="wide"
)

load_css()
require_permission('manage_users')

page_header("User Administration", "Manage system users and permissions")

# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = 'list'  # list, add, edit, reset_pw
if 'edit_user_id' not in st.session_state:
    st.session_state.edit_user_id = None

# ═══════════════════════════════════════════════════════════════════
# LOAD USERS
# ═══════════════════════════════════════════════════════════════════
users = get_all_users()

# ═══════════════════════════════════════════════════════════════════
# USER LIST
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")

col_header, col_add = st.columns([3, 1])
with col_header:
    st.markdown("## Users")
with col_add:
    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
    if st.button("Add User", type="primary", width='stretch'):
        st.session_state.admin_mode = 'add'
        st.rerun()

if not users:
    st.info("No users found. Click 'Add User' to create one.")
else:
    import pandas as pd

    users_data = []
    for u in users:
        users_data.append({
            'Username': u['username'],
            'Name': u['name'],
            'Role': ROLE_LABELS.get(u['role'], u['role']),
            'Permissions': len(u['permissions']),
            'Status': 'Active' if u['is_active'] else 'Inactive',
        })

    df_users = pd.DataFrame(users_data)

    event = st.dataframe(
        df_users,
        width='stretch',
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="admin_user_table",
    )

    selected_rows = event.selection.rows if event and event.selection else []

    if selected_rows:
        selected_user = users[selected_rows[0]]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Edit User", width='stretch'):
                st.session_state.admin_mode = 'edit'
                st.session_state.edit_user_id = selected_user['id']
                st.rerun()

        with col2:
            if st.button("Reset Password", width='stretch'):
                st.session_state.admin_mode = 'reset_pw'
                st.session_state.edit_user_id = selected_user['id']
                st.rerun()

        with col3:
            if selected_user['is_active']:
                if st.button("Deactivate", width='stretch'):
                    # Don't let admin deactivate themselves
                    if selected_user['username'] == st.session_state.username:
                        st.error("You cannot deactivate your own account")
                    else:
                        deactivate_user(selected_user['id'])
                        st.success(f"User '{selected_user['username']}' deactivated")
                        st.rerun()
            else:
                if st.button("Reactivate", width='stretch'):
                    reactivate_user(selected_user['id'])
                    st.success(f"User '{selected_user['username']}' reactivated")
                    st.rerun()

        with col4:
            # Show permissions summary
            st.caption(f"Permissions: {', '.join(selected_user['permissions'][:3])}{'...' if len(selected_user['permissions']) > 3 else ''}")

# ═══════════════════════════════════════════════════════════════════
# ADD USER FORM
# ═══════════════════════════════════════════════════════════════════
if st.session_state.admin_mode == 'add':
    st.markdown("---")
    st.markdown("## Add New User")

    with st.form("add_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input("Username", placeholder="e.g., jsmith")
            show_add_pw = st.checkbox("Show password", key="add_show_pw")
            new_password = st.text_input(
                "Password",
                type="default" if show_add_pw else "password",
            )

        with col2:
            new_name = st.text_input("Full Name", placeholder="e.g., John Smith")
            new_role = st.selectbox("Role", ['admin', 'editor', 'viewer'],
                                   format_func=lambda r: ROLE_LABELS.get(r, r),
                                   index=2)

        # Show what permissions this role gets
        default_perms = get_default_permissions(new_role)
        st.caption(f"**{ROLE_LABELS[new_role]}** default permissions: {', '.join(default_perms)}")

        col_submit, col_cancel = st.columns(2)
        submitted = st.form_submit_button("Create User", type="primary")

    # Cancel button outside form
    if st.button("Cancel"):
        st.session_state.admin_mode = 'list'
        st.rerun()

    if submitted:
        if not new_username or not new_password or not new_name:
            st.error("All fields are required")
        elif len(new_password) < 6:
            st.error("Password must be at least 6 characters")
        else:
            try:
                create_user(new_username, new_password, new_name, new_role)
                st.success(f"User '{new_username}' created with role '{ROLE_LABELS[new_role]}'")
                st.session_state.admin_mode = 'list'
                st.rerun()
            except ValueError as e:
                st.error(str(e))

# ═══════════════════════════════════════════════════════════════════
# EDIT USER
# ═══════════════════════════════════════════════════════════════════
if st.session_state.admin_mode == 'edit' and st.session_state.edit_user_id:
    st.markdown("---")

    # Find the user
    edit_user = next((u for u in users if u['id'] == st.session_state.edit_user_id), None)

    if not edit_user:
        st.error("User not found")
        st.session_state.admin_mode = 'list'
        st.rerun()
    else:
        st.markdown(f"## Edit User: {edit_user['username']}")

        # Name, password, and role
        with st.form("edit_user_form"):
            edit_name = st.text_input("Full Name", value=edit_user['name'])

            # Password field with show/hide toggle
            st.markdown("#### Password")
            show_pw = st.checkbox("Show password", key="edit_show_pw")
            edit_password = st.text_input(
                "New Password (leave blank to keep current)",
                type="default" if show_pw else "password",
                placeholder="Enter new password to change",
            )

            edit_role = st.selectbox(
                "Role Template",
                ['admin', 'editor', 'viewer'],
                format_func=lambda r: ROLE_LABELS.get(r, r),
                index=['admin', 'editor', 'viewer'].index(edit_user['role']),
                help="Changing role will update to the role's default permissions"
            )

            st.markdown("### Permissions")
            st.caption("Toggle individual permissions for this user")

            # Permission checkboxes
            perm_values = {}
            cols = st.columns(2)
            for i, perm in enumerate(ALL_PERMISSIONS):
                with cols[i % 2]:
                    current_granted = perm['key'] in edit_user['permissions']
                    perm_values[perm['key']] = st.checkbox(
                        f"**{perm['label']}** — {perm['description']}",
                        value=current_granted,
                        key=f"perm_{perm['key']}"
                    )

            col_save, col_apply_role = st.columns(2)
            save_clicked = st.form_submit_button("Save Changes", type="primary")

        # Buttons outside form
        col_role_btn, col_cancel_btn = st.columns(2)
        with col_role_btn:
            if st.button(f"Apply '{ROLE_LABELS[edit_role]}' Defaults", width='stretch'):
                role_perms = get_default_permissions(edit_role)
                role_perm_dict = {k: (k in role_perms) for k in PERMISSION_KEYS}
                update_user(edit_user['id'], role=edit_role)
                update_user_permissions(edit_user['id'], role_perm_dict)
                st.success(f"Applied {ROLE_LABELS[edit_role]} defaults")
                st.rerun()

        with col_cancel_btn:
            if st.button("Cancel", width='stretch'):
                st.session_state.admin_mode = 'list'
                st.session_state.edit_user_id = None
                st.rerun()

        if save_clicked:
            if edit_password and len(edit_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                try:
                    update_user(edit_user['id'], name=edit_name, role=edit_role)
                    update_user_permissions(edit_user['id'], perm_values)
                    if edit_password:
                        reset_user_password(edit_user['id'], edit_password)
                    st.success(f"User '{edit_user['username']}' updated")
                    st.session_state.admin_mode = 'list'
                    st.session_state.edit_user_id = None
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

# ═══════════════════════════════════════════════════════════════════
# RESET PASSWORD
# ═══════════════════════════════════════════════════════════════════
if st.session_state.admin_mode == 'reset_pw' and st.session_state.edit_user_id:
    st.markdown("---")

    edit_user = next((u for u in users if u['id'] == st.session_state.edit_user_id), None)

    if not edit_user:
        st.error("User not found")
        st.session_state.admin_mode = 'list'
        st.rerun()
    else:
        st.markdown(f"## Reset Password: {edit_user['username']}")

        with st.form("reset_pw_form"):
            show_reset_pw = st.checkbox("Show password", key="reset_show_pw")
            new_pw = st.text_input(
                "New Password",
                type="default" if show_reset_pw else "password",
            )
            confirm_pw = st.text_input(
                "Confirm Password",
                type="default" if show_reset_pw else "password",
            )
            reset_clicked = st.form_submit_button("Reset Password", type="primary")

        if st.button("Cancel"):
            st.session_state.admin_mode = 'list'
            st.session_state.edit_user_id = None
            st.rerun()

        if reset_clicked:
            if not new_pw:
                st.error("Password is required")
            elif len(new_pw) < 6:
                st.error("Password must be at least 6 characters")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match")
            else:
                reset_user_password(edit_user['id'], new_pw)
                st.success(f"Password reset for '{edit_user['username']}'")
                st.session_state.admin_mode = 'list'
                st.session_state.edit_user_id = None
                st.rerun()

# ═══════════════════════════════════════════════════════════════════
# ROLE REFERENCE
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")

with st.expander("Role & Permission Reference"):
    st.markdown("### Role Templates")
    st.caption("These are the default permissions for each role. Individual permissions can be customized per user.")

    import pandas as pd

    perm_data = []
    for perm in ALL_PERMISSIONS:
        row = {'Permission': perm['label'], 'Description': perm['description']}
        for role_key, role_label in ROLE_LABELS.items():
            row[role_label] = 'Yes' if perm['key'] in ROLE_TEMPLATES[role_key] else '—'
        perm_data.append(row)

    df_perms = pd.DataFrame(perm_data)
    st.table(df_perms)
