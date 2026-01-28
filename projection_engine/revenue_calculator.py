"""
Revenue calculator for JESUS Company Cash Management System.
Calculates projected revenue inflows based on customer contracts and payment terms.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta

from config.constants import PAYMENT_PLAN_FREQUENCIES
from database.models import CustomerContract
from database.queries import get_payment_overrides


def _get_payment_terms_settings() -> Dict[str, int]:
    """
    Get payment terms settings from database with fallback to defaults.

    Returns:
        Dictionary with invoice_lead_days, payment_terms_days, realistic_delay_days
    """
    try:
        from database.settings_manager import get_payment_terms_config
        return get_payment_terms_config()
    except Exception:
        # Fallback to defaults if database not available
        return {
            'invoice_lead_days': 15,
            'payment_terms_days': 30,
            'realistic_delay_days': 10,
            'default_reliability': 80
        }


@dataclass
class RevenueEvent:
    """Single revenue inflow event."""
    date: date
    customer_id: int
    company_name: str
    amount: Decimal
    entity: str
    event_type: str  # 'invoice' or 'payment'
    payment_plan: str
    invoice_date: Optional[date] = None


class RevenueCalculator:
    """Calculate projected revenue inflows."""

    def __init__(self, scenario_type: str = 'realistic'):
        """
        Initialize revenue calculator.

        Args:
            scenario_type: 'optimistic' or 'realistic'
        """
        self.scenario_type = scenario_type

        # Load settings from database
        settings = _get_payment_terms_settings()

        # Determine payment delay based on scenario
        if scenario_type == 'optimistic':
            self.payment_delay_days = 0  # On-time payment
        else:  # realistic
            self.payment_delay_days = settings['realistic_delay_days']  # Default: 10 days

    def calculate_payment_date(self, billing_month: date, contract_start: date) -> date:
        """
        Calculate payment date based on contract start day.

        Payment is received on the same day of month as the contract started,
        plus any delay for realistic scenario.

        Args:
            billing_month: The month being billed (e.g., March 2026)
            contract_start: Contract start date (use day of month)

        Returns:
            Payment date for this billing month

        Example:
            Contract starts March 5 with realistic scenario (10-day delay):
            >>> calc = RevenueCalculator(scenario_type='realistic')
            >>> calc.calculate_payment_date(date(2026, 4, 1), date(2026, 3, 5))
            date(2026, 4, 15)  # 5th + 10 day delay = 15th
        """
        from calendar import monthrange

        # Use the day of month from contract_start
        payment_day = contract_start.day

        # Cap at max days in the billing month (handle Feb, etc.)
        max_day = monthrange(billing_month.year, billing_month.month)[1]
        payment_day = min(payment_day, max_day)

        # Payment is on that day of the billing month
        base_payment_date = date(billing_month.year, billing_month.month, payment_day)

        # Add delay for realistic scenario
        return base_payment_date + timedelta(days=self.payment_delay_days)

    def get_billing_months(self, contract: CustomerContract, start_date: date, end_date: date) -> List[date]:
        """
        Get all billing months for a contract within the projection period.

        Args:
            contract: Customer contract
            start_date: Projection start date
            end_date: Projection end date

        Returns:
            List of billing month dates (1st of each billing month)

        Example:
            For a Monthly contract from Jan 2026 to Dec 2026:
            Returns: [date(2026, 1, 1), date(2026, 2, 1), ..., date(2026, 12, 1)]
        """
        billing_months = []

        # Determine billing frequency
        frequency_months = PAYMENT_PLAN_FREQUENCIES.get(contract.payment_plan, 1)

        # Start from contract start month or projection start month, whichever is later
        current_month = max(
            date(contract.contract_start.year, contract.contract_start.month, 1),
            date(start_date.year, start_date.month, 1)
        )

        # End at contract end or projection end, whichever is earlier
        if contract.contract_end:
            last_month = min(
                date(contract.contract_end.year, contract.contract_end.month, 1),
                date(end_date.year, end_date.month, 1)
            )
        else:
            # No contract end = subscription continues
            last_month = date(end_date.year, end_date.month, 1)

        # Generate billing months
        while current_month <= last_month:
            billing_months.append(current_month)
            current_month += relativedelta(months=frequency_months)

        return billing_months

    def calculate_revenue_events(
        self,
        contracts: List[CustomerContract],
        start_date: date,
        end_date: date,
        payment_overrides: Optional[List[Dict]] = None
    ) -> List[RevenueEvent]:
        """
        Calculate all revenue events (payments) for contracts.

        Args:
            contracts: List of active customer contracts
            start_date: Projection start date
            end_date: Projection end date
            payment_overrides: Optional list of payment overrides (for testing).
                              If None, loads from database.

        Returns:
            List of revenue events (sorted by date)
        """
        events = []

        # Load payment overrides for customer payments
        # Use provided overrides if given (for testing), otherwise load from DB
        if payment_overrides is None:
            overrides = get_payment_overrides(override_type='customer')
        else:
            overrides = payment_overrides

        # Create a lookup dict: (customer_id, original_date) -> override
        override_lookup = {}
        for override in overrides:
            key = (override['contract_id'], override['original_date'])
            override_lookup[key] = override

        for contract in contracts:
            # Skip inactive contracts
            if contract.status != 'Active':
                continue

            # Get billing months for this contract
            billing_months = self.get_billing_months(contract, start_date, end_date)

            for billing_month in billing_months:
                # Calculate payment date based on contract start day
                # Payment is received on the same day of month as contract started
                payment_date = self.calculate_payment_date(billing_month, contract.contract_start)

                # Check for payment override
                override_key = (contract.id, payment_date)
                if override_key in override_lookup:
                    override = override_lookup[override_key]
                    if override['action'] == 'skip':
                        # Skip this payment entirely
                        continue
                    elif override['action'] == 'move' and override['new_date']:
                        # Move to new date
                        payment_date = override['new_date']

                # Only include if payment falls within projection period
                if start_date <= payment_date <= end_date:
                    # Calculate payment amount based on payment plan
                    # Monthly Fee × number of months in payment period
                    # Example: ₱100K monthly fee with Quarterly plan = ₱100K × 3 = ₱300K per quarter
                    frequency_months = PAYMENT_PLAN_FREQUENCIES.get(contract.payment_plan, 1)
                    payment_amount = contract.monthly_fee * frequency_months

                    event = RevenueEvent(
                        date=payment_date,
                        customer_id=contract.id,
                        company_name=contract.company_name,
                        amount=payment_amount,
                        entity=contract.entity,
                        event_type='payment',
                        payment_plan=contract.payment_plan,
                        invoice_date=None  # Simplified: no separate invoice date tracking
                    )
                    events.append(event)

        # Sort by date
        events.sort(key=lambda x: x.date)

        return events

    def calculate_total_revenue_by_date(
        self,
        events: List[RevenueEvent],
        target_date: date,
        entity: Optional[str] = None
    ) -> Decimal:
        """
        Calculate total revenue received on a specific date.

        Args:
            events: List of revenue events
            target_date: Date to calculate revenue for
            entity: Filter by entity (optional)

        Returns:
            Total revenue for that date
        """
        total = Decimal('0.00')

        for event in events:
            if event.date == target_date:
                if entity is None or event.entity == entity:
                    total += event.amount

        return total

    def calculate_total_revenue_by_period(
        self,
        events: List[RevenueEvent],
        start_date: date,
        end_date: date,
        entity: Optional[str] = None
    ) -> Decimal:
        """
        Calculate total revenue received during a period.

        Args:
            events: List of revenue events
            start_date: Period start date
            end_date: Period end date
            entity: Filter by entity (optional)

        Returns:
            Total revenue for the period
        """
        total = Decimal('0.00')

        for event in events:
            if start_date <= event.date <= end_date:
                if entity is None or event.entity == entity:
                    total += event.amount

        return total

    def get_revenue_breakdown_by_customer(
        self,
        events: List[RevenueEvent],
        entity: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """
        Get revenue breakdown by customer.

        Args:
            events: List of revenue events
            entity: Filter by entity (optional)

        Returns:
            Dictionary mapping company name to total revenue
        """
        breakdown = {}

        for event in events:
            if entity is None or event.entity == entity:
                if event.company_name not in breakdown:
                    breakdown[event.company_name] = Decimal('0.00')
                breakdown[event.company_name] += event.amount

        return breakdown
