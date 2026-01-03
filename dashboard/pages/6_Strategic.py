"""
Strategic Planning Page
Path to ₱250M, hiring affordability, and growth planning.
"""
import streamlit as st
import sys
from pathlib import Path
from decimal import Decimal
from datetime import date

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth
from utils.currency_formatter import format_currency
from database.queries import get_total_mrr

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Strategic Planning - JESUS Company",
    page_icon="🎯",
    layout="wide"
)

require_auth()

st.title("🎯 Strategic Planning")

# ═══════════════════════════════════════════════════════════════════
# PATH TO ₱250M
# ═══════════════════════════════════════════════════════════════════
st.markdown("## 📈 Path to ₱250M Revenue")

# Get current revenue
try:
    current_mrr = get_total_mrr()
    current_arr = current_mrr * 12
except:
    current_arr = Decimal('50000000')  # Default assumption

target_arr = Decimal('250000000')

# Progress
progress_pct = float(current_arr / target_arr * 100)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Current Annual Revenue", format_currency(current_arr))

with col2:
    st.metric("Target Revenue", format_currency(target_arr))

with col3:
    remaining = target_arr - current_arr
    st.metric("Remaining Gap", format_currency(remaining))

# Progress bar
st.progress(min(progress_pct / 100, 1.0))
st.caption(f"Progress: {progress_pct:.1f}%")

# ═══════════════════════════════════════════════════════════════════
# HIRING AFFORDABILITY CALCULATOR
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 👥 Hiring Affordability Calculator")

st.info("Calculate whether you can afford to hire new employees with current revenue")

col1, col2 = st.columns(2)

with col1:
    hire_num = st.number_input(
        "Number of Employees to Hire",
        min_value=1,
        max_value=100,
        value=10,
        key="strategic_hire_num"
    )

    hire_salary = st.number_input(
        "Average Salary per Employee (₱/month)",
        min_value=20000,
        max_value=500000,
        value=50000,
        step=5000,
        key="strategic_hire_salary"
    )

with col2:
    hire_entity = st.selectbox(
        "Entity",
        ["YAHSHUA", "ABBA", "Both"],
        key="strategic_hire_entity"
    )

    hire_start = st.date_input(
        "Proposed Start Date",
        min_value=date.today(),
        key="strategic_hire_start"
    )

# Calculate impact
monthly_cost = hire_num * hire_salary
annual_cost = monthly_cost * 12

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Monthly Payroll Impact", format_currency(monthly_cost))

with col2:
    st.metric("Annual Cost", format_currency(annual_cost))

with col3:
    # Simple affordability check
    if current_arr > annual_cost * 3:
        st.success("✅ Likely Affordable")
    elif current_arr > annual_cost * 2:
        st.warning("⚠️ Review Carefully")
    else:
        st.error("❌ May Not Be Affordable")

if st.button("Calculate Hiring Affordability", type="primary"):
    st.info("Full affordability calculation with cash flow impact will be available after backend integration")

# ═══════════════════════════════════════════════════════════════════
# REVENUE TARGET CALCULATOR
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 💰 Revenue Target Calculator")

st.info("Calculate what's needed to reach a specific revenue target")

col1, col2 = st.columns(2)

with col1:
    target_amount = st.number_input(
        "Target Annual Revenue (₱)",
        min_value=50000000,
        max_value=500000000,
        value=100000000,
        step=10000000,
        key="target_revenue"
    )

with col2:
    target_date = st.date_input(
        "Target Date",
        min_value=date.today(),
        value=date(2026, 12, 31),
        key="target_date"
    )

if st.button("Calculate Requirements", type="primary", key="calc_target"):
    st.info("Revenue target calculation will be implemented with backend integration")

    # Simple estimates
    additional_revenue_needed = Decimal(str(target_amount)) - current_arr
    months_to_target = ((target_date.year - date.today().year) * 12 +
                       (target_date.month - date.today().month))

    if months_to_target > 0:
        monthly_growth_needed = additional_revenue_needed / 12 / months_to_target

        st.markdown("### Estimated Requirements")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Additional Revenue Needed", format_currency(additional_revenue_needed))

        with col2:
            st.metric("Time to Target", f"{months_to_target} months")

        with col3:
            if monthly_growth_needed > 0:
                monthly_mrr_growth = monthly_growth_needed
                st.metric("Monthly MRR Growth Needed", format_currency(monthly_mrr_growth))

# ═══════════════════════════════════════════════════════════════════
# GROWTH MILESTONES
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🎯 Growth Milestones")

milestones = [
    {"revenue": Decimal('50000000'), "label": "₱50M (Current)", "status": "✅ Achieved"},
    {"revenue": Decimal('75000000'), "label": "₱75M", "status": "🎯 Next Target"},
    {"revenue": Decimal('100000000'), "label": "₱100M", "status": "📍 Milestone"},
    {"revenue": Decimal('150000000'), "label": "₱150M", "status": "📍 Milestone"},
    {"revenue": Decimal('200000000'), "label": "₱200M", "status": "📍 Milestone"},
    {"revenue": Decimal('250000000'), "label": "₱250M (Target)", "status": "🏁 Goal"},
]

for milestone in milestones:
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown(f"**{milestone['label']}**")

    with col2:
        if current_arr >= milestone['revenue']:
            st.markdown(f"{milestone['status']}")
        else:
            gap = milestone['revenue'] - current_arr
            st.markdown(f"Gap: {format_currency(gap)}")

    with col3:
        progress = min(float(current_arr / milestone['revenue'] * 100), 100)
        st.progress(progress / 100)

# ═══════════════════════════════════════════════════════════════════
# STRATEGIC NOTES
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Strategic Planning Tools")

st.markdown("""
**How to Use These Tools:**

1. **Path to ₱250M** - Track overall progress toward revenue goal
2. **Hiring Affordability** - Determine if you can afford new hires
3. **Revenue Target** - Calculate what's needed to hit specific goals

**Key Questions to Answer:**

- How many employees can we hire this quarter?
- What revenue growth rate do we need?
- When can we afford a ₱10M investment?
- What's our runway if we hire 20 people?

**Next Steps:**

- Create scenarios on the Scenarios page to test specific plans
- Use Scenario Comparison to evaluate multiple options
- Review Settings page to adjust payroll and expense assumptions

*Full strategic planning tools with detailed calculations coming soon.*
""")
