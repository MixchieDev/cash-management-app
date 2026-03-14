"""
Database-backed authentication system for Streamlit dashboard.
Supports granular permission-based access control.
"""
import streamlit as st
import bcrypt
from typing import Dict, Optional


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a bcrypt hash.

    Args:
        password: Plain text password
        hashed: Bcrypt hashed password

    Returns:
        True if password matches
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password string
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def authenticate(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user against the database.

    Args:
        username: Username
        password: Plain text password

    Returns:
        User dict if authenticated, None otherwise
    """
    from database.queries import get_user_by_username

    user = get_user_by_username(username)
    if not user:
        return None

    if not user['is_active']:
        return None

    if verify_password(password, user['password_hash']):
        return {
            'username': user['username'],
            'name': user['name'],
            'role': user['role'],
            'permissions': user['permissions'],
        }

    return None


def login_page() -> Optional[Dict]:
    """
    Display professional login page with centered card design.

    Returns:
        User dict if logged in, None otherwise
    """
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        st.markdown("<div style='height: 8vh'></div>", unsafe_allow_html=True)

        st.markdown("""
            <div style="
                text-align: center;
                margin-bottom: 32px;
            ">
                <div style="font-size: 56px; margin-bottom: 16px;">💼</div>
                <h1 style="
                    font-size: 26px;
                    font-weight: 600;
                    margin-bottom: 8px;
                    color: #1D1D1F;
                    font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
                ">JESUS Company</h1>
                <p style="
                    color: #86868B;
                    font-size: 15px;
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
                ">Cash Management System</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")

            st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

            submit = st.form_submit_button("Sign In", width='stretch', type="primary")

            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                    return None

                user = authenticate(username, password)
                if user:
                    return user
                else:
                    st.error("Invalid username or password")
                    return None

        st.markdown("""
            <div style="
                text-align: center;
                margin-top: 24px;
                color: #AEAEB2;
                font-size: 13px;
            ">
                Strategic Financial Planning Tool
            </div>
        """, unsafe_allow_html=True)

    return None


def login_form() -> Optional[Dict]:
    """Legacy login form (kept for compatibility)."""
    return login_page()


def logout():
    """Clear session state and log out user."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def require_auth(required_role: Optional[str] = None):
    """
    Require authentication for a page.

    Args:
        required_role: Required role ('admin' or None). None = any authenticated user.
    """
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("Please log in to access this page")
        st.stop()

    if required_role and st.session_state.get('user_role') != required_role:
        st.error(f"Access Denied: {required_role} privileges required")
        st.stop()


def require_permission(permission: str):
    """
    Require a specific permission to access content.
    Shows error and stops if user doesn't have the permission.

    Args:
        permission: Permission key (e.g. 'view_dashboard', 'edit_contracts')
    """
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("Please log in to access this page")
        st.stop()

    user_permissions = st.session_state.get('user_permissions', [])
    if permission not in user_permissions:
        from auth.permissions import get_permission_label
        label = get_permission_label(permission)
        st.error(f"Access Denied: You don't have the '{label}' permission.")
        st.info("Contact your administrator to request access.")
        st.stop()


def check_permission(permission: str) -> bool:
    """
    Check if current user has a permission (without stopping).

    Args:
        permission: Permission key

    Returns:
        True if user has the permission
    """
    user_permissions = st.session_state.get('user_permissions', [])
    return permission in user_permissions


def init_session_state():
    """Initialize session state variables and ensure default users exist."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'name' not in st.session_state:
        st.session_state.name = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_permissions' not in st.session_state:
        st.session_state.user_permissions = []

    # Seed default users on first run
    if '_users_seeded' not in st.session_state:
        from database.db_manager import ensure_users_seeded
        ensure_users_seeded()
        st.session_state._users_seeded = True
