"""
Scenario Comparison Page
Compare multiple saved scenarios side-by-side.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth
from database.queries import get_all_scenarios, get_scenario_by_id
from projection_engine.cash_projector import CashProjector, ProjectionDataPoint
from scenario_engine.scenario_calculator import ScenarioCalculator
from utils.currency_formatter import format_currency
from dashboard.components.styling import load_css, page_header
from dashboard.theme import COLORS, get_chart_layout, CHART_COLORS

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def generate_baseline_projection(entity: str, scenario_type: str = 'realistic') -> List[ProjectionDataPoint]:
    """
    Generate 12-month monthly baseline projection for entity.

    Args:
        entity: Entity name ('YAHSHUA', 'ABBA', or 'Consolidated')
        scenario_type: 'optimistic' or 'realistic' (default)

    Returns:
        List of ProjectionDataPoint objects for 12 months
    """
    projector = CashProjector()
    start_date = date.today()
    end_date = start_date + timedelta(days=365)

    projection = projector.calculate_cash_projection(
        entity=entity,
        start_date=start_date,
        end_date=end_date,
        timeframe='monthly',
        scenario_type=scenario_type
    )

    return projection


def calculate_runway_months(projection: List[ProjectionDataPoint]) -> int:
    """
    Calculate cash runway in months.

    Args:
        projection: List of ProjectionDataPoint objects

    Returns:
        Number of months until cash goes negative, or full period if never negative
    """
    for i, point in enumerate(projection):
        if point.ending_cash < Decimal('0'):
            return i
    return len(projection)


def get_projection_metric(projection: List[ProjectionDataPoint], month_index: int) -> Decimal:
    """
    Get ending cash for specific month.

    Args:
        projection: List of ProjectionDataPoint objects
        month_index: 0-indexed month number (0 = first month, 2 = month 3, etc.)

    Returns:
        Ending cash for that month, or Decimal('0') if out of bounds
    """
    if 0 <= month_index < len(projection):
        return projection[month_index].ending_cash
    return Decimal('0')


def find_first_negative_date(projection: List[ProjectionDataPoint]) -> Optional[date]:
    """
    Find first date where cash goes negative.

    Args:
        projection: List of ProjectionDataPoint objects

    Returns:
        Date of first negative cash, or None if never negative
    """
    for point in projection:
        if point.ending_cash < Decimal('0'):
            return point.date
    return None


def get_scenario_expense_summary(scenario_id: int) -> str:
    """
    Get formatted summary of monthly expenses for a scenario.

    Args:
        scenario_id: Scenario ID

    Returns:
        Formatted string showing recurring and one-time expenses, or "No expenses"
    """
    scenario = get_scenario_by_id(scenario_id)

    if not scenario or not scenario.get('changes'):
        return "No expenses"

    recurring = []
    one_time = []

    for change in scenario['changes']:
        change_type = change.get('change_type')

        if change_type == 'hiring':
            # Hiring: employees × salary = monthly payroll expense
            employees = change.get('employees', 0)
            salary = change.get('salary_per_employee', Decimal('0'))
            if employees and salary:
                amount = Decimal(str(employees)) * Decimal(str(salary))
                recurring.append(f"Hire {employees} employees: {format_currency(amount)}/mo")

        elif change_type == 'expense':
            # Recurring expense: monthly amount
            expense_name = change.get('expense_name', 'Expense')
            expense_amount = change.get('expense_amount')
            if expense_amount:
                recurring.append(f"{expense_name}: {format_currency(expense_amount)}/mo")

        elif change_type == 'investment':
            # One-time investment
            investment_amount = change.get('investment_amount')
            if investment_amount:
                # Try to get investment name from notes or use default
                investment_name = change.get('notes', 'Investment')
                one_time.append(f"{investment_name}: {format_currency(investment_amount)}")

    # Build output string
    if not recurring and not one_time:
        return "No expenses"

    lines = []

    if recurring:
        lines.append("Recurring:")
        for item in recurring:
            lines.append(f"  • {item}")

    if one_time:
        if lines:  # Add spacing if there are recurring expenses
            lines.append("")
        lines.append("One-time:")
        for item in one_time:
            lines.append(f"  • {item}")

    return "\n".join(lines)


def get_scenario_revenue_summary(scenario_id: int) -> str:
    """
    Get formatted summary of monthly revenue changes for a scenario.

    Args:
        scenario_id: Scenario ID

    Returns:
        Formatted string showing revenue additions and reductions, or "No revenue changes"
    """
    scenario = get_scenario_by_id(scenario_id)

    if not scenario or not scenario.get('changes'):
        return "No revenue changes"

    additions = []
    reductions = []

    for change in scenario['changes']:
        change_type = change.get('change_type')

        if change_type == 'revenue':
            # Revenue addition: new clients
            new_clients = change.get('new_clients', 0)
            revenue_per_client = change.get('revenue_per_client')
            if new_clients and revenue_per_client:
                amount = Decimal(str(new_clients)) * Decimal(str(revenue_per_client))
                additions.append(f"Add {new_clients} clients: {format_currency(amount)}/mo")

        elif change_type == 'customer_loss':
            # Revenue reduction: customer churn
            lost_revenue = change.get('lost_revenue')
            if lost_revenue:
                reductions.append(f"Customer churn: -{format_currency(lost_revenue)}/mo")

    # Build output string
    if not additions and not reductions:
        return "No revenue changes"

    lines = []

    if additions:
        lines.append("Revenue Additions:")
        for item in additions:
            lines.append(f"  • {item}")

    if reductions:
        if lines:  # Add spacing
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
    """
    Build Plotly comparison chart showing Baseline vs Combined scenarios.

    Args:
        baseline: Baseline projection (no scenario changes)
        combined_projection: Combined projection with all scenarios applied
        entity: Entity name for chart title
        combined_name: Name for combined scenario

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Add baseline trace (gray, dashed)
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

    # Add combined scenario trace (blue, solid)
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
        title=f"Scenario Comparison - {entity}",
        xaxis_title="Month",
        yaxis_title="Cash Position (₱)",
        hovermode='x unified',
        height=600,
        yaxis=dict(tickformat=',.0f', tickprefix='₱'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def build_metrics_dataframe(
    baseline: List[ProjectionDataPoint],
    combined_projection: List[ProjectionDataPoint],
    combined_name: str
) -> pd.DataFrame:
    """
    Build metrics comparison table as DataFrame (Baseline vs Combined).

    Args:
        baseline: Baseline projection
        combined_projection: Combined projection with all scenarios applied
        combined_name: Name for combined scenario

    Returns:
        pandas DataFrame with comparison metrics
    """
    metrics = {
        'Metric': [
            'Month 3 Cash',
            'Month 6 Cash',
            'Month 12 Cash',
            'Cash Runway (months)',
            'First Negative Date'
        ]
    }

    # Baseline metrics
    metrics['Baseline (No Changes)'] = [
        format_currency(get_projection_metric(baseline, 2)),  # Month 3 (index 2)
        format_currency(get_projection_metric(baseline, 5)),  # Month 6 (index 5)
        format_currency(get_projection_metric(baseline, 11)),  # Month 12 (index 11)
        f"{calculate_runway_months(baseline)} months" if calculate_runway_months(baseline) < len(baseline) else "Never goes negative",
        find_first_negative_date(baseline).strftime('%Y-%m-%d') if find_first_negative_date(baseline) else "Never"
    ]

    # Combined scenario metrics
    metrics[combined_name] = [
        format_currency(get_projection_metric(combined_projection, 2)),  # Month 3
        format_currency(get_projection_metric(combined_projection, 5)),  # Month 6
        format_currency(get_projection_metric(combined_projection, 11)),  # Month 12
        f"{calculate_runway_months(combined_projection)} months" if calculate_runway_months(combined_projection) < len(combined_projection) else "Never goes negative",
        find_first_negative_date(combined_projection).strftime('%Y-%m-%d') if find_first_negative_date(combined_projection) else "Never"
    ]

    return pd.DataFrame(metrics)

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Scenario Comparison - JESUS Company",
    page_icon="📊",
    layout="wide"
)

