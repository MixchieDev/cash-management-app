"""
Scenarios Page - Scenario Builder and Analysis
Create and run what-if scenarios.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
import plotly.graph_objects as go

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth
from utils.currency_formatter import format_currency

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Scenarios - JESUS Company",
    page_icon="📊",
    layout="wide"
)

require_auth()

st.title("📊 Scenario Modeling")

# Permission check
if st.session_state.get('user_role') != 'admin':
    st.warning("⚠️ You don't have permission to create scenarios. Contact your administrator.")
    st.info("You can view existing scenarios in read-only mode on the Scenario Comparison page.")
    st.stop()

# Initialize session state for scenario
if 'current_scenario' not in st.session_state:
    st.session_state.current_scenario = {
        'name': '',
        'entity': 'YAHSHUA',
        'changes': []
    }

# Entity selector for scenario
scenario_entity = st.selectbox(
    "Apply scenario to entity",
    ["YAHSHUA", "ABBA", "Both"],
    key="scenario_entity"
)

st.session_state.current_scenario['entity'] = scenario_entity

# ═══════════════════════════════════════════════════════════════════
# SCENARIO BUILDER TABS
# ═══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["👥 Hiring", "💸 Expenses", "💰 Revenue", "📉 Customer Loss"])

with tab1:
    st.markdown("### Add Hiring Scenario")
    st.info("Model the impact of hiring new employees")

    col1, col2 = st.columns(2)

    with col1:
        num_employees = st.number_input(
            "Number of Employees",
            min_value=1,
            max_value=100,
            value=10,
            key="hire_num"
        )

        salary_per_employee = st.number_input(
            "Salary per Employee (₱/month)",
            min_value=20000,
            max_value=500000,
            value=50000,
            step=5000,
            key="hire_salary"
        )

    with col2:
        hire_start_date = st.date_input(
            "Start Date",
            min_value=date.today(),
            value=date.today().replace(month=date.today().month + 1 if date.today().month < 12 else 1),
            key="hire_date"
        )

        # Show impact preview
        total_monthly_cost = num_employees * salary_per_employee
        st.metric("Total Monthly Payroll Impact", format_currency(total_monthly_cost))

    if st.button("➕ Add Hiring to Scenario", key="add_hiring"):
        change = {
            'type': 'hiring',
            'employees': num_employees,
            'salary_per_employee': salary_per_employee,
            'start_date': hire_start_date.isoformat(),
            'description': f"Hire {num_employees} employees at {format_currency(salary_per_employee)}/month"
        }
        st.session_state.current_scenario['changes'].append(change)
        st.success(f"✅ Added: {change['description']}")
        st.rerun()

with tab2:
    st.markdown("### Add Expense Scenario")
    st.info("Model the impact of new recurring expenses")

    col1, col2 = st.columns(2)

    with col1:
        expense_name = st.text_input(
            "Expense Name",
            placeholder="e.g., CyTech CTO Service",
            key="expense_name"
        )

        expense_amount = st.number_input(
            "Monthly Amount (₱)",
            min_value=10000,
            max_value=10000000,
            value=489000,
            step=10000,
            key="expense_amount"
        )

    with col2:
        expense_category = st.selectbox(
            "Category",
            ["Software/Tech", "Operations", "Rent", "Utilities", "Subscriptions", "Other"],
            key="expense_category"
        )

        expense_start_date = st.date_input(
            "Start Date",
            min_value=date.today(),
            key="expense_date"
        )

    if st.button("➕ Add Expense to Scenario", key="add_expense"):
        if not expense_name:
            st.error("Please enter an expense name")
        else:
            change = {
                'type': 'expense',
                'name': expense_name,
                'amount_per_month': expense_amount,
                'start_date': expense_start_date.isoformat(),
                'category': expense_category,
                'description': f"Add {expense_name}: {format_currency(expense_amount)}/month"
            }
            st.session_state.current_scenario['changes'].append(change)
            st.success(f"✅ Added: {change['description']}")
            st.rerun()

with tab3:
    st.markdown("### Add Revenue Scenario")
    st.info("Model the impact of winning new clients")

    col1, col2 = st.columns(2)

    with col1:
        num_clients = st.number_input(
            "Number of New Clients",
            min_value=1,
            max_value=50,
            value=5,
            key="rev_clients"
        )

        revenue_per_client = st.number_input(
            "Revenue per Client (₱/month)",
            min_value=10000,
            max_value=1000000,
            value=100000,
            step=10000,
            key="rev_amount"
        )

    with col2:
        revenue_start_date = st.date_input(
            "Start Date",
            min_value=date.today(),
            key="rev_date"
        )

        # Show impact preview
        total_new_revenue = num_clients * revenue_per_client
        st.metric("Total New Monthly Revenue", format_currency(total_new_revenue))

    if st.button("➕ Add Revenue to Scenario", key="add_revenue"):
        change = {
            'type': 'revenue',
            'new_clients': num_clients,
            'revenue_per_client': revenue_per_client,
            'start_date': revenue_start_date.isoformat(),
            'description': f"Win {num_clients} clients at {format_currency(revenue_per_client)}/month"
        }
        st.session_state.current_scenario['changes'].append(change)
        st.success(f"✅ Added: {change['description']}")
        st.rerun()

with tab4:
    st.markdown("### Add Customer Loss Scenario")
    st.info("Model the impact of losing a customer")

    col1, col2 = st.columns(2)

    with col1:
        loss_customer = st.text_input(
            "Customer Name",
            placeholder="e.g., ABC Corp",
            key="loss_customer"
        )

        loss_revenue = st.number_input(
            "Monthly Revenue Lost (₱)",
            min_value=10000,
            max_value=5000000,
            value=300000,
            step=10000,
            key="loss_amount"
        )

    with col2:
        loss_date = st.date_input(
            "Loss Date",
            min_value=date.today(),
            key="loss_date"
        )

    if st.button("➕ Add Customer Loss to Scenario", key="add_loss"):
        if not loss_customer:
            st.error("Please enter a customer name")
        else:
            change = {
                'type': 'customer_loss',
                'customer_name': loss_customer,
                'revenue_lost': loss_revenue,
                'loss_date': loss_date.isoformat(),
                'description': f"Lose {loss_customer}: -{format_currency(loss_revenue)}/month"
            }
            st.session_state.current_scenario['changes'].append(change)
            st.success(f"✅ Added: {change['description']}")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════
# CURRENT SCENARIO DISPLAY
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Current Scenario")

if st.session_state.current_scenario['changes']:
    scenario_name = st.text_input(
        "Scenario Name",
        value=st.session_state.current_scenario.get('name', ''),
        placeholder="e.g., Aggressive Growth 2026",
        key="scenario_name_input"
    )
    st.session_state.current_scenario['name'] = scenario_name

    st.markdown(f"**Entity:** {st.session_state.current_scenario['entity']}")

    # Display changes
    for i, change in enumerate(st.session_state.current_scenario['changes']):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"{i+1}. {change['description']}")
        with col2:
            if st.button("❌", key=f"remove_{i}"):
                st.session_state.current_scenario['changes'].pop(i)
                st.rerun()

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("▶️ Run Scenario", type="primary", use_container_width=True):
            st.info("Scenario calculation will be implemented with backend integration")

    with col2:
        if st.button("💾 Save Scenario", use_container_width=True):
            if not st.session_state.current_scenario['name']:
                st.error("Please enter a scenario name before saving")
            else:
                st.success(f"✅ Scenario '{st.session_state.current_scenario['name']}' saved!")
                st.info("Note: Scenario storage will be fully implemented in backend integration")

    with col3:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.current_scenario = {'name': '', 'entity': 'YAHSHUA', 'changes': []}
            st.rerun()

else:
    st.info("👆 Use the tabs above to add changes to your scenario")

# ═══════════════════════════════════════════════════════════════════
# NOTES FOR CFO
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### How Scenario Modeling Works")

st.markdown("""
**What is a Scenario?**

A scenario is a "what-if" analysis that shows how your cash position would change if you:
- Hire new employees
- Add new recurring expenses
- Win new clients
- Lose existing clients

**How to Use:**

1. **Build Your Scenario**: Use the tabs above to add one or more changes
2. **Name It**: Give your scenario a descriptive name (e.g., "Hire 10 Engineers")
3. **Run It**: Click "Run Scenario" to see the impact on your cash flow
4. **Save It**: Click "Save Scenario" to keep it for future comparison

**Example Scenarios:**

- "Can we afford to hire 10 employees at ₱50K/month?"
- "What happens if we lose our biggest client?"
- "Impact of partnering with CyTech (₱489K/month expense)"

**Next Steps:**

After creating scenarios, go to the **Scenario Comparison** page to compare multiple scenarios side-by-side.
""")
