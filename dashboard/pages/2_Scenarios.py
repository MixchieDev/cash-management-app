"""
Scenarios Page - Build, Compare, and Strategic Planning
Consolidated scenario management: create what-if scenarios, compare them, and plan growth.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta, datetime
from decimal import Decimal
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Optional
from copy import deepcopy

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth, require_permission, check_permission
from utils.currency_formatter import format_currency
from database.queries import get_all_scenarios, get_scenario_by_id, get_total_mrr
from projection_engine.cash_projector import CashProjector, ProjectionDataPoint
from scenario_engine.scenario_calculator import ScenarioCalculator
from scenario_engine.scenario_storage import ScenarioStorage
from dashboard.components.styling import load_css, page_header
from dashboard.theme import COLORS, get_chart_layout, CHART_COLORS

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Scenarios - JESUS Company",
    page_icon="📊",
    layout="wide"
)

load_css()
require_auth()
require_permission('view_scenarios')

can_edit_scenarios = check_permission('edit_scenarios')

page_header("Scenario Modeling", "Build, compare, and plan strategic scenarios")

with st.expander("How Scenarios Work"):
    st.markdown("""
- Scenarios model **changes on top of the current baseline** projection (your actual contracts and balances)
- **Build Scenario** — add changes like hiring new employees, new expenses, revenue increases, or losing a customer, then click "Run Scenario" to see the impact
- **Compare Scenarios** — select up to 3 saved scenarios to view side-by-side on a chart with key metrics
- **Strategic Planning** — use calculators to answer growth questions:
    - How many employees can we afford to hire?
    - What revenue do we need to reach ₱250M?
    - What are our growth milestones?

