"""
Contracts Page - Customer and Vendor Contract Management
Shows all contracts with Google Sheets links for editing.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from decimal import Decimal

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth
from config.settings import SPREADSHEET_ID
from config.constants import PAYMENT_PLAN_FREQUENCIES
from database.queries import get_customers, get_vendors
from utils.currency_formatter import format_currency

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Contracts - JESUS Company",
    page_icon="📄",
    layout="wide"
)

require_auth()

st.title("📄 Contract Management")

# ═══════════════════════════════════════════════════════════════════
# DATA MANAGEMENT INFO (PHASE 1)
# ═══════════════════════════════════════════════════════════════════
st.info("""
📋 **Data Management (Phase 1)**

Contract data is managed in Google Sheets. Use the buttons below to edit data,
then sync to update the dashboard.

*Direct editing in dashboard coming in Phase 2 (Week 3)*
""")

# Google Sheets links
sheets_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"

col1, col2, col3 = st.columns(3)

with col1:
    st.link_button(
        "📝 Edit Customer Contracts",
        f"{sheets_url}#gid=0",
        use_container_width=True,
        help="Opens Google Sheets to edit customer contracts"
    )

with col2:
    st.link_button(
        "📝 Edit Vendor Contracts",
        f"{sheets_url}#gid=1",
        use_container_width=True,
        help="Opens Google Sheets to edit vendor contracts"
    )

with col3:
    st.link_button(
        "📝 Update Bank Balances",
        f"{sheets_url}#gid=2",
        use_container_width=True,
        help="Opens Google Sheets to update bank balances"
    )

# Sync button
st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    if 'last_sync' in st.session_state:
        st.caption(f"Last synced: {st.session_state.last_sync}")
    else:
        st.caption("Data not yet synced")

with col2:
    if st.button("↻ Sync from Google Sheets", type="primary", use_container_width=True):
        with st.spinner("Syncing data from Google Sheets..."):
            try:
                from data_processing.google_sheets_import import sync_all_data
                from datetime import datetime

                result = sync_all_data()
                st.session_state.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.success(f"""