load_css()
require_auth()

page_header("Scenario Comparison", "Compare multiple scenarios side-by-side")

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

# ═══════════════════════════════════════════════════════════════════
# LIST SAVED SCENARIOS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## Saved Scenarios")

try:
    scenarios = get_all_scenarios()

    if scenarios:
        import pandas as pd

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
            use_container_width=True,
            hide_index=True,
            column_config={
                "Monthly Expenses": st.column_config.TextColumn(
                    "Monthly Expenses",
                    width="large",
                    help="Breakdown of recurring and one-time expenses for this scenario"
                ),
                "Monthly Revenue": st.column_config.TextColumn(
                    "Monthly Revenue",
                    width="large",
                    help="Revenue additions and reductions from this scenario"
                )
            }
        )

        st.markdown("### Select Scenarios to Compare")

        selected_scenarios = st.multiselect(
            "Choose 1-3 scenarios (changes will be combined/stacked together)",
            options=[s['scenario_name'] for s in scenarios],
            max_selections=3
        )

        if len(selected_scenarios) >= 1:
            st.success(f"✅ Selected {len(selected_scenarios)} scenarios for comparison")

            if st.button("📊 Compare Scenarios", type="primary"):
                with st.spinner("Calculating scenario comparisons..."):
                    try:
                        # Validate entity consistency
                        name_to_id = {s['scenario_name']: s['id'] for s in scenarios}
                        name_to_entity = {s['scenario_name']: s['entity'] for s in scenarios}

                        selected_entities = [name_to_entity[name] for name in selected_scenarios]
                        if len(set(selected_entities)) > 1:
                            st.error("❌ All scenarios must be for the same entity")
                            st.info(f"Selected entities: {', '.join(set(selected_entities))}")
                            st.stop()

                        entity = selected_entities[0]

                        # Generate baseline projection (12 months, monthly, realistic)
                        baseline = generate_baseline_projection(entity, 'realistic')

                        # Combine all selected scenarios into one projection
                        calculator = ScenarioCalculator()
                        selected_scenario_ids = [name_to_id[name] for name in selected_scenarios]

                        # Apply all scenarios together (stacks all changes)
                        combined_projection = calculator.apply_multiple_scenarios_to_projection(
                            baseline,
                            selected_scenario_ids
                        )

                        # Create combined scenario name
                        if len(selected_scenarios) == 1:
                            combined_name = selected_scenarios[0]
                        else:
                            combined_name = f"Combined: {', '.join(selected_scenarios)}"

                        # Display results
                        st.markdown("---")
                        st.markdown("## 📊 Comparison Results")
                        st.info(f"**Comparing:** Baseline vs {combined_name}")

                        # Build and display chart
                        fig = build_comparison_chart(baseline, combined_projection, entity, combined_name)
                        st.plotly_chart(fig, use_container_width=True)

                        # Build and display metrics table
                        st.markdown("### Key Metrics Comparison")
                        metrics_df = build_metrics_dataframe(baseline, combined_projection, combined_name)
                        st.dataframe(metrics_df, use_container_width=True)

                        # Interpretation guide
                        with st.expander("💡 How to Interpret Results"):
                            st.markdown("""
                            **Reading the Chart:**
                            - **Baseline (No Changes)** - Gray dashed line: Current trajectory with no scenario changes
                            - **Combined Scenario** - Blue solid line: Projected cash flow with ALL selected scenarios applied together
                            - **Red zone**: Negative cash (cannot pay obligations)
                            - **Orange zone**: Low cash warning (below ₱500,000)

                            **How Scenarios Combine:**
                            When you select multiple scenarios, all changes are **stacked/combined**:
                            - Example: "Hire 5 employees" + "New Office" + "Add 10 Clients"
                            - Result: Shows cumulative effect of ALL THREE changes together
                            - NOT three separate lines - ONE combined projection

                            **Reading the Metrics Table:**
                            - **Month 3/6/12 Cash**: Projected cash balance at those milestones
                            - **Cash Runway**: Months until cash reaches ₱0 (higher is better)
                            - **First Negative Date**: When cash first goes negative (Never is best)

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
        st.warning("No saved scenarios found. Create scenarios on the Scenarios page first.")

except Exception as e:
    st.error(f"Error loading scenarios: {str(e)}")
