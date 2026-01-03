"""
Home Page - Main Dashboard
Shows cash position, KPIs, projections, and alerts.
"""
import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
from datetime import date, timedelta
from decimal import Decimal

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth
from config.constants import PAYMENT_PLAN_FREQUENCIES
from projection_engine.cash_projector import CashProjector, ProjectionResult
from database.queries import get_latest_bank_balance, get_consolidated_bank_balance, get_total_mrr, get_total_monthly_expenses
from utils.currency_formatter import format_currency
from dashboard.components.transaction_modal import show_transaction_breakdown_modal
from utils.period_helpers import calculate_period_range

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Home - JESUS Company",
    page_icon="₱",
    layout="wide"
)

require_auth()

st.title("₱ JESUS Company - Strategic Cash Management")

# ═══════════════════════════════════════════════════════════════════
# HEADER CONTROLS
# ═══════════════════════════════════════════════════════════════════
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    entity = st.selectbox(
        "Entity",
        ["YAHSHUA", "ABBA", "Consolidated"],
        key="entity_selector",
        help="Select entity to view projections"
    )

with col2:
    scenario_type = st.radio(
        "Projection Scenario",
        ["Optimistic", "Realistic"],
        horizontal=True,
        key="scenario_type",
        help="Optimistic: On-time payments | Realistic: 10-day delay"
    )

with col3:
    st.markdown(f"**{st.session_state.get('name', 'User')}**")
    st.caption(f"@{st.session_state.get('username', 'user')}")

# ═══════════════════════════════════════════════════════════════════
# GET BANK BALANCE
# ═══════════════════════════════════════════════════════════════════
try:
    if entity == 'Consolidated':
        bank_data = get_consolidated_bank_balance()
        current_cash = bank_data['amount']
        balance_date = bank_data['date']
    else:
        bank_data = get_latest_bank_balance(entity)
        current_cash = bank_data['amount']
        balance_date = bank_data['date']
except Exception as e:
    st.error(f"Unable to load bank balance: {str(e)}")
    st.info("Please ensure you have synced data from Google Sheets. Go to Contracts page and click 'Sync from Google Sheets'.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════
# INITIALIZE SESSION STATE FOR MODAL
# ═══════════════════════════════════════════════════════════════════
if 'show_transaction_modal' not in st.session_state:
    st.session_state.show_transaction_modal = False
if 'modal_period_data' not in st.session_state:
    st.session_state.modal_period_data = None
if 'projection_result' not in st.session_state:
    st.session_state.projection_result = None

# ═══════════════════════════════════════════════════════════════════
# GENERATE PROJECTION
# ═══════════════════════════════════════════════════════════════════
try:
    projector = CashProjector()
    # Use detailed projection to get both aggregated data AND events
    projection_result_90d = projector.calculate_cash_projection_detailed(
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90),
        entity=entity,
        timeframe='daily',
        scenario_type=scenario_type.lower()
    )
    projection = projection_result_90d.data_points
except Exception as e:
    st.error(f"Error calculating projection: {str(e)}")
    projection = []
    projection_result_90d = None

# Extract key metrics
if projection:
    day_30_cash = next((p.ending_cash for p in projection if (p.date - date.today()).days >= 30), current_cash)
    day_60_cash = next((p.ending_cash for p in projection if (p.date - date.today()).days >= 60), current_cash)
    day_90_cash = next((p.ending_cash for p in projection if (p.date - date.today()).days >= 90), current_cash)
else:
    day_30_cash = day_60_cash = day_90_cash = current_cash

# Calculate cash runway
monthly_burn = get_total_monthly_expenses(entity)
if monthly_burn > 0:
    cash_runway_months = int(current_cash / monthly_burn)
else:
    cash_runway_months = 99

# ═══════════════════════════════════════════════════════════════════
# KPI CARDS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric(
        "Current Cash (Actual)",
        format_currency(current_cash),
        help=f"Bank balance as of {balance_date}"
    )
    st.caption(f"as of {balance_date}")

with col2:
    delta_30 = day_30_cash - current_cash
    st.metric(
        "30-Day Projection",
        format_currency(day_30_cash),
        delta=format_currency(delta_30),
        delta_color="normal" if delta_30 >= 0 else "inverse"
    )