✅ Sync complete!
- Customers: {result.get('customers', 0)} records
- Vendors: {result.get('vendors', 0)} records
- Bank Balances: {result.get('bank_balances', 0)} records
                """)
                st.rerun()
            except Exception as e:
                st.error(f"Sync failed: {str(e)}")
                st.info("Please check your Google Sheets credentials and spreadsheet ID in config/google_sheets_config.py")

# ═══════════════════════════════════════════════════════════════════
# ENTITY FILTER
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")

entity_filter = st.selectbox(
    "Filter by Entity",
    ["All", "YAHSHUA", "ABBA"],
    key="contract_entity_filter"
)

# ═══════════════════════════════════════════════════════════════════
# CUSTOMER CONTRACTS
# ═══════════════════════════════════════════════════════════════════
st.markdown("## Customer Contracts")

try:
    # Get customers from database
    customers = get_customers(entity=entity_filter if entity_filter != "All" else None, status='Active')

    if customers:
        # Build display data with payment amount calculation
        customer_data = []
        for c in customers:
            multiplier = PAYMENT_PLAN_FREQUENCIES.get(c['payment_plan'], 1)
            payment_amount = c['monthly_fee'] * multiplier

            customer_data.append({
                'Customer': c['company_name'],
                'Monthly Fee': format_currency(c['monthly_fee']),
                'Payment Plan': c['payment_plan'],
                'Payment Amount': format_currency(payment_amount),
                'Entity': c['entity'],
                'Status': c['status'],
                'Start Date': c['contract_start'].strftime('%Y-%m-%d') if c['contract_start'] else 'N/A',
                'End Date': c['contract_end'].strftime('%Y-%m-%d') if c['contract_end'] else 'Ongoing'
            })

        df_customers = pd.DataFrame(customer_data)

        st.dataframe(
            df_customers,
            use_container_width=True,
            hide_index=True
        )

        # Summary metrics
        total_mrr = sum(c['monthly_fee'] for c in customers)
        total_arr = total_mrr * 12
        active_count = len(customers)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total MRR", format_currency(total_mrr))
        with col2:
            st.metric("Annual Run Rate", format_currency(total_arr))
        with col3:
            st.metric("Active Contracts", active_count)

        # Payment plan breakdown
        st.markdown("### Payment Plan Breakdown")
        plan_counts = {}
        for c in customers:
            plan = c['payment_plan']
            plan_counts[plan] = plan_counts.get(plan, 0) + 1

        col1, col2, col3, col4, col5 = st.columns(5)
        cols = [col1, col2, col3, col4, col5]

        for i, (plan, count) in enumerate(sorted(plan_counts.items())):
            if i < 5:
                with cols[i]:
                    st.metric(plan, count)

    else:
        st.warning("No customer contracts found. Click 'Sync from Google Sheets' to import data.")

except Exception as e:
    st.error(f"Error loading customer contracts: {str(e)}")
    st.info("If you haven't synced data yet, click the 'Sync from Google Sheets' button above.")

# ═══════════════════════════════════════════════════════════════════
# VENDOR CONTRACTS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## Vendor Contracts")

try:
    # Get vendors from database
    vendors = get_vendors(entity=entity_filter if entity_filter != "All" else None, status='Active')

    if vendors:
        # Build display data
        vendor_data = []
        for v in vendors:
            vendor_data.append({
                'Vendor': v['vendor_name'],
                'Category': v['category'],
                'Amount': format_currency(v['amount']),
                'Frequency': v['frequency'],
                'Due Date': v['due_date'].strftime('%b %d') if v['due_date'] else 'N/A',
                'Start Date': v['start_date'].strftime('%Y-%m-%d') if v.get('start_date') else 'Active',
                'End Date': v['end_date'].strftime('%Y-%m-%d') if v.get('end_date') else 'Ongoing',
                'Entity': v['entity'],
                'Priority': v['priority']
            })

        df_vendors = pd.DataFrame(vendor_data)

        st.dataframe(
            df_vendors,
            use_container_width=True,
            hide_index=True
        )

        # Summary by category
        st.markdown("### Expenses by Category")

        category_totals = {}
        for v in vendors:
            amount = v['amount']
            category = v['category']
            category_totals[category] = category_totals.get(category, Decimal('0')) + amount

        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]

        for i, (category, total) in enumerate(sorted(category_totals.items(), key=lambda x: x[1], reverse=True)):
            if i < 4:
                with cols[i]:
                    st.metric(category, format_currency(total))

        # Show additional categories if more than 4
        if len(category_totals) > 4:
            st.markdown("### Additional Categories")
            remaining = list(sorted(category_totals.items(), key=lambda x: x[1], reverse=True))[4:]
            for category, total in remaining:
                st.caption(f"**{category}**: {format_currency(total)}")

    else:
        st.warning("No vendor contracts found. Click 'Sync from Google Sheets' to import data.")

except Exception as e:
    st.error(f"Error loading vendor contracts: {str(e)}")
    st.info("If you haven't synced data yet, click the 'Sync from Google Sheets' button above.")

# ═══════════════════════════════════════════════════════════════════
# EXPLANATION NOTES
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Understanding Payment Amounts")

st.markdown("""
**For Customers:**
- **Monthly Fee** = The recurring monthly value of the contract
- **Payment Plan** = How often payment is collected
- **Payment Amount** = Monthly Fee × Payment Plan Multiplier

Examples:
- ₱100,000 Monthly Fee + Quarterly plan = ₱300,000 per quarter (₱100K × 3)
- ₱200,000 Monthly Fee + Annual plan = ₱2,400,000 per year (₱200K × 12)

**For Vendors (Entity "Both"):**
- Full Amount = Total cost of vendor
- Split by configured ratio (see Settings page)
- Default: 50% YAHSHUA, 50% ABBA
- Consolidated view shows 100% (no double-counting)
""")

# ═══════════════════════════════════════════════════════════════════
# PHASE 2 PLACEHOLDER
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Coming in Phase 2 (Week 3)")
st.markdown("""
- ➕ Add new contracts directly in dashboard
- ✏️ Edit existing contracts
- 🗑️ Deactivate contracts
- 📊 Contract analytics and trends
- 📈 Revenue forecasting by customer
""")
