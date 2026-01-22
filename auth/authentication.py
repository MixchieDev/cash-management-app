"""
Simple authentication system for Streamlit dashboard.
Uses streamlit-authenticator for user management.
"""
import streamlit as st
from typing import Dict, Optional
import bcrypt


# TEMPORARY: Hardcoded users for Phase 1
# TODO Phase 2: Move to database with proper user management
USERS_DB = {
    'admin': {
        'name': 'CFO Mich',
        'password': '$2b$12$twD0n0hTzQj5L6V.Jck2hOgRC7JWIhU9.OeAklgaRa70VOzC5H/mW',  # 'admin123'
        'email': 'cfo@jesuscompany.com',
        'role': 'admin'
    },
    'viewer': {
        'name': 'Team Viewer',
        'password': '$2b$12$2ZexoN.oKUOdoKwOG0lPU.fEbocoNR8y.jh6ecNkxF1dk1CFvY9d.',  # 'viewer123'
        'email': 'team@jesuscompany.com',
        'role': 'viewer'
    }
}


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        password: Plain text password
        hashed: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def authenticate(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user.

    Args:
        username: Username
        password: Plain text password

    Returns:
        User dict if authenticated, None otherwise
    """
    user = USERS_DB.get(username)
    if not user:
        return None

    if verify_password(password, user['password']):
        return {
            'username': username,
            'name': user['name'],
            'email': user['email'],
            'role': user['role']
        }

    return None


def login_form() -> Optional[Dict]:
    """
    Display login form and handle authentication (legacy).

    Returns:
        User dict if logged in, None otherwise
    """
    st.markdown("## JESUS Company - Cash Management")
    st.markdown("---")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", width='stretch')

        if submit:
            user = authenticate(username, password)
            if user:
                return user
            else:
                st.error("Invalid username or password")
                return None

    return None


def login_page() -> Optional[Dict]:
    """
    Display professional login page with centered card design.

    Returns:
        User dict if logged in, None otherwise
    """
    # Center the login card using columns
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        # Add vertical spacing
        st.markdown("<div style='height: 8vh'></div>", unsafe_allow_html=True)

        # Branding header (no card)
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

        # Login form
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

        # Footer
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


def logout():
    """Clear session state and log out user."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def require_auth(required_role: Optional[str] = None):
    """
    Decorator to require authentication for a page.

    Args:
        required_role: Required role ('admin' or 'viewer'). None = any authenticated user
    """
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.warning("Please log in to access this page")
        st.stop()

    if required_role and st.session_state.get('user_role') != required_role:
        st.error(f"Access Denied: {required_role} privileges required")
        st.stop()


def init_session_state():
    """Initialize session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'name' not in st.session_state:
        st.session_state.name = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
