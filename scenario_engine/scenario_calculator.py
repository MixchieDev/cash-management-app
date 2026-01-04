"""
Scenario calculator for JESUS Company Cash Management System.
Applies scenario changes to baseline projections for what-if analysis.
"""
from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional
from copy import deepcopy
from sqlalchemy.orm import joinedload

from projection_engine.cash_projector import ProjectionDataPoint, CashProjector
from database.db_manager import db_manager
from database.models import Scenario, ScenarioChange
from config.settings import PAYROLL_MONTHLY_TOTAL


class ScenarioCalculator:
    """Apply scenario changes to baseline projections."""

    def __init__(self):
        """Initialize scenario calculator."""
        self.projector = CashProjector()

    def get_scenario_by_id(self, scenario_id: int) -> Scenario:
        """
        Get scenario by ID.

        Args:
            scenario_id: Scenario ID

        Returns:
            Scenario object

        Raises:
            ValueError: If scenario not found
        """
        with db_manager.session_scope() as session:
            # Eagerly load the 'changes' relationship to avoid DetachedInstanceError
            scenario = session.query(Scenario)\
                .options(joinedload(Scenario.changes))\
                .filter(Scenario.id == scenario_id)\
                .first()

            if not scenario:
                raise ValueError(f"Scenario with ID {scenario_id} not found")

            # Expunge the scenario from the session (changes are already loaded)
            session.expunge_all()

            return scenario

    def apply_scenario_to_projection(
        self,
        baseline_projection: List[ProjectionDataPoint],
        scenario_id: int
    ) -> List[ProjectionDataPoint]:
        """
        Apply scenario changes to baseline projection.

        Args:
            baseline_projection: Baseline cash projection
            scenario_id: Scenario ID to apply

        Returns:
            New projection with scenario applied
        """
        # Get scenario
        scenario = self.get_scenario_by_id(scenario_id)

        # Start with copy of baseline
        scenario_projection = deepcopy(baseline_projection)

        # Apply each change
        for change in scenario.changes:
            if change.change_type == 'hiring':
                scenario_projection = self._apply_hiring_change(scenario_projection, change)
            elif change.change_type == 'expense':
                scenario_projection = self._apply_expense_change(scenario_projection, change)
            elif change.change_type == 'revenue':
                scenario_projection = self._apply_revenue_change(scenario_projection, change)
            elif change.change_type == 'customer_loss':
                scenario_projection = self._apply_customer_loss_change(scenario_projection, change)
            elif change.change_type == 'investment':
                scenario_projection = self._apply_investment_change(scenario_projection, change)

        # Recalculate ending cash for each period
        scenario_projection = self._recalculate_ending_cash(scenario_projection)

        return scenario_projection

    def apply_multiple_scenarios_to_projection(
        self,
        baseline_projection: List[ProjectionDataPoint],
        scenario_ids: List[int]
    ) -> List[ProjectionDataPoint]:
        """
        Apply multiple scenarios to baseline projection (combines all changes).

        Args:
            baseline_projection: Baseline cash projection
            scenario_ids: List of scenario IDs to apply (changes are stacked/combined)

        Returns:
            New projection with all scenarios applied together
        """
        # Start with copy of baseline
        combined_projection = deepcopy(baseline_projection)

        # Apply each scenario's changes to the same projection (stacking them)
        for scenario_id in scenario_ids:
            scenario = self.get_scenario_by_id(scenario_id)

            # Apply all changes from this scenario
            for change in scenario.changes:
                if change.change_type == 'hiring':
                    combined_projection = self._apply_hiring_change(combined_projection, change)
                elif change.change_type == 'expense':
                    combined_projection = self._apply_expense_change(combined_projection, change)
                elif change.change_type == 'revenue':
                    combined_projection = self._apply_revenue_change(combined_projection, change)
                elif change.change_type == 'customer_loss':
                    combined_projection = self._apply_customer_loss_change(combined_projection, change)
                elif change.change_type == 'investment':
                    combined_projection = self._apply_investment_change(combined_projection, change)

        # Recalculate ending cash after all changes applied
        combined_projection = self._recalculate_ending_cash(combined_projection)

        return combined_projection

    def _apply_hiring_change(
        self,
        projection: List[ProjectionDataPoint],
        change: ScenarioChange
    ) -> List[ProjectionDataPoint]:
        """
        Apply hiring scenario change.

        Adds employees × salary to payroll starting from start_date.

        Args:
            projection: Current projection
            change: Hiring change

        Returns:
            Updated projection
        """
        additional_payroll = change.employees * change.salary_per_employee

        for point in projection:
            if point.date >= change.start_date:
                if change.end_date is None or point.date <= change.end_date:
                    # Add to outflows
                    point.outflows += additional_payroll

        return projection

    def _apply_expense_change(
        self,
        projection: List[ProjectionDataPoint],
        change: ScenarioChange
    ) -> List[ProjectionDataPoint]:
        """
        Apply recurring expense scenario change.

        Args:
            projection: Current projection
            change: Expense change

        Returns:
            Updated projection
        """
        for point in projection:
            if point.date >= change.start_date:
                if change.end_date is None or point.date <= change.end_date:
                    # Add expense based on frequency
                    # For simplicity, add to every period (monthly timeframe assumed)
                    point.outflows += change.expense_amount

        return projection

    def _apply_revenue_change(
        self,
        projection: List[ProjectionDataPoint],
        change: ScenarioChange
    ) -> List[ProjectionDataPoint]:
        """
        Apply new revenue scenario change.

        Adds new_clients × revenue_per_client starting from start_date.

        Args:
            projection: Current projection
            change: Revenue change

        Returns:
            Updated projection
        """
        additional_revenue = change.new_clients * change.revenue_per_client

        for point in projection:
            if point.date >= change.start_date:
                if change.end_date is None or point.date <= change.end_date:
                    # Add to inflows
                    point.inflows += additional_revenue

        return projection

    def _apply_customer_loss_change(
        self,
        projection: List[ProjectionDataPoint],
        change: ScenarioChange
    ) -> List[ProjectionDataPoint]:
        """
        Apply customer loss scenario change.

        Removes revenue starting from start_date.

        Args:
            projection: Current projection
            change: Customer loss change

        Returns:
            Updated projection
        """
        for point in projection:
            if point.date >= change.start_date:
                if change.end_date is None or point.date <= change.end_date:
                    # Subtract from inflows
                    point.inflows -= change.lost_revenue
                    # Ensure inflows don't go negative
                    if point.inflows < 0:
                        point.inflows = Decimal('0.00')

        return projection

    def _apply_investment_change(
        self,
        projection: List[ProjectionDataPoint],
        change: ScenarioChange
    ) -> List[ProjectionDataPoint]:
        """
        Apply one-time investment scenario change.

        Args:
            projection: Current projection
            change: Investment change

        Returns:
            Updated projection
        """
        for point in projection:
            if point.date == change.start_date:
                # One-time outflow
                point.outflows += change.investment_amount
                break

        return projection

    def _recalculate_ending_cash(
        self,
        projection: List[ProjectionDataPoint]
    ) -> List[ProjectionDataPoint]:
        """
        Recalculate ending cash for all periods after applying changes.

        Args:
            projection: Projection with modified inflows/outflows

        Returns:
            Projection with recalculated ending cash
        """
        for i, point in enumerate(projection):
            if i == 0:
                # First period uses original starting cash
                point.ending_cash = point.starting_cash + point.inflows - point.outflows
            else:
                # Subsequent periods use previous ending cash as starting cash
                point.starting_cash = projection[i - 1].ending_cash
                point.ending_cash = point.starting_cash + point.inflows - point.outflows

            # Update is_negative flag
            point.is_negative = point.ending_cash < 0

        return projection

    def calculate_break_even(
        self,
        baseline_projection: List[ProjectionDataPoint],
        scenario_id: int
    ) -> Dict:
        """
        Calculate when scenario becomes affordable.

        Args:
            baseline_projection: Baseline cash projection
            scenario_id: Scenario ID

        Returns:
            Dictionary with break-even analysis:
            {
                'affordable': bool,
                'start_date': date (if affordable),
                'first_negative_date': date (if goes negative),
                'additional_revenue_needed': Decimal (if not affordable),
                'message': str
            }
        """
        # Apply scenario
        scenario_projection = self.apply_scenario_to_projection(baseline_projection, scenario_id)

        # Check if any period goes negative
        first_negative_date = None
        for point in scenario_projection:
            if point.is_negative:
                first_negative_date = point.date
                break

        if first_negative_date is None:
            # Scenario is affordable throughout the projection
            return {
                'affordable': True,
                'start_date': scenario_projection[0].date,
                'first_negative_date': None,
                'additional_revenue_needed': Decimal('0.00'),
                'message': 'Scenario is affordable throughout the entire projection period.'
            }
        else:
            # Find how much additional revenue is needed
            # Get the most negative cash position
            min_cash = min(point.ending_cash for point in scenario_projection)
            additional_revenue_needed = abs(min_cash)

            return {
                'affordable': False,
                'start_date': None,
                'first_negative_date': first_negative_date,
                'additional_revenue_needed': additional_revenue_needed,
                'message': f'Scenario results in negative cash on {first_negative_date}. '
                           f'Additional revenue of ₱{additional_revenue_needed:,.2f} needed.'
            }

    def calculate_scenario_impact_summary(
        self,
        baseline_projection: List[ProjectionDataPoint],
        scenario_projection: List[ProjectionDataPoint]
    ) -> Dict:
        """
        Calculate summary of scenario impact vs baseline.

        Args:
            baseline_projection: Baseline projection
            scenario_projection: Scenario projection

        Returns:
            Dictionary with impact summary
        """
        # Calculate totals
        baseline_total_inflows = sum(p.inflows for p in baseline_projection)
        baseline_total_outflows = sum(p.outflows for p in baseline_projection)
        baseline_ending_cash = baseline_projection[-1].ending_cash

        scenario_total_inflows = sum(p.inflows for p in scenario_projection)
        scenario_total_outflows = sum(p.outflows for p in scenario_projection)
        scenario_ending_cash = scenario_projection[-1].ending_cash

        # Calculate differences
        inflows_diff = scenario_total_inflows - baseline_total_inflows
        outflows_diff = scenario_total_outflows - baseline_total_outflows
        ending_cash_diff = scenario_ending_cash - baseline_ending_cash

        return {
            'baseline': {
                'total_inflows': baseline_total_inflows,
                'total_outflows': baseline_total_outflows,
                'ending_cash': baseline_ending_cash
            },
            'scenario': {
                'total_inflows': scenario_total_inflows,
                'total_outflows': scenario_total_outflows,
                'ending_cash': scenario_ending_cash
            },
            'difference': {
                'inflows': inflows_diff,
                'outflows': outflows_diff,
                'ending_cash': ending_cash_diff
            },
            'percentage_change': {
                'inflows': (inflows_diff / baseline_total_inflows * 100) if baseline_total_inflows > 0 else 0,
                'outflows': (outflows_diff / baseline_total_outflows * 100) if baseline_total_outflows > 0 else 0,
                'ending_cash': (ending_cash_diff / baseline_ending_cash * 100) if baseline_ending_cash > 0 else 0
            }
        }
