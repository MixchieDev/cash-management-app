"""
Payment Overrides Page - Manage one-off payment date adjustments.
Allows moving or skipping individual customer/vendor payments.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth
from database.queries import (
    get_payment_overrides,
    create_payment_override,
    delete_payment_override,
    get_customers,
    get_vendors,
    get_customer_by_id,
    get_vendor_by_id
)
from projection_engine.revenue_calculator import RevenueCalculator
from projection_engine.expense_scheduler import ExpenseScheduler
from utils.currency_formatter import format_currency
from dashboard.components.styling import load_css, page_header, entity_badge, empty_state
from dashboard.theme import COLORS

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Payment Overrides - JESUS Company",
    page_icon="📅",
    layout="wide"
)

load_css()
require_auth()

page_header("Payment Overrides", "Adjust individual payment dates without changing the recurring schedule")

# ═══════════════════════════════════════════════════════════════════
# FILTERS
# ═══════════════════════════════════════════════════════════════════
col1, col2 = st.columns(2)

with col1:
    entity_filter = st.selectbox(
        "Entity",
        ["All", "YAHSHUA", "ABBA"],
        key="override_entity_filter"
    )

with col2:
    type_filter = st.selectbox(
        "Type",
        ["All", "Customer", "Vendor"],
        key="override_type_filter"
    )

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════
# ADD NEW OVERRIDE
# ═══════════════════════════════════════════════════════════════════
with st.expander("➕ Add New Override", expanded=False):
    st.markdown("### Create Payment Override")

    # Override type selection
    override_type = st.radio(
        "Payment Type",
        ["Customer", "Vendor"],
        horizontal=True,
        key="new_override_type"
    )

    # Entity selection for the override
    override_entity = st.selectbox(
        "Entity",
        ["YAHSHUA", "ABBA"],
        key="new_override_entity"
    )

    if override_type == "Customer":
        # Get customers for selected entity
        customers = get_customers(entity=override_entity, status='Active')

        if not customers:
            st.warning(f"No active customers found for {override_entity}")
        else:
            # Customer selection
            customer_options = {c['id']: c['company_name'] for c in customers}
            selected_customer_id = st.selectbox(
                "Customer",
                options=list(customer_options.keys()),
                format_func=lambda x: customer_options[x],
                key="new_override_customer"
            )

            # Get upcoming payment dates for this customer
            if selected_customer_id:
                customer = get_customer_by_id(selected_customer_id)
                if customer:
                    # Calculate upcoming payment dates
                    # Use optimistic (no delay) to show base contractual payment dates
                    revenue_calc = RevenueCalculator(scenario_type='optimistic')

                    # Create a mock contract object for calculation
                    class MockContract:
                        pass

                    mock = MockContract()
                    mock.id = customer['id']
                    mock.company_name = customer['company_name']
                    mock.monthly_fee = customer['monthly_fee']
                    mock.payment_plan = customer['payment_plan']
                    mock.contract_start = customer['contract_start']
                    mock.contract_end = customer['contract_end']
                    mock.status = customer['status']
                    mock.entity = customer['entity']
                    mock.payment_terms_days = customer['payment_terms_days']

                    # Calculate payments for next 12 months
                    today = date.today()
                    end_calc = today + timedelta(days=365)

                    events = revenue_calc.calculate_revenue_events(
                        [mock], today, end_calc
                    )

                    payment_dates = [e.date for e in events if e.customer_id == selected_customer_id]

                    if payment_dates:
                        selected_payment_date = st.selectbox(
                            "Payment Date to Override",
                            options=payment_dates,
                            format_func=lambda x: x.strftime('%B %d, %Y'),
                            key="new_override_payment_date"
                        )
                    else:
                        st.info("No upcoming payments found for this customer")
                        selected_payment_date = None
                else:
                    selected_payment_date = None

    else:  # Vendor
        # Get vendors for selected entity
        vendors = get_vendors(entity=override_entity, status='Active')

        if not vendors:
            st.warning(f"No active vendors found for {override_entity}")
        else:
            # Vendor selection
            vendor_options = {v['id']: f"{v['vendor_name']} ({v['category']})" for v in vendors}
            selected_vendor_id = st.selectbox(
                "Vendor",
                options=list(vendor_options.keys()),
                format_func=lambda x: vendor_options[x],
                key="new_override_vendor"
            )

            # Get upcoming payment dates for this vendor
            if selected_vendor_id:
                vendor = get_vendor_by_id(selected_vendor_id)
                if vendor:
                    # Calculate upcoming payment dates
                    expense_scheduler = ExpenseScheduler()

                    # Create a mock contract object
                    class MockVendor:
                        pass

                    mock = MockVendor()
                    mock.id = vendor['id']
                    mock.vendor_name = vendor['vendor_name']
                    mock.amount = vendor['amount']
                    mock.frequency = vendor['frequency']
                    mock.due_date = vendor['due_date']
                    mock.start_date = vendor['start_date']
                    mock.end_date = vendor['end_date']
                    mock.entity = vendor['entity']
                    mock.category = vendor['category']
                    mock.priority = vendor['priority']
                    mock.status = vendor['status']

                    # Calculate payments for next 12 months
                    today = date.today()
                    end_calc = today + timedelta(days=365)

                    payment_dates = expense_scheduler.get_vendor_payment_dates(
                        mock, today, end_calc
                    )

                    if payment_dates:
                        selected_payment_date = st.selectbox(
                            "Payment Date to Override",
                            options=payment_dates,
                            format_func=lambda x: x.strftime('%B %d, %Y'),
                            key="new_override_vendor_date"
                        )
                    else:
                        st.info("No upcoming payments found for this vendor")
                        selected_payment_date = None
                else:
                    selected_payment_date = None

    # Only show action options if we have a payment date
    if 'selected_payment_date' in dir() and selected_payment_date:
        st.markdown("---")

        # Action selection
        action = st.radio(
            "Action",
            ["Move to New Date", "Skip Payment"],
            horizontal=True,
            key="new_override_action"
        )

        if action == "Move to New Date":
            new_date = st.date_input(
                "New Payment Date",
                value=selected_payment_date + timedelta(days=7),
                min_value=date.today(),
                key="new_override_new_date"
            )
        else:
            new_date = None

        # Reason
        reason = st.text_area(
            "Reason (optional)",
            placeholder="e.g., Client requested delay, Billing dispute, etc.",
            key="new_override_reason"
        )

        # Create button
        if st.button("Create Override", type="primary", key="create_override_btn"):
            try:
                contract_id = selected_customer_id if override_type == "Customer" else selected_vendor_id
                action_value = "move" if action == "Move to New Date" else "skip"

                result = create_payment_override(
                    override_type=override_type.lower(),
                    contract_id=contract_id,
                    original_date=selected_payment_date,
                    action=action_value,
                    entity=override_entity,
                    new_date=new_date,
                    reason=reason if reason else None
                )

                st.success(f"Override created successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Error creating override: {str(e)}")

# ═══════════════════════════════════════════════════════════════════
# ACTIVE OVERRIDES LIST
# ═══════════════════════════════════════════════════════════════════
st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
st.markdown("### Active Overrides")

# Build query filters
query_entity = None if entity_filter == "All" else entity_filter
query_type = None if type_filter == "All" else type_filter.lower()

# Only show future overrides by default
overrides = get_payment_overrides(
    override_type=query_type,
    entity=query_entity,
    start_date=date.today() - timedelta(days=30)  # Show recent past too
)

if not overrides:
    empty_state(
        "No payment overrides yet",
        "Click 'Add New Override' above to adjust a payment date",
        "📅"
    )
else:
    # Display overrides with styled cards
    for override in overrides:
        # Get contract details
        if override['override_type'] == 'customer':
            contract = get_customer_by_id(override['contract_id'])
            contract_name = contract['company_name'] if contract else f"Customer #{override['contract_id']}"
            icon = "👤"
        else:
            contract = get_vendor_by_id(override['contract_id'])
            contract_name = contract['vendor_name'] if contract else f"Vendor #{override['contract_id']}"
            icon = "🏢"

        # Entity badge styling
        entity_bg = COLORS['yahshua_light'] if override['entity'] == 'YAHSHUA' else COLORS['abba_light']
        entity_color = '#2563EB' if override['entity'] == 'YAHSHUA' else '#7C3AED'

        # Date display
        if override['action'] == 'move':
            date_html = f'''
                <span style="color: {COLORS['text_secondary']};">
                    {override['original_date'].strftime('%b %d, %Y')}
                </span>
                <span style="color: {COLORS['text_muted']}; padding: 0 8px;">→</span>
                <span style="color: {COLORS['text_primary']}; font-weight: 500;">
                    {override['new_date'].strftime('%b %d, %Y')}
                </span>
            '''
        else:
            date_html = f'''
                <span style="color: {COLORS['danger']}; text-decoration: line-through;">
                    {override['original_date'].strftime('%b %d, %Y')}
                </span>
                <span style="color: {COLORS['danger']}; font-weight: 500; margin-left: 8px;">
                    SKIPPED
                </span>
            '''

        # Reason display
        reason_html = f'''
            <span style="color: {COLORS['text_muted']}; font-style: italic;">
                {override['reason'] if override['reason'] else 'No reason provided'}
            </span>
        '''

        # Render styled card
        col1, col2, col3 = st.columns([4, 3, 1])

        with col1:
            st.markdown(f'''
                <div style="margin-bottom: 4px;">
                    <span style="font-size: 14px; font-weight: 500; color: {COLORS['text_primary']};">
                        {icon} {contract_name}
                    </span>
                    <span style="
                        background: {entity_bg};
                        color: {entity_color};
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: 500;
                        margin-left: 8px;
                    ">{override['entity']}</span>
                </div>
                <div style="font-size: 14px; margin-top: 4px;">
                    📅 {date_html}
                </div>
            ''', unsafe_allow_html=True)

        with col2:
            st.markdown(f'''
                <div style="font-size: 14px; padding-top: 8px;">
                    {reason_html}
                </div>
            ''', unsafe_allow_html=True)

        with col3:
            if st.button("Delete", key=f"delete_{override['id']}", type="secondary"):
                if delete_payment_override(override['id']):
                    st.success("Override deleted")
                    st.rerun()
                else:
                    st.error("Failed to delete override")

        # Divider between items
        st.markdown(f'''
            <div style="border-bottom: 1px solid {COLORS['border']}; margin: 16px 0;"></div>
        ''', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# HELP TEXT
# ═══════════════════════════════════════════════════════════════════
with st.expander("ℹ️ How Payment Overrides Work"):
    st.markdown("""
    **Payment overrides** allow you to adjust individual payment dates without changing the recurring schedule.

    ### Actions

    - **Move to New Date**: Reschedules a specific payment to a different date
    - **Skip Payment**: Excludes a payment from the cash flow projection entirely

    ### Examples

    1. **Delayed Customer Payment**
       - ACME Corp usually pays on the 15th
       - This month they requested a delay
       - Create override: Move Jan 15 → Jan 25

    2. **Billing Dispute**
       - AWS payment is disputed this month
       - Create override: Skip Feb 21 payment
       - (Once resolved, delete the override)

    ### Notes

    - Overrides only affect the specific date selected
    - The recurring schedule remains unchanged
    - Overrides are automatically reflected in cash flow projections
    - Delete an override to restore the original payment date
    """)
