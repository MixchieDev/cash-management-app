"""
Cash projector engine for JESUS Company Cash Management System.
Main projection engine that calculates cash flow forecasts.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta

from database.db_manager import db_manager
from database.models import CustomerContract, VendorContract, BankBalance, Projection
from projection_engine.revenue_calculator import RevenueCalculator, RevenueEvent
from projection_engine.expense_scheduler import ExpenseScheduler, ExpenseEvent


@dataclass
class ProjectionDataPoint:
    """Single data point in cash projection."""
    date: date
    starting_cash: Decimal
    inflows: Decimal
    outflows: Decimal
    ending_cash: Decimal
    entity: str
    timeframe: str
    scenario_type: str
    is_negative: bool = False

    def __post_init__(self):
        """Set is_negative flag."""
        self.is_negative = self.ending_cash < 0


@dataclass
class ProjectionResult:
    """Complete projection result with aggregated data and detailed events."""
    data_points: List[ProjectionDataPoint]
    revenue_events: List[RevenueEvent]
    expense_events: List[ExpenseEvent]

    def get_events_for_period(
        self,
        start_date: date,
        end_date: date
    ) -> Tuple[List[RevenueEvent], List[ExpenseEvent]]:
        """
        Get all events within a specific period.

        Args:
            start_date: Period start date (inclusive)
            end_date: Period end date (inclusive)

        Returns:
            Tuple of (revenue_events, expense_events) for the period
        """
        revenue_events = [
            event for event in self.revenue_events
            if start_date <= event.date <= end_date
        ]
        expense_events = [
            event for event in self.expense_events
            if start_date <= event.date <= end_date
        ]
        return revenue_events, expense_events

    def get_events_for_date(
        self,
        target_date: date
    ) -> Tuple[List[RevenueEvent], List[ExpenseEvent]]:
        """
        Get all events for a specific date.

        Args:
            target_date: Target date

        Returns:
            Tuple of (revenue_events, expense_events) for that date
        """
        return self.get_events_for_period(target_date, target_date)


class CashProjector:
    """Main cash projection engine."""

    def __init__(self):
        """Initialize cash projector."""
        pass

    def get_starting_cash(self, entity: str, as_of_date: Optional[date] = None) -> Tuple[Decimal, date]:
        """
        Get starting cash balance for entity.

        CRITICAL: ALWAYS use the most recent bank balance from bank_balances table.
        NEVER use projected cash as starting point.

        Args:
            entity: Entity ('YAHSHUA' or 'ABBA')
            as_of_date: Get balance as of this date (defaults to most recent)

        Returns:
            Tuple of (balance, balance_date)

        Raises:
            ValueError: If no bank balance found
        """
        with db_manager.session_scope() as session:
            query = session.query(BankBalance).filter(
                BankBalance.entity == entity
            )

            if as_of_date:
                query = query.filter(BankBalance.balance_date <= as_of_date)

            balance_record = query.order_by(BankBalance.balance_date.desc()).first()

            if not balance_record:
                raise ValueError(
                    f"No bank balance found for entity '{entity}'. "
                    f"Please add a bank balance record first."
                )

            return balance_record.balance, balance_record.balance_date

    def get_active_customer_contracts(self, entity: str) -> List[CustomerContract]:
        """
        Get active customer contracts for entity.

        Args:
            entity: Entity ('YAHSHUA' or 'ABBA')

        Returns:
            List of active customer contracts
        """
        with db_manager.session_scope() as session:
            contracts = session.query(CustomerContract).filter(
                CustomerContract.entity == entity,
                CustomerContract.status == 'Active'
            ).all()

            # Detach from session so we can use them after session closes
            session.expunge_all()

            return contracts

    def get_active_vendor_contracts(self, entity: str) -> List[VendorContract]:
        """
        Get active vendor contracts for entity.

        Args:
            entity: Entity ('YAHSHUA' or 'ABBA')

        Returns:
            List of active vendor contracts
        """
        with db_manager.session_scope() as session:
            # Get contracts for this entity
            contracts = session.query(VendorContract).filter(
                VendorContract.status == 'Active'
            ).filter(
                VendorContract.entity == entity
            ).all()

            # Detach from session
            session.expunge_all()

            return contracts

    def generate_date_range(
        self,
        start_date: date,
        end_date: date,
        timeframe: str = 'monthly'
    ) -> List[date]:
        """
        Generate list of dates for projection based on timeframe.

        Args:
            start_date: Projection start date
            end_date: Projection end date
            timeframe: 'daily', 'weekly', 'monthly', or 'quarterly'

        Returns:
            List of dates (period end dates)
        """
        dates = []
        current_date = start_date

        if timeframe == 'daily':
            while current_date <= end_date:
                dates.append(current_date)
                current_date += timedelta(days=1)

        elif timeframe == 'weekly':
            while current_date <= end_date:
                period_end = min(current_date + timedelta(days=6), end_date)
                dates.append(period_end)
                current_date += timedelta(days=7)

        elif timeframe == 'monthly':
            while current_date <= end_date:
                # Last day of current month
                next_month = current_date + relativedelta(months=1)
                period_end = next_month - timedelta(days=1)
                period_end = min(period_end, end_date)
                dates.append(period_end)
                current_date = next_month

        elif timeframe == 'quarterly':
            while current_date <= end_date:
                # Last day of current quarter
                period_end = current_date + relativedelta(months=3) - timedelta(days=1)
                period_end = min(period_end, end_date)
                dates.append(period_end)
                current_date += relativedelta(months=3)

        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")

        return dates

    def calculate_cash_projection(
        self,
        start_date: date,
        end_date: date,
        entity: str,
        timeframe: str = 'monthly',
        scenario_type: str = 'realistic',
        scenario_id: Optional[int] = None
    ) -> List[ProjectionDataPoint]:
        """
        Calculate cash projection for specified period.

        Args:
            start_date: Projection start date
            end_date: Projection end date
            entity: 'YAHSHUA', 'ABBA', or 'Consolidated'
            timeframe: 'daily', 'weekly', 'monthly', or 'quarterly'
            scenario_type: 'optimistic' or 'realistic'
            scenario_id: Custom scenario to apply (optional)

        Returns:
            List of projection data points

        Algorithm:
            1. Get starting cash from bank_balances table (most recent)
            2. For each time period:
               a. Calculate revenue inflows (contracts + payment terms + reliability)
               b. Calculate expense outflows (vendors + payroll)
               c. Calculate ending cash: start + inflows - outflows
               d. Update starting cash for next period
        """
        # Validate entity
        if entity not in ['YAHSHUA', 'ABBA', 'Consolidated']:
            raise ValueError(f"Invalid entity: {entity}. Must be YAHSHUA, ABBA, or Consolidated")

        # For consolidated, calculate separately and combine
        if entity == 'Consolidated':
            return self._calculate_consolidated_projection(
                start_date, end_date, timeframe, scenario_type, scenario_id
            )

        # Get starting cash
        starting_cash, balance_date = self.get_starting_cash(entity)
        print(f"Starting cash for {entity}: ₱{starting_cash:,.2f} (as of {balance_date})")

        # Get active contracts
        customer_contracts = self.get_active_customer_contracts(entity)
        vendor_contracts = self.get_active_vendor_contracts(entity)

        print(f"Active customers: {len(customer_contracts)}, Active vendors: {len(vendor_contracts)}")

        # Initialize calculators
        revenue_calc = RevenueCalculator(scenario_type=scenario_type)
        expense_scheduler = ExpenseScheduler()

        # Calculate all revenue and expense events
        revenue_events = revenue_calc.calculate_revenue_events(
            customer_contracts, start_date, end_date
        )
        expense_events = expense_scheduler.calculate_expense_events(
            vendor_contracts, start_date, end_date, entity
        )

        print(f"Revenue events: {len(revenue_events)}, Expense events: {len(expense_events)}")

        # Generate projection data points
        projection = []
        current_cash = starting_cash

        # Generate date range
        period_dates = self.generate_date_range(start_date, end_date, timeframe)

        # Track period start date
        period_start = start_date

        for period_end in period_dates:
            # Calculate inflows for this period
            inflows = revenue_calc.calculate_total_revenue_by_period(
                revenue_events, period_start, period_end, entity
            )

            # Calculate outflows for this period
            outflows = expense_scheduler.calculate_total_expenses_by_period(
                expense_events, period_start, period_end, entity
            )

            # Calculate ending cash
            ending_cash = current_cash + inflows - outflows

            # Create data point
            data_point = ProjectionDataPoint(
                date=period_end,
                starting_cash=current_cash,
                inflows=inflows,
                outflows=outflows,
                ending_cash=ending_cash,
                entity=entity,
                timeframe=timeframe,
                scenario_type=scenario_type
            )
            projection.append(data_point)

            # Update current cash for next period
            current_cash = ending_cash

            # Update period start for next iteration
            period_start = period_end + timedelta(days=1)

        return projection

    def calculate_cash_projection_detailed(
        self,
        start_date: date,
        end_date: date,
        entity: str,
        timeframe: str = 'monthly',
        scenario_type: str = 'realistic',
        scenario_id: Optional[int] = None
    ) -> ProjectionResult:
        """
        Calculate cash projection with detailed event breakdown.

        This method returns BOTH aggregated projection data AND the underlying
        revenue/expense events for transaction-level drill-down.

        Args:
            start_date: Projection start date
            end_date: Projection end date
            entity: 'YAHSHUA', 'ABBA', or 'Consolidated'
            timeframe: 'daily', 'weekly', 'monthly', or 'quarterly'
            scenario_type: 'optimistic' or 'realistic'
            scenario_id: Custom scenario to apply (optional)

        Returns:
            ProjectionResult with both aggregated data and detailed events

        Example:
            >>> projector = CashProjector()
            >>> result = projector.calculate_cash_projection_detailed(
            ...     start_date=date(2026, 1, 1),
            ...     end_date=date(2026, 3, 31),
            ...     entity='YAHSHUA',
            ...     timeframe='daily',
            ...     scenario_type='realistic'
            ... )
            >>> # Get aggregated data points
            >>> data_points = result.data_points
            >>> # Get events for Jan 15, 2026
            >>> revenue, expenses = result.get_events_for_date(date(2026, 1, 15))
        """
        # Validate entity
        if entity not in ['YAHSHUA', 'ABBA', 'Consolidated']:
            raise ValueError(f"Invalid entity: {entity}. Must be YAHSHUA, ABBA, or Consolidated")

        # For consolidated view, need to combine events from both entities
        if entity == 'Consolidated':
            return self._calculate_consolidated_projection_detailed(
                start_date, end_date, timeframe, scenario_type, scenario_id
            )

        # Get starting cash
        starting_cash, balance_date = self.get_starting_cash(entity)

        # Get active contracts
        customer_contracts = self.get_active_customer_contracts(entity)
        vendor_contracts = self.get_active_vendor_contracts(entity)

        # Initialize calculators
        revenue_calc = RevenueCalculator(scenario_type=scenario_type)
        expense_scheduler = ExpenseScheduler()

        # Calculate ALL revenue and expense events
        revenue_events = revenue_calc.calculate_revenue_events(
            customer_contracts, start_date, end_date
        )
        expense_events = expense_scheduler.calculate_expense_events(
            vendor_contracts, start_date, end_date, entity
        )

        # Generate aggregated projection data points (reuse existing logic)
        projection = []
        current_cash = starting_cash
        period_dates = self.generate_date_range(start_date, end_date, timeframe)
        period_start = start_date

        for period_end in period_dates:
            # Calculate inflows for this period
            inflows = revenue_calc.calculate_total_revenue_by_period(
                revenue_events, period_start, period_end, entity
            )

            # Calculate outflows for this period
            outflows = expense_scheduler.calculate_total_expenses_by_period(
                expense_events, period_start, period_end, entity
            )

            # Calculate ending cash
            ending_cash = current_cash + inflows - outflows

            # Create data point
            data_point = ProjectionDataPoint(
                date=period_end,
                starting_cash=current_cash,
                inflows=inflows,
                outflows=outflows,
                ending_cash=ending_cash,
                entity=entity,
                timeframe=timeframe,
                scenario_type=scenario_type
            )
            projection.append(data_point)

            # Update for next period
            current_cash = ending_cash
            period_start = period_end + timedelta(days=1)

        # Return complete result with both aggregated data and events
        return ProjectionResult(
            data_points=projection,
            revenue_events=revenue_events,
            expense_events=expense_events
        )

    def _calculate_consolidated_projection(
        self,
        start_date: date,
        end_date: date,
        timeframe: str,
        scenario_type: str,
        scenario_id: Optional[int]
    ) -> List[ProjectionDataPoint]:
        """
        Calculate consolidated projection (YAHSHUA + ABBA combined).

        Args:
            start_date: Projection start date
            end_date: Projection end date
            timeframe: Timeframe
            scenario_type: Scenario type
            scenario_id: Scenario ID

        Returns:
            List of consolidated projection data points
        """
        # Calculate projections for both entities
        yahshua_projection = self.calculate_cash_projection(
            start_date, end_date, 'YAHSHUA', timeframe, scenario_type, scenario_id
        )
        abba_projection = self.calculate_cash_projection(
            start_date, end_date, 'ABBA', timeframe, scenario_type, scenario_id
        )

        # Combine projections
        consolidated = []

        for yahshua_point, abba_point in zip(yahshua_projection, abba_projection):
            # Verify dates match
            assert yahshua_point.date == abba_point.date, "Projection dates must match"

            consolidated_point = ProjectionDataPoint(
                date=yahshua_point.date,
                starting_cash=yahshua_point.starting_cash + abba_point.starting_cash,
                inflows=yahshua_point.inflows + abba_point.inflows,
                outflows=yahshua_point.outflows + abba_point.outflows,
                ending_cash=yahshua_point.ending_cash + abba_point.ending_cash,
                entity='Consolidated',
                timeframe=timeframe,
                scenario_type=scenario_type
            )
            consolidated.append(consolidated_point)

        return consolidated

    def _calculate_consolidated_projection_detailed(
        self,
        start_date: date,
        end_date: date,
        timeframe: str,
        scenario_type: str,
        scenario_id: Optional[int]
    ) -> ProjectionResult:
        """
        Calculate consolidated projection with detailed events.

        Combines YAHSHUA and ABBA projections and merges their events.

        Args:
            start_date: Projection start date
            end_date: Projection end date
            timeframe: Timeframe
            scenario_type: Scenario type
            scenario_id: Scenario ID

        Returns:
            ProjectionResult with consolidated data
        """
        # Calculate detailed projections for both entities
        yahshua_result = self.calculate_cash_projection_detailed(
            start_date, end_date, 'YAHSHUA', timeframe, scenario_type, scenario_id
        )
        abba_result = self.calculate_cash_projection_detailed(
            start_date, end_date, 'ABBA', timeframe, scenario_type, scenario_id
        )

        # Combine data points (existing logic)
        consolidated_data_points = []
        for yahshua_point, abba_point in zip(yahshua_result.data_points, abba_result.data_points):
            assert yahshua_point.date == abba_point.date, "Projection dates must match"

            consolidated_point = ProjectionDataPoint(
                date=yahshua_point.date,
                starting_cash=yahshua_point.starting_cash + abba_point.starting_cash,
                inflows=yahshua_point.inflows + abba_point.inflows,
                outflows=yahshua_point.outflows + abba_point.outflows,
                ending_cash=yahshua_point.ending_cash + abba_point.ending_cash,
                entity='Consolidated',
                timeframe=timeframe,
                scenario_type=scenario_type
            )
            consolidated_data_points.append(consolidated_point)

        # Merge event lists
        all_revenue_events = yahshua_result.revenue_events + abba_result.revenue_events
        all_expense_events = yahshua_result.expense_events + abba_result.expense_events

        # Sort merged events by date
        all_revenue_events.sort(key=lambda x: x.date)
        all_expense_events.sort(key=lambda x: x.date)

        return ProjectionResult(
            data_points=consolidated_data_points,
            revenue_events=all_revenue_events,
            expense_events=all_expense_events
        )

    def save_projection_to_db(self, projection: List[ProjectionDataPoint], scenario_id: Optional[int] = None):
        """
        Save projection to database for caching.

        Args:
            projection: Projection data points
            scenario_id: Scenario ID (optional)
        """
        with db_manager.session_scope() as session:
            for point in projection:
                db_projection = Projection(
                    projection_date=point.date,
                    entity=point.entity,
                    timeframe=point.timeframe,
                    scenario_type=point.scenario_type,
                    scenario_id=scenario_id,
                    starting_cash=point.starting_cash,
                    inflows=point.inflows,
                    outflows=point.outflows,
                    ending_cash=point.ending_cash,
                    is_negative=point.is_negative
                )
                session.add(db_projection)

        print(f"✓ Saved {len(projection)} projection data points to database")