with col3:
    delta_60 = day_60_cash - current_cash
    st.metric(
        "60-Day Projection",
        format_currency(day_60_cash),
        delta=format_currency(delta_60),
        delta_color="normal" if delta_60 >= 0 else "inverse"
    )

with col5:
    delta_90 = day_90_cash - current_cash
    st.metric(
        "90-Day Projection",
        format_currency(day_90_cash),
        delta=format_currency(delta_90),
        delta_color="normal" if delta_90 >= 0 else "inverse"
    )

with col6:
    runway_color = "green" if cash_runway_months > 12 else "orange" if cash_runway_months > 6 else "red"
    st.metric(
        "Cash Runway",
        f"{cash_runway_months} months",
        help="Months until cash reaches ₱0 at current burn rate"
    )

# ═══════════════════════════════════════════════════════════════════
# ALERTS SECTION
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")

# Check for alerts
alerts = []

# Cash crunch alert
for p in projection[:30]:  # Check next 30 days
    if p.ending_cash < Decimal('0'):
        alerts.append({
            'type': 'danger',
            'icon': '🚨',
            'title': 'Cash Crunch Warning',
            'message': f"Projected negative cash on {p.date}: {format_currency(p.ending_cash)}"
        })
        break

# Low cash warning
if not alerts:  # Only show if no cash crunch
    for p in projection[:30]:
        if Decimal('0') <= p.ending_cash < Decimal('500000'):
            alerts.append({
                'type': 'warning',
                'icon': '⚠️',
                'title': 'Low Cash Warning',
                'message': f"Cash projected below ₱500,000 on {p.date}: {format_currency(p.ending_cash)}"
            })
            break

if alerts:
    with st.expander(f"🔔 ALERTS ({len(alerts)})", expanded=True):
        for alert in alerts:
            if alert['type'] == 'danger':
                st.error(f"{alert['icon']} **{alert['title']}**: {alert['message']}")
            else:
                st.warning(f"{alert['icon']} **{alert['title']}**: {alert['message']}")
else:
    st.success("✅ No alerts - cash position healthy")

# ═══════════════════════════════════════════════════════════════════
# MAIN PROJECTION CHART
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## Cash Flow Projection")

# Timeline selector
timeframe = st.radio(
    "Timeline",
    ["Daily (90d)", "Weekly (6mo)", "Monthly (12mo)", "Quarterly (3yr)"],
    horizontal=True,
    key="timeframe_selector"
)

# Map selection to parameters
timeframe_map = {
    "Daily (90d)": ('daily', 90),
    "Weekly (6mo)": ('weekly', 180),
    "Monthly (12mo)": ('monthly', 365),
    "Quarterly (3yr)": ('quarterly', 1095)
}

tf_key, tf_days = timeframe_map[timeframe]

# Get projection for selected timeframe
try:
    projection_result = projector.calculate_cash_projection_detailed(
        start_date=date.today(),
        end_date=date.today() + timedelta(days=tf_days),
        entity=entity,
        timeframe=tf_key,
        scenario_type=scenario_type.lower()
    )
    projection_data = projection_result.data_points

    # Store in session state for modal access
    st.session_state.projection_result = projection_result
    st.session_state.projection_start_date = date.today()
    st.session_state.current_timeframe = tf_key

except Exception as e:
    st.error(f"Error generating {timeframe} projection: {str(e)}")
    projection_data = []
    projection_result = None