**How changes work:**
| Type | What it does to projections |
|------|---------------------------|
| **Hiring** | Adds monthly payroll cost (avg ₱40K-60K per employee) starting from a date |
| **New Expense** | Adds a recurring or one-time cost |
| **Revenue Change** | Increases or decreases monthly revenue by a fixed amount |
| **Customer Loss** | Removes a specific customer's revenue from projections |
""")

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def generate_baseline_projection(entity: str, scenario_type: str = 'realistic') -> List[ProjectionDataPoint]:
    """Generate 12-month monthly baseline projection for entity."""
    projector = CashProjector()
    return projector.calculate_cash_projection(
        entity=entity,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        timeframe='monthly',
        scenario_type=scenario_type
    )


def calculate_runway_months(projection: List[ProjectionDataPoint]) -> int:
    """Calculate cash runway in months."""
    for i, point in enumerate(projection):
        if point.ending_cash < Decimal('0'):
            return i
    return len(projection)


def get_projection_metric(projection: List[ProjectionDataPoint], month_index: int) -> Decimal:
    """Get ending cash for specific month."""
    if 0 <= month_index < len(projection):
        return projection[month_index].ending_cash
    return Decimal('0')


def find_first_negative_date(projection: List[ProjectionDataPoint]) -> Optional[date]:
    """Find first date where cash goes negative."""
    for point in projection:
        if point.ending_cash < Decimal('0'):
            return point.date
    return None


def get_scenario_expense_summary(scenario_id: int) -> str:
    """Get formatted summary of monthly expenses for a scenario."""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario or not scenario.get('changes'):
        return "No expenses"

    recurring = []
    one_time = []

    for change in scenario['changes']:
        change_type = change.get('change_type')
        if change_type == 'hiring':
            employees = change.get('employees', 0)
            salary = change.get('salary_per_employee', Decimal('0'))
            if employees and salary:
                amount = Decimal(str(employees)) * Decimal(str(salary))
                recurring.append(f"Hire {employees} employees: {format_currency(amount)}/mo")
        elif change_type == 'expense':
            expense_name = change.get('expense_name', 'Expense')
            expense_amount = change.get('expense_amount')
            if expense_amount:
                recurring.append(f"{expense_name}: {format_currency(expense_amount)}/mo")
        elif change_type == 'investment':
            investment_amount = change.get('investment_amount')
            if investment_amount:
                investment_name = change.get('notes', 'Investment')
                one_time.append(f"{investment_name}: {format_currency(investment_amount)}")

    if not recurring and not one_time:
        return "No expenses"

    lines = []
    if recurring:
        lines.append("Recurring:")
        for item in recurring:
            lines.append(f"  • {item}")
    if one_time:
        if lines:
            lines.append("")
        lines.append("One-time:")
        for item in one_time:
            lines.append(f"  • {item}")

    return "\n".join(lines)


def get_scenario_revenue_summary(scenario_id: int) -> str:
    """Get formatted summary of monthly revenue changes for a scenario."""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario or not scenario.get('changes'):
        return "No revenue changes"

    additions = []
    reductions = []

    for change in scenario['changes']:
        change_type = change.get('change_type')
        if change_type == 'revenue':
            new_clients = change.get('new_clients', 0)
            revenue_per_client = change.get('revenue_per_client')
            if new_clients and revenue_per_client:
                amount = Decimal(str(new_clients)) * Decimal(str(revenue_per_client))
                additions.append(f"Add {new_clients} clients: {format_currency(amount)}/mo")
        elif change_type == 'customer_loss':
            lost_revenue = change.get('lost_revenue')
            if lost_revenue:
                reductions.append(f"Customer churn: -{format_currency(lost_revenue)}/mo")

    if not additions and not reductions:
        return "No revenue changes"

    lines = []
    if additions:
        lines.append("Revenue Additions:")
        for item in additions:
            lines.append(f"  • {item}")
    if reductions:
        if lines:
            lines.append("")
        lines.append("Revenue Reductions:")
        for item in reductions:
            lines.append(f"  ⚠️ {item}")

    return "\n".join(lines)


def build_comparison_chart(
    baseline: List[ProjectionDataPoint],
    combined_projection: List[ProjectionDataPoint],
    entity: str,
    combined_name: str
) -> go.Figure:
    """Build Plotly comparison chart showing Baseline vs Combined scenarios."""
    fig = go.Figure()

    baseline_dates = [p.date for p in baseline]
    baseline_cash = [float(p.ending_cash) for p in baseline]

    fig.add_trace(go.Scatter(
        x=baseline_dates,
        y=baseline_cash,
        mode='lines+markers',
        name='Baseline (No Changes)',
        line=dict(color='#808080', width=3, dash='dash'),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>Cash: ₱%{y:,.2f}<extra></extra>'
    ))

    combined_dates = [p.date for p in combined_projection]
    combined_cash = [float(p.ending_cash) for p in combined_projection]

    fig.add_trace(go.Scatter(
        x=combined_dates,
        y=combined_cash,
        mode='lines+markers',
        name=combined_name,
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>Cash: ₱%{y:,.2f}<extra></extra>'
    ))

    fig.add_hrect(
        y0=-10000000, y1=0,
        fillcolor="red", opacity=0.1,
        line_width=0,
        annotation_text="Negative Cash Zone",
        annotation_position="top left"
    )

    fig.add_hrect(
        y0=0, y1=500000,
        fillcolor="orange", opacity=0.1,
        line_width=0
    )

    layout = get_chart_layout(height=500)
    layout.update({
        'title': f"Scenario Comparison - {entity}",
        'xaxis_title': "Month",
        'yaxis_title': "Cash Position (₱)",
        'hovermode': 'x unified',
        'yaxis': {
            **layout.get('yaxis', {}),
            'tickformat': ',.0f',
            'tickprefix': '₱',
        },
        'legend': dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    })
    fig.update_layout(**layout)

    return fig


def build_metrics_dataframe(
    baseline: List[ProjectionDataPoint],
    combined_projection: List[ProjectionDataPoint],
    combined_name: str
) -> pd.DataFrame:
    """Build metrics comparison table as DataFrame."""
    metrics = {
        'Metric': [
            'Month 3 Cash',
            'Month 6 Cash',
            'Month 12 Cash',
            'Cash Runway (months)',
            'First Negative Date'
        ]
    }

    metrics['Baseline (No Changes)'] = [
        format_currency(get_projection_metric(baseline, 2)),
        format_currency(get_projection_metric(baseline, 5)),
        format_currency(get_projection_metric(baseline, 11)),
        f"{calculate_runway_months(baseline)} months" if calculate_runway_months(baseline) < len(baseline) else "Never goes negative",
        find_first_negative_date(baseline).strftime('%Y-%m-%d') if find_first_negative_date(baseline) else "Never"
    ]

    metrics[combined_name] = [
        format_currency(get_projection_metric(combined_projection, 2)),
        format_currency(get_projection_metric(combined_projection, 5)),
        format_currency(get_projection_metric(combined_projection, 11)),
        f"{calculate_runway_months(combined_projection)} months" if calculate_runway_months(combined_projection) < len(combined_projection) else "Never goes negative",
        find_first_negative_date(combined_projection).strftime('%Y-%m-%d') if find_first_negative_date(combined_projection) else "Never"
    ]

    return pd.DataFrame(metrics)


# ═══════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════
main_tab1, main_tab2, main_tab3 = st.tabs([
    "Build Scenario",
    "Compare Scenarios",
    "Strategic Planning"
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1: BUILD SCENARIO
# ═══════════════════════════════════════════════════════════════════
with main_tab1:
    # Permission check
    if st.session_state.get('user_role') != 'admin':
        st.warning("You don't have permission to create scenarios. Contact your administrator.")
        st.info("You can view existing scenarios in the Compare tab.")
    else:
        # Initialize session state for scenario
        if 'current_scenario' not in st.session_state:
            st.session_state.current_scenario = {
                'name': '',
                'entity': 'YAHSHUA',
                'changes': []
            }

        scenario_entity = st.selectbox(
            "Apply scenario to entity",
            ["YAHSHUA", "ABBA", "Both"],
            key="scenario_entity"
        )
        st.session_state.current_scenario['entity'] = scenario_entity

        # Scenario builder sub-tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Hiring", "Expenses", "Revenue", "Customer Loss"])

        with tab1:
            st.markdown("### Add Hiring Scenario")
            st.info("Model the impact of hiring new employees")

            col1, col2 = st.columns(2)

            with col1:
                num_employees = st.number_input(
                    "Number of Employees",
                    min_value=1, max_value=100, value=10,
                    key="hire_num"
                )
                salary_per_employee = st.number_input(
                    "Salary per Employee (₱/month)",
                    min_value=20000, max_value=500000, value=50000, step=5000,
                    key="hire_salary"
                )

            with col2:
                hire_start_date = st.date_input(
                    "Start Date",
                    min_value=date.today(),
                    value=date.today().replace(month=date.today().month + 1 if date.today().month < 12 else 1),
                    key="hire_date"
                )
                total_monthly_cost = num_employees * salary_per_employee
                st.metric("Total Monthly Payroll Impact", format_currency(total_monthly_cost))

            if st.button("Add Hiring to Scenario", key="add_hiring"):
                change = {
                    'type': 'hiring',
                    'employees': num_employees,
                    'salary_per_employee': salary_per_employee,
                    'start_date': hire_start_date.isoformat(),
                    'description': f"Hire {num_employees} employees at {format_currency(salary_per_employee)}/month"
                }
                st.session_state.current_scenario['changes'].append(change)
                st.success(f"Added: {change['description']}")
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
                    min_value=10000, max_value=10000000, value=489000, step=10000,
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

            if st.button("Add Expense to Scenario", key="add_expense"):
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
                    st.success(f"Added: {change['description']}")
                    st.rerun()

        with tab3:
            st.markdown("### Add Revenue Scenario")
            st.info("Model the impact of winning new clients")

            col1, col2 = st.columns(2)

            with col1:
                num_clients = st.number_input(
                    "Number of New Clients",
                    min_value=1, max_value=50, value=5,
                    key="rev_clients"
                )
                revenue_per_client = st.number_input(
                    "Revenue per Client (₱/month)",
                    min_value=10000, max_value=1000000, value=100000, step=10000,
                    key="rev_amount"
                )

            with col2:
                revenue_start_date = st.date_input(
                    "Start Date",
                    min_value=date.today(),
                    key="rev_date"
                )
                total_new_revenue = num_clients * revenue_per_client
                st.metric("Total New Monthly Revenue", format_currency(total_new_revenue))

            if st.button("Add Revenue to Scenario", key="add_revenue"):
                change = {
                    'type': 'revenue',
                    'new_clients': num_clients,
                    'revenue_per_client': revenue_per_client,
                    'start_date': revenue_start_date.isoformat(),
                    'description': f"Win {num_clients} clients at {format_currency(revenue_per_client)}/month"
                }
                st.session_state.current_scenario['changes'].append(change)
                st.success(f"Added: {change['description']}")
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
                    min_value=10000, max_value=5000000, value=300000, step=10000,
                    key="loss_amount"
                )

            with col2:
                loss_date = st.date_input(
                    "Loss Date",
                    min_value=date.today(),
                    key="loss_date"
                )

            if st.button("Add Customer Loss to Scenario", key="add_loss"):
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
                    st.success(f"Added: {change['description']}")
                    st.rerun()

        # ═══════════════════════════════════════════════════════════
        # CURRENT SCENARIO DISPLAY
        # ═══════════════════════════════════════════════════════════
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

            for i, change in enumerate(st.session_state.current_scenario['changes']):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"{i+1}. {change['description']}")
                with col2:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state.current_scenario['changes'].pop(i)
                        st.rerun()

            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Run Scenario", type="primary", width='stretch'):
                    # Generate baseline and apply scenario changes inline
                    with st.spinner("Running scenario..."):
                        try:
                            entity = st.session_state.current_scenario['entity']
                            if entity == 'Both':
                                entity = 'YAHSHUA'

                            baseline = generate_baseline_projection(entity, 'realistic')
                            scenario_projection = deepcopy(baseline)

                            # Apply changes directly without saving
                            for change in st.session_state.current_scenario['changes']:
                                for point in scenario_projection:
                                    start_dt = date.fromisoformat(change.get('start_date') or change.get('loss_date'))
                                    if point.date >= start_dt:
                                        if change['type'] == 'hiring':
                                            point.outflows += Decimal(str(change['employees'] * change['salary_per_employee']))
                                        elif change['type'] == 'expense':
                                            point.outflows += Decimal(str(change['amount_per_month']))
                                        elif change['type'] == 'revenue':
                                            point.inflows += Decimal(str(change['new_clients'] * change['revenue_per_client']))
                                        elif change['type'] == 'customer_loss':
                                            point.inflows -= Decimal(str(change['revenue_lost']))
                                            if point.inflows < 0:
                                                point.inflows = Decimal('0')

                            # Recalculate ending cash
                            for i, point in enumerate(scenario_projection):
                                if i == 0:
                                    point.ending_cash = point.starting_cash + point.inflows - point.outflows
                                else:
                                    point.starting_cash = scenario_projection[i - 1].ending_cash
                                    point.ending_cash = point.starting_cash + point.inflows - point.outflows
                                point.is_negative = point.ending_cash < 0

                            scenario_name_display = st.session_state.current_scenario.get('name') or "Current Scenario"
                            fig = build_comparison_chart(baseline, scenario_projection, entity, scenario_name_display)
                            st.plotly_chart(fig, width='stretch')

                            metrics_df = build_metrics_dataframe(baseline, scenario_projection, scenario_name_display)
                            st.dataframe(metrics_df, width='stretch', hide_index=True)

                        except Exception as e:
                            st.error(f"Error running scenario: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())

            with col2:
                if st.button("Save Scenario", width='stretch'):
                    if not st.session_state.current_scenario['name']:
                        st.error("Please enter a scenario name before saving")
                    else:
                        try:
                            entity = st.session_state.current_scenario['entity']
                            if entity == 'Both':
                                entity = 'YAHSHUA'

                            scenario_id = ScenarioStorage.create_scenario(
                                scenario_name=st.session_state.current_scenario['name'],
                                entity=entity,
                                description="Created via Scenario Builder",
                                created_by=st.session_state.get('username', 'Unknown')
                            )

                            for change in st.session_state.current_scenario['changes']:
                                change_type = change['type']
                                start_date_str = change.get('start_date') or change.get('loss_date')
                                start_date_val = datetime.fromisoformat(start_date_str).date() if start_date_str else date.today()

                                if change_type == 'hiring':
                                    ScenarioStorage.add_scenario_change(
                                        scenario_id=scenario_id,
                                        change_type='hiring',
                                        start_date=start_date_val,
                                        employees=change.get('employees'),
                                        salary_per_employee=change.get('salary_per_employee')
                                    )
                                elif change_type == 'expense':
                                    ScenarioStorage.add_scenario_change(
                                        scenario_id=scenario_id,
                                        change_type='expense',
                                        start_date=start_date_val,
                                        expense_name=change.get('name'),
                                        expense_amount=change.get('amount_per_month')
                                    )
                                elif change_type == 'revenue':
                                    ScenarioStorage.add_scenario_change(
                                        scenario_id=scenario_id,
                                        change_type='revenue',
                                        start_date=start_date_val,
                                        new_clients=change.get('new_clients'),
                                        revenue_per_client=change.get('revenue_per_client')
                                    )
                                elif change_type == 'customer_loss':
                                    ScenarioStorage.add_scenario_change(
                                        scenario_id=scenario_id,
                                        change_type='customer_loss',
                                        start_date=start_date_val,
                                        lost_revenue=change.get('revenue_lost'),
                                        notes=change.get('customer_name')
                                    )

                            st.success(f"Scenario '{st.session_state.current_scenario['name']}' saved!")
                            st.session_state.current_scenario = {'name': '', 'entity': 'YAHSHUA', 'changes': []}
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error saving scenario: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())

            with col3:
                if st.button("Clear All", width='stretch'):
                    st.session_state.current_scenario = {'name': '', 'entity': 'YAHSHUA', 'changes': []}
                    st.rerun()

        else:
            st.info("Use the tabs above to add changes to your scenario")

# ═══════════════════════════════════════════════════════════════════
# TAB 2: COMPARE SCENARIOS
# ═══════════════════════════════════════════════════════════════════
with main_tab2:
    st.markdown(f'''
    <div style="
        background: {COLORS['info_light']};
        border-left: 4px solid {COLORS['info']};
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        font-size: 14px;
        color: {COLORS['text_primary']};
        margin: 16px 0;
    ">
        <strong>Compare Multiple Scenarios</strong><br>
        Select 1-3 saved scenarios to see their combined impact on cash flow.
        When multiple scenarios are selected, all changes are stacked together to show the cumulative effect.
    </div>
    ''', unsafe_allow_html=True)

    try:
        scenarios = get_all_scenarios()

        if scenarios:
            scenario_data = []
            for s in scenarios:
                scenario_data.append({
                    'ID': s['id'],
                    'Name': s['scenario_name'],
                    'Entity': s['entity'],
                    'Changes': s['num_changes'],
                    'Monthly Expenses': get_scenario_expense_summary(s['id']),
                    'Monthly Revenue': get_scenario_revenue_summary(s['id']),
                    'Created By': s['created_by'] or 'Unknown',
                    'Created': s['created_at'].strftime('%Y-%m-%d') if s['created_at'] else 'N/A'
                })

            df_scenarios = pd.DataFrame(scenario_data)
            st.dataframe(
                df_scenarios,
                width='stretch',
                hide_index=True,
                column_config={
                    "Monthly Expenses": st.column_config.TextColumn(
                        "Monthly Expenses", width="large",
                        help="Breakdown of recurring and one-time expenses"
                    ),
                    "Monthly Revenue": st.column_config.TextColumn(
                        "Monthly Revenue", width="large",
                        help="Revenue additions and reductions"
                    )
                }
            )

            st.markdown("### Select Scenarios to Compare")

            selected_scenarios = st.multiselect(
                "Choose 1-3 scenarios (changes will be combined/stacked together)",
                options=[s['scenario_name'] for s in scenarios],
                max_selections=3,
                key="compare_scenarios_select"
            )

            if len(selected_scenarios) >= 1:
                st.success(f"Selected {len(selected_scenarios)} scenarios for comparison")

                if st.button("Compare Scenarios", type="primary", key="compare_btn"):
                    with st.spinner("Calculating scenario comparisons..."):
                        try:
                            name_to_id = {s['scenario_name']: s['id'] for s in scenarios}
                            name_to_entity = {s['scenario_name']: s['entity'] for s in scenarios}

                            selected_entities = [name_to_entity[name] for name in selected_scenarios]
                            if len(set(selected_entities)) > 1:
                                st.error("All scenarios must be for the same entity")
                                st.info(f"Selected entities: {', '.join(set(selected_entities))}")
                                st.stop()

                            entity = selected_entities[0]
                            baseline = generate_baseline_projection(entity, 'realistic')

                            calculator = ScenarioCalculator()
                            selected_scenario_ids = [name_to_id[name] for name in selected_scenarios]

                            combined_projection = calculator.apply_multiple_scenarios_to_projection(
                                baseline, selected_scenario_ids
                            )

                            if len(selected_scenarios) == 1:
                                combined_name = selected_scenarios[0]
                            else:
                                combined_name = f"Combined: {', '.join(selected_scenarios)}"

                            st.markdown("---")
                            st.markdown("## Comparison Results")
                            st.info(f"**Comparing:** Baseline vs {combined_name}")

                            fig = build_comparison_chart(baseline, combined_projection, entity, combined_name)
                            st.plotly_chart(fig, width='stretch')

                            st.markdown("### Key Metrics Comparison")
                            metrics_df = build_metrics_dataframe(baseline, combined_projection, combined_name)
                            st.dataframe(metrics_df, width='stretch', hide_index=True)

                            with st.expander("How to Interpret Results"):
                                st.markdown("""
                                **Reading the Chart:**
                                - **Baseline (No Changes)** - Gray dashed line: Current trajectory with no scenario changes
                                - **Combined Scenario** - Blue solid line: Projected cash flow with ALL selected scenarios applied
                                - **Red zone**: Negative cash (cannot pay obligations)
                                - **Orange zone**: Low cash warning (below ₱500,000)

                                **How Scenarios Combine:**
                                When you select multiple scenarios, all changes are **stacked/combined**:
                                - Example: "Hire 5 employees" + "New Office" + "Add 10 Clients"
                                - Result: Shows cumulative effect of ALL THREE changes together

                                **Making Decisions:**
                                - Compare combined scenario against baseline to see total impact
                                - If cash goes negative, consider which changes to delay or scale back
                                - Use this to answer: "Can we afford ALL these changes together?"
                                """)

                        except Exception as e:
                            st.error(f"Error comparing scenarios: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
            else:
                st.info("Select at least 1 scenario to compare against baseline")

        else:
            st.warning("No saved scenarios found. Create scenarios in the Build Scenario tab first.")

    except Exception as e:
        st.error(f"Error loading scenarios: {str(e)}")

# ═══════════════════════════════════════════════════════════════════
# TAB 3: STRATEGIC PLANNING
# ═══════════════════════════════════════════════════════════════════
with main_tab3:
    # ── Path to ₱250M ──
    st.markdown("## Path to ₱250M Revenue")

    try:
        current_mrr = get_total_mrr()
        current_arr = current_mrr * 12
    except Exception:
        current_arr = Decimal('50000000')

    target_arr = Decimal('250000000')
    progress_pct = float(current_arr / target_arr * 100)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Annual Revenue", format_currency(current_arr))
    with col2:
        st.metric("Target Revenue", format_currency(target_arr))
    with col3:
        remaining = target_arr - current_arr
        st.metric("Remaining Gap", format_currency(remaining))

    st.progress(min(progress_pct / 100, 1.0))
    st.caption(f"Progress: {progress_pct:.1f}%")

    # ── Hiring Affordability Calculator ──
    st.markdown("---")
    st.markdown("## Hiring Affordability Calculator")
    st.info("Calculate whether you can afford to hire new employees with current revenue")

    col1, col2 = st.columns(2)
    with col1:
        hire_num = st.number_input(
            "Number of Employees to Hire",
            min_value=1, max_value=100, value=10,
            key="strategic_hire_num"
        )
        hire_salary = st.number_input(
            "Average Salary per Employee (₱/month)",
            min_value=20000, max_value=500000, value=50000, step=5000,
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

    monthly_cost = hire_num * hire_salary
    annual_cost = monthly_cost * 12

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Monthly Payroll Impact", format_currency(monthly_cost))
    with col2:
        st.metric("Annual Cost", format_currency(annual_cost))
    with col3:
        if current_arr > annual_cost * 3:
            st.success("Likely Affordable")
        elif current_arr > annual_cost * 2:
            st.warning("Review Carefully")
        else:
            st.error("May Not Be Affordable")

    if st.button("Run Hiring Scenario", type="primary", key="run_hiring_scenario"):
        with st.spinner("Calculating hiring impact..."):
            try:
                entity_for_calc = hire_entity if hire_entity != 'Both' else 'YAHSHUA'
                baseline = generate_baseline_projection(entity_for_calc, 'realistic')
                scenario_projection = deepcopy(baseline)

                additional_payroll = Decimal(str(monthly_cost))
                for point in scenario_projection:
                    if point.date >= hire_start:
                        point.outflows += additional_payroll

                for i, point in enumerate(scenario_projection):
                    if i == 0:
                        point.ending_cash = point.starting_cash + point.inflows - point.outflows
                    else:
                        point.starting_cash = scenario_projection[i - 1].ending_cash
                        point.ending_cash = point.starting_cash + point.inflows - point.outflows
                    point.is_negative = point.ending_cash < 0

                fig = build_comparison_chart(
                    baseline, scenario_projection, entity_for_calc,
                    f"Hire {hire_num} at {format_currency(hire_salary)}/mo"
                )
                st.plotly_chart(fig, width='stretch')

                metrics_df = build_metrics_dataframe(
                    baseline, scenario_projection,
                    f"Hire {hire_num}"
                )
                st.dataframe(metrics_df, width='stretch', hide_index=True)

            except Exception as e:
                st.error(f"Error calculating hiring impact: {str(e)}")

    # ── Revenue Target Calculator ──
    st.markdown("---")
    st.markdown("## Revenue Target Calculator")
    st.info("Calculate what's needed to reach a specific revenue target")

    col1, col2 = st.columns(2)
    with col1:
        target_amount = st.number_input(
            "Target Annual Revenue (₱)",
            min_value=50000000, max_value=500000000, value=100000000, step=10000000,
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
                    st.metric("Monthly MRR Growth Needed", format_currency(monthly_growth_needed))
        else:
            st.warning("Target date must be in the future")

    # ── Growth Milestones ──
    st.markdown("---")
    st.markdown("## Growth Milestones")

    milestones = [
        {"revenue": Decimal('50000000'), "label": "₱50M (Current)"},
        {"revenue": Decimal('75000000'), "label": "₱75M"},
        {"revenue": Decimal('100000000'), "label": "₱100M"},
        {"revenue": Decimal('150000000'), "label": "₱150M"},
        {"revenue": Decimal('200000000'), "label": "₱200M"},
        {"revenue": Decimal('250000000'), "label": "₱250M (Target)"},
    ]

    for milestone in milestones:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"**{milestone['label']}**")
        with col2:
            if current_arr >= milestone['revenue']:
                st.markdown("Achieved")
            else:
                gap = milestone['revenue'] - current_arr
                st.markdown(f"Gap: {format_currency(gap)}")
        with col3:
            progress = min(float(current_arr / milestone['revenue'] * 100), 100)
            st.progress(progress / 100)
