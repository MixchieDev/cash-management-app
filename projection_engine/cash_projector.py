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
    """Detailed projection result with both aggregated data and underlying events."""
    data_points: List[ProjectionDataPoint]
    revenue_events: List[RevenueEvent]
    expense_events: List[ExpenseEvent]

    def get_events_for_period(
        self,
        start_date: date,
        end_date: date
    ) -> Tuple[List[RevenueEvent], List[ExpenseEvent]]:
        """
        Get revenue and expense events for a specific period.

        Args:
            start_date: Period start date
            end_date: Period end date

        Returns:
            Tuple of (revenue_events, expense_events) within the period
        """
        period_revenue = [
            e for e in self.revenue_events
            if start_date <= e.date <= end_date
        ]
        period_expenses = [
            e for e in self.expense_events
            if start_date <= e.date <= end_date
        ]
        return period_revenue, period_expenses

    def get_events_for_date(
        self,
        target_date: date
    ) -> Tuple[List[RevenueEvent], List[ExpenseEvent]]:
        """
        Get revenue and expense events for a specific date.

        Args:
            target_date: Target date

        Returns:
            Tuple of (revenue_events, expense_events) on that date
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
        # Validate entity (dynamically from database)
        from config.entity_mapping import get_valid_entities
        valid_entities = get_valid_entities()
        if entity not in valid_entities:
            raise ValueError(f"Invalid entity: {entity}. Must be one of: {valid_entities}")

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

    def _calculate_consolidated_projection(
        self,
        start_date: date,
        end_date: date,
        timeframe: str,
        scenario_type: str,
        scenario_id: Optional[int]
    ) -> List[ProjectionDataPoint]:
        """
        Calculate consolidated projection (ALL active entities combined).

        Dynamically fetches all active entities from the database and
        combines their projections for the consolidated view.

        Args:
            start_date: Projection start date
            end_date: Projection end date
            timeframe: Timeframe
            scenario_type: Scenario type
            scenario_id: Scenario ID

        Returns:
            List of consolidated projection data points
        """
        # Get all active entity codes from database
        from database.settings_manager import get_valid_entity_codes
        entity_codes = get_valid_entity_codes()

        if not entity_codes:
            raise ValueError("No active entities found in database")

        print(f"Calculating consolidated projection for entities: {entity_codes}")

        # Calculate projections for all entities
        entity_projections = {}
        for entity_code in entity_codes:
            try:
                entity_projections[entity_code] = self.calculate_cash_projection(
                    start_date, end_date, entity_code, timeframe, scenario_type, scenario_id
                )
            except ValueError as e:
                # Skip entities with no bank balance
                print(f"Warning: Skipping {entity_code} - {e}")
                continue

        if not entity_projections:
            raise ValueError("No entity projections could be calculated (no bank balances found)")

        # Get the first projection to use as template for dates
        first_entity = next(iter(entity_projections.keys()))
        first_projection = entity_projections[first_entity]

        # Combine projections from all entities
        consolidated = []

        for i, template_point in enumerate(first_projection):
            # Sum values from all entity projections
            total_starting_cash = Decimal('0')
            total_inflows = Decimal('0')
            total_outflows = Decimal('0')
            total_ending_cash = Decimal('0')

            for entity_code, projection in entity_projections.items():
                if i < len(projection):
                    point = projection[i]
                    # Verify dates match
                    assert point.date == template_point.date, \
                        f"Projection dates must match: {point.date} vs {template_point.date}"

                    total_starting_cash += point.starting_cash
                    total_inflows += point.inflows
                    total_outflows += point.outflows
                    total_ending_cash += point.ending_cash

            consolidated_point = ProjectionDataPoint(
                date=template_point.date,
                starting_cash=total_starting_cash,
                inflows=total_inflows,
                outflows=total_outflows,
                ending_cash=total_ending_cash,
                entity='Consolidated',
                timeframe=timeframe,
                scenario_type=scenario_type
            )
            consolidated.append(consolidated_point)

        return consolidated

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
        Calculate cash projection with detailed event data.

        Returns both the aggregated projection data points AND the
        underlying revenue/expense events that contributed to them.
        This enables drill-down into specific periods.

        Args:
            start_date: Projection start date
            end_date: Projection end date
            entity: 'YAHSHUA', 'ABBA', or 'Consolidated'
            timeframe: 'daily', 'weekly', 'monthly', or 'quarterly'
            scenario_type: 'optimistic' or 'realistic'
            scenario_id: Custom scenario to apply (optional)

        Returns:
            ProjectionResult with data_points and underlying events
        """
        # Validate entity (dynamically from database)
        from config.entity_mapping import get_valid_entities
        valid_entities = get_valid_entities()
        if entity not in valid_entities:
            raise ValueError(f"Invalid entity: {entity}. Must be one of: {valid_entities}")

        # For consolidated, calculate separately and combine
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

        # Calculate all revenue and expense events
        revenue_events = revenue_calc.calculate_revenue_events(
            customer_contracts, start_date, end_date
        )
        expense_events = expense_scheduler.calculate_expense_events(
            vendor_contracts, start_date, end_date, entity
        )

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

        return ProjectionResult(
            data_points=projection,
            revenue_events=revenue_events,
            expense_events=expense_events
        )

    def _calculate_consolidated_projection_detailed(
        self,
        start_date: date,
        end_date: date,
        timeframe: str,
        scenario_type: str,
        scenario_id: Optional[int]
    ) -> ProjectionResult:
        """
        Calculate consolidated detailed projection (ALL active entities combined).

        Args:
            start_date: Projection start date
            end_date: Projection end date
            timeframe: Timeframe
            scenario_type: Scenario type
            scenario_id: Scenario ID

        Returns:
            ProjectionResult with combined data from all entities
        """
        # Get all active entity codes from database
        from database.settings_manager import get_valid_entity_codes
        entity_codes = get_valid_entity_codes()

        if not entity_codes:
            raise ValueError("No active entities found in database")

        # Calculate detailed projections for all entities
        all_revenue_events = []
        all_expense_events = []
        entity_projections = {}

        for entity_code in entity_codes:
            try:
                result = self.calculate_cash_projection_detailed(
                    start_date, end_date, entity_code, timeframe, scenario_type, scenario_id
                )
                entity_projections[entity_code] = result.data_points
                all_revenue_events.extend(result.revenue_events)
                all_expense_events.extend(result.expense_events)
            except ValueError as e:
                # Skip entities with no bank balance
                print(f"Warning: Skipping {entity_code} - {e}")
                continue

        if not entity_projections:
            raise ValueError("No entity projections could be calculated (no bank balances found)")

        # Get the first projection to use as template for dates
        first_entity = next(iter(entity_projections.keys()))
        first_projection = entity_projections[first_entity]

        # Combine projections from all entities
        consolidated = []

        for i, template_point in enumerate(first_projection):
            # Sum values from all entity projections
            total_starting_cash = Decimal('0')
            total_inflows = Decimal('0')
            total_outflows = Decimal('0')
            total_ending_cash = Decimal('0')

            for entity_code, projection in entity_projections.items():
                if i < len(projection):
                    point = projection[i]
                    total_starting_cash += point.starting_cash
                    total_inflows += point.inflows
                    total_outflows += point.outflows
                    total_ending_cash += point.ending_cash

            consolidated_point = ProjectionDataPoint(
                date=template_point.date,
                starting_cash=total_starting_cash,
                inflows=total_inflows,
                outflows=total_outflows,
                ending_cash=total_ending_cash,
                entity='Consolidated',
                timeframe=timeframe,
                scenario_type=scenario_type
            )
            consolidated.append(consolidated_point)

        return ProjectionResult(
            data_points=consolidated,
            revenue_events=all_revenue_events,
            expense_events=all_expense_events
        )