if projection_data:
    # Build chart
    dates = [p.date for p in projection_data]
    cash_amounts = [float(p.ending_cash) for p in projection_data]

    fig = go.Figure()

    # Cash position line
    fig.add_trace(go.Scatter(
        x=dates,
        y=cash_amounts,
        mode='lines+markers',
        name='Cash Position',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>Cash: ₱%{y:,.2f}<extra></extra>'
    ))

    # Add red zone for negative cash
    fig.add_hrect(
        y0=-10000000, y1=0,
        fillcolor="red", opacity=0.1,
        line_width=0,
        annotation_text="Negative Cash Zone",
        annotation_position="top left"
    )

    # Add warning zone
    fig.add_hrect(
        y0=0, y1=500000,
        fillcolor="orange", opacity=0.1,
        line_width=0
    )

    fig.update_layout(
        title=f"Cash Flow Projection - {entity} ({scenario_type})",
        xaxis_title="Date",
        yaxis_title="Cash Position (₱)",
        hovermode='x unified',
        height=500,
        yaxis=dict(tickformat=',.0f', tickprefix='₱'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Render chart with click event handling
    selected = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        key="cash_flow_chart"
    )

    # Handle chart clicks
    if selected and selected.selection and selected.selection.points:
        clicked_point = selected.selection.points[0]
        clicked_date = dates[clicked_point['point_index']]

        # Calculate period range based on timeframe
        period_start, period_end, period_label = calculate_period_range(
            clicked_date,
            st.session_state.current_timeframe,
            st.session_state.projection_start_date
        )

        # Get events for this period
        revenue_events, expense_events = projection_result.get_events_for_period(
            period_start, period_end
        )

        # Store modal data in session state
        st.session_state.modal_period_data = {
            'period_label': period_label,
            'period_start': period_start,
            'period_end': period_end,
            'revenue_events': revenue_events,
            'expense_events': expense_events,
            'entity': entity
        }
        st.session_state.show_transaction_modal = True
        st.rerun()

    # Show info about clicking
    st.info("💡 Click on any point on the chart to see detailed transaction breakdown")

else:
    st.warning("No projection data available")

# ═══════════════════════════════════════════════════════════════════
# TRANSACTION MODAL
# ═══════════════════════════════════════════════════════════════════
# Display transaction modal if active
if st.session_state.show_transaction_modal and st.session_state.modal_period_data:
    modal_data = st.session_state.modal_period_data
    show_transaction_breakdown_modal(
        period_label=modal_data['period_label'],
        period_start=modal_data['period_start'],
        period_end=modal_data['period_end'],
        revenue_events=modal_data['revenue_events'],
        expense_events=modal_data['expense_events'],
        entity=modal_data['entity']
    )

# ═══════════════════════════════════════════════════════════════════
# SYNC BUTTON
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    if 'last_sync' in st.session_state:
        st.caption(f"Last synced: {st.session_state.last_sync}")
    else:
        st.caption("Data not yet synced")

with col2:
    if st.button("↻ Sync from Google Sheets", type="primary"):
        with st.spinner("Syncing data from Google Sheets..."):
            try:
                from data_processing.google_sheets_import import sync_all_data
                from datetime import datetime

                result = sync_all_data()
                st.session_state.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.success(f"✅ Synced: {result.get('customers', 0)} customers, {result.get('vendors', 0)} vendors")
                st.rerun()
            except Exception as e:
                st.error(f"Sync failed: {str(e)}")

# ═══════════════════════════════════════════════════════════════════
# REVENUE & EXPENSE BREAKDOWNS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Revenue Summary")

    try:
        total_mrr = get_total_mrr(entity)
        st.metric("Total MRR", format_currency(total_mrr))
        st.metric("Annual Run Rate", format_currency(total_mrr * 12))
    except Exception as e:
        st.warning("Unable to calculate revenue metrics")

with col2:
    st.markdown("### Expense Summary")

    try:
        monthly_expenses = get_total_monthly_expenses(entity)
        st.metric("Total Monthly Expenses", format_currency(monthly_expenses))
        st.caption("Based on all active vendor contracts (including payroll)")
    except Exception as e:
        st.warning("Unable to calculate expense metrics")

# ═══════════════════════════════════════════════════════════════════
# QUICK ACTIONS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("➕ Create Scenario", use_container_width=True):
        st.switch_page("pages/2_Scenarios.py")

with col2:
    if st.button("📊 Compare Scenarios", use_container_width=True):
        st.switch_page("pages/3_Scenario_Comparison.py")

with col3:
    if st.button("📄 View Contracts", use_container_width=True):
        st.switch_page("pages/4_Contracts.py")

with col4:
    if st.button("🎯 Strategic Planning", use_container_width=True):
        st.switch_page("pages/6_Strategic.py")
