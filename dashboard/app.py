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
        st.session_state.user_permissions = user.get('permissions', [])
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
    - **Home** - Main dashboard & projections
    - **Scenarios** - Build, compare & strategic planning
    - **Contracts** - Manage contracts & balances
    - **Settings** - System configuration
    - **Admin** - User management (admin only)
    """)

    st.markdown("---")

    # Logout button
    if st.button("Logout", width='stretch'):
        logout()
        st.rerun()

# ═══════════════════════════════════════════════════════════════════
# MAIN CONTENT - Dashboard Overview
# ═══════════════════════════════════════════════════════════════════
from datetime import date
from decimal import Decimal
from database.queries import get_latest_bank_balance, get_total_mrr, get_total_monthly_expenses
from utils.currency_formatter import format_currency
from dashboard.components.styling import kpi_card

st.markdown(f"### Good {'morning' if __import__('datetime').datetime.now().hour < 12 else 'afternoon'}, {st.session_state.name}")
st.caption(f"Today is {date.today().strftime('%B %d, %Y')}")

# ── Cash Position ─────────────────────────────────────────────────
st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

try:
    yahshua_balance = get_latest_bank_balance('YAHSHUA')
    abba_balance = get_latest_bank_balance('ABBA')
    total_balance = yahshua_balance['amount'] + abba_balance['amount']
    balance_date = yahshua_balance['date']

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        kpi_card("YAHSHUA Cash", format_currency(yahshua_balance['amount']), f"as of {balance_date}")
    with col2:
        kpi_card("ABBA Cash", format_currency(abba_balance['amount']), f"as of {balance_date}")
    with col3:
        kpi_card("Consolidated", format_currency(total_balance), f"as of {balance_date}")

    # ── Revenue & Expenses ────────────────────────────────────────
    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    total_mrr = get_total_mrr(None)
    total_expenses = get_total_monthly_expenses(None)
    net_monthly = total_mrr - total_expenses

    col1, col2, col3 = st.columns(3, gap="medium")
    with col1:
        kpi_card("Monthly Revenue", format_currency(total_mrr), "All entities")
    with col2:
        kpi_card("Monthly Expenses", format_currency(total_expenses), "All entities")
    with col3:
        kpi_card(
            "Net Monthly",
            format_currency(net_monthly),
            "Surplus" if net_monthly >= 0 else "Deficit",
            change_positive=net_monthly >= 0
        )

    # ── Runway ────────────────────────────────────────────────────
    if total_expenses > 0:
        runway_months = int(total_balance / total_expenses)
        runway_label = f"{runway_months} months of runway"
        if runway_months > 12:
            st.success(f"Healthy — {runway_label} at current burn rate")
        elif runway_months > 6:
            st.warning(f"Caution — {runway_label} at current burn rate")
        else:
            st.error(f"Critical — {runway_label} at current burn rate")

except Exception as e:
    st.warning(f"Unable to load financial data: {str(e)}")
    st.info("Go to Settings > Data Import to upload CSV files and load data.")

# ── Quick Actions ─────────────────────────────────────────────────
st.markdown("---")

col1, col2, col3, col4 = st.columns(4, gap="medium")
with col1:
    if st.button("View Projections", use_container_width=True, type="primary"):
        st.switch_page("pages/1_Home.py")
with col2:
    if st.button("Build Scenario", use_container_width=True):
        st.switch_page("pages/2_Scenarios.py")
with col3:
    if st.button("Manage Contracts", use_container_width=True):
        st.switch_page("pages/3_Contracts.py")
with col4:
    if st.button("Settings", use_container_width=True):
        st.switch_page("pages/4_Settings.py")

# ── How It Works ──────────────────────────────────────────────────
st.markdown("---")
with st.expander("How Cash Projections Work"):
    st.markdown("""
**Data Flow:**
- **Bank Balance** (starting cash) + **Customer Payments** (revenue) − **Vendor Expenses** (costs) = **Projected Cash**

**Two Scenarios:**
- **Optimistic** — customers pay on their due date
- **Realistic** — customers pay late (delay configured in Settings)

**Entity Filter:**
- **YAHSHUA** — revenue & expenses for YAHSHUA Outsourcing
- **ABBA** — revenue & expenses for The ABBA Initiative
- **Consolidated** — combined view of both entities

**What Each Page Does:**

| Page | Role in Projections |
|------|-------------------|
| **Home** | View the projection chart, KPIs, and alerts |
| **Scenarios** | Model "what-if" changes (hiring, expenses, revenue) on top of the baseline |
| **Contracts** | Manage the data that feeds projections — customer revenue, vendor expenses, bank balances, and payment overrides |
| **Settings** | Configure the realistic delay and alert thresholds |
""")

with st.expander("Getting Started — Step by Step"):
    st.markdown("""
### First-Time Setup

**Step 1: Import your data** (Settings > Data Import)
- Upload a CSV of your **customer contracts** — company name, monthly fee, payment plan, start date, entity
- Upload a CSV of your **vendor contracts** — vendor name, category, amount, frequency, due date, entity
- Upload your **bank balances** — the current cash in each entity's bank account

**Step 2: Verify your contracts** (Contracts page)
- Check the **Customer Contracts** tab — are all active clients listed with correct monthly fees?
- Check the **Vendor Contracts** tab — are all recurring expenses listed with the right amounts and due days?
- Check **Bank Balances** — does the latest balance match your actual bank account?

**Step 3: View your projections** (Home page)
- Your 90-day cash forecast is now live
- Toggle between **Optimistic** (on-time payments) and **Realistic** (late payments) to see the range
- Check for any alerts — red means projected negative cash, yellow means cash dropping below ₱500K

---

### Ongoing Use

**Weekly: Update bank balance**
- Go to Contracts > Bank Balances > Add Balance
- Enter today's actual bank balance per entity — this keeps projections accurate

**When a new client signs:**
- Go to Contracts > Customer Contracts > Add Customer
- Fill in the monthly fee, payment plan, and start date
- Projections automatically update

**When you add a new expense:**
- Go to Contracts > Vendor Contracts > Add Vendor
- Set the amount, frequency, due date, and priority

**When a payment is delayed or skipped:**
- Go to Contracts > Payment Overrides > Add New Override
- Move the payment to a new date, or skip it entirely
- This adjusts projections without changing the recurring schedule

**When planning a big decision:**
- Go to Scenarios > Build Scenario
- Model the change (e.g. "Hire 5 employees starting June")
- Click "Run Scenario" to see the impact on your cash position
- Save it and compare with other scenarios on the Compare tab

**Monthly: Review Settings**
- Check if the realistic delay still reflects actual collection times
- Adjust alert thresholds if your cash position has changed significantly
""")
