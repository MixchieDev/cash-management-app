"""
JESUS Company - Strategic Cash Management System
Main entry point for Streamlit dashboard with authentication.

Run with: streamlit run dashboard/app.py
"""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.authentication import init_session_state, login_form, login_page, logout

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="JESUS Company - Cash Management",
    page_icon="₱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════════
# LOAD CUSTOM CSS
# ═══════════════════════════════════════════════════════════════════
css_path = Path(__file__).parent / "styles.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# INITIALIZE SESSION STATE
# ═══════════════════════════════════════════════════════════════════
init_session_state()

# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    # Hide sidebar completely on login page
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="stSidebarNav"] { display: none !important; }
            section[data-testid="stSidebarContent"] { display: none !important; }
            .css-1d391kg { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    # Show professional login page
    user = login_page()

    if user:
        # Successful login
        st.session_state.authenticated = True
        st.session_state.username = user['username']
        st.session_state.name = user['name']
        st.session_state.user_role = user['role']
        st.rerun()

    st.stop()

# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATED VIEW
# ═══════════════════════════════════════════════════════════════════

# Sidebar with user info
with st.sidebar:
    st.markdown(f"### {st.session_state.name}")
    st.caption(f"Role: {st.session_state.user_role.capitalize()}")
    st.caption(f"User: @{st.session_state.username}")

    st.markdown("---")

    # Navigation info
    st.markdown("### Navigation")
    st.markdown("""
    - **Home** - Main dashboard
    - **Scenarios** - Create and run scenarios
    - **Scenario Comparison** - Compare multiple scenarios
    - **Contracts** - View customer and vendor contracts
    - **Settings** - View system configuration
    - **Strategic** - Path to ₱250M planning
    - **Admin** - User management (admin only)
    """)

    st.markdown("---")

    # Logout button
    if st.button("Logout", width='stretch'):
        logout()
        st.rerun()

# ═══════════════════════════════════════════════════════════════════
# MAIN CONTENT - Welcome/Home Summary
# ═══════════════════════════════════════════════════════════════════
st.title("₱ JESUS Company - Strategic Cash Management")

st.markdown("""
Welcome to the strategic cash management system. Use the sidebar to navigate to different sections.

### Quick Links

- **Home** - View current cash position and projections
- **Scenarios** - Model the impact of hiring, expenses, or revenue changes
- **Contracts** - Manage customer and vendor contracts
- **Strategic** - Plan your path to ₱250M revenue

### Getting Started

1. **View Current Projections** - Go to Home to see 90-day cash forecast
2. **Create a Scenario** - Go to Scenarios to model "what-if" situations
3. **Review Contracts** - Go to Contracts to see all active agreements
4. **Plan Growth** - Go to Strategic for long-term planning tools
""")

# Quick stats
from database.queries import get_latest_bank_balance, get_total_mrr
from utils.currency_formatter import format_currency
from dashboard.components.styling import kpi_card

try:
    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        yahshua_balance = get_latest_bank_balance('YAHSHUA')
        kpi_card("YAHSHUA Cash", format_currency(yahshua_balance['amount']))

    with col2:
        abba_balance = get_latest_bank_balance('ABBA')
        kpi_card("ABBA Cash", format_currency(abba_balance['amount']))

    with col3:
        total_balance = yahshua_balance['amount'] + abba_balance['amount']
        kpi_card("Consolidated Cash", format_currency(total_balance))

except Exception as e:
    st.warning(f"Unable to load quick stats: {str(e)}")
    st.info("Click 'Sync from Google Sheets' on the Contracts page to load data.")
