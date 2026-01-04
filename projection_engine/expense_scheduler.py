"""
Expense scheduler for JESUS Company Cash Management System.
Schedules expense outflows from vendor contracts.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from calendar import monthrange

from config.constants import EXPENSE_FREQUENCIES
from database.models import VendorContract
from database.queries import get_payment_overrides


@dataclass
class ExpenseEvent:
    """Single expense outflow event."""
    date: date
    vendor_id: Optional[int]
    vendor_name: str
    amount: Decimal
    entity: str
    category: str
    priority: int
    is_payroll: bool = False


class ExpenseScheduler:
    """Schedule projected expense outflows."""

    def __init__(self):
        """Initialize expense scheduler."""
        pass

    def get_vendor_payment_dates(
        self,
        contract: VendorContract,
        start_date: date,
        end_date: date
    ) -> List[date]:
        """
        Get all payment dates for a vendor contract.

        Args:
            contract: Vendor contract
            start_date: Projection start date
            end_date: Projection end date

        Returns:
            List of payment dates
        """
        payment_dates = []

        # Determine the effective start date (maximum of projection start and contract start)
        effective_start_date = start_date
        if hasattr(contract, 'start_date') and contract.start_date:
            effective_start_date = max(start_date, contract.start_date)

        # Determine the effective end date (minimum of projection end and contract end)
        effective_end_date = end_date
        if hasattr(contract, 'end_date') and contract.end_date:
            effective_end_date = min(end_date, contract.end_date)

        # If effective start is after effective end, no payments in range
        if effective_start_date > effective_end_date:
            return payment_dates

        # Get frequency in days
        frequency_days = EXPENSE_FREQUENCIES.get(contract.frequency)

        if frequency_days is None:  # One-time payment
            # Check if due_date is within effective period
            if effective_start_date <= contract.due_date <= effective_end_date:
                payment_dates.append(contract.due_date)
            return payment_dates

        # Recurring payment
        current_date = contract.due_date

        # Start from the first payment on or after effective_start_date
        while current_date < effective_start_date:
            if contract.frequency == 'Monthly':
                current_date += relativedelta(months=1)
            elif contract.frequency == 'Quarterly':
                current_date += relativedelta(months=3)
            elif contract.frequency == 'Annual':
                current_date += relativedelta(years=1)
            else:
                current_date += timedelta(days=frequency_days)

        # Generate payment dates (respecting contract end_date)
        while current_date <= effective_end_date:
            payment_dates.append(current_date)

            # Move to next payment date
            if contract.frequency == 'Monthly':
                current_date += relativedelta(months=1)
            elif contract.frequency == 'Quarterly':
                current_date += relativedelta(months=3)
            elif contract.frequency == 'Annual':
                current_date += relativedelta(years=1)
            else:
                current_date += timedelta(days=frequency_days)

        return payment_dates

    def calculate_vendor_events(
        self,
        contracts: List[VendorContract],
        start_date: date,
        end_date: date,
        entity: Optional[str] = None,
        payment_overrides: Optional[List[Dict]] = None
    ) -> List[ExpenseEvent]:
        """
        Calculate all vendor expense events.

        Args:
            contracts: List of active vendor contracts
            start_date: Projection start date
            end_date: Projection end date
            entity: Filter by entity (optional)
            payment_overrides: Optional list of payment overrides (for testing).
                              If None, loads from database.

        Returns:
            List of vendor expense events
        """
        events = []

        # Load payment overrides for vendor payments
        # Use provided overrides if given (for testing), otherwise load from DB
        if payment_overrides is None:
            overrides = get_payment_overrides(override_type='vendor')
        else:
            overrides = payment_overrides

        # Create a lookup dict: (vendor_id, original_date) -> override
        override_lookup = {}
        for override in overrides:
            key = (override['contract_id'], override['original_date'])
            override_lookup[key] = override

        for contract in contracts:
            # Skip inactive contracts
            if contract.status != 'Active':
                continue

            # Skip if entity filter doesn't match
            if entity and contract.entity != entity:
                continue

            # Skip if vendor has a start_date and projection period is before that date
            # If start_date is None, vendor is already active
            if hasattr(contract, 'start_date') and contract.start_date:
                # If the entire projection period is before the vendor's start date, skip it
                if end_date < contract.start_date:
                    continue

            # Get payment dates for this contract
            payment_dates = self.get_vendor_payment_dates(contract, start_date, end_date)

            for payment_date in payment_dates:
                # Skip payment if it's before vendor's start date
                if hasattr(contract, 'start_date') and contract.start_date:
                    if payment_date < contract.start_date:
                        continue

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
                        # Verify new date is still in projection range
                        if payment_date < start_date or payment_date > end_date:
                            continue

                # Use vendor amount and entity directly
                event_amount = contract.amount
                event_entity = contract.entity

                event = ExpenseEvent(
                    date=payment_date,
                    vendor_id=contract.id,
                    vendor_name=contract.vendor_name,
                    amount=event_amount,
                    entity=event_entity,
                    category=contract.category,
                    priority=contract.priority,
                    is_payroll=False
                )
                events.append(event)

        return events

    def calculate_expense_events(
        self,
        vendor_contracts: List[VendorContract],
        start_date: date,
        end_date: date,
        entity: str,
        payment_overrides: Optional[List[Dict]] = None
    ) -> List[ExpenseEvent]:
        """
        Calculate ALL expense events from vendor contracts.

        Args:
            vendor_contracts: List of vendor contracts
            start_date: Projection start date
            end_date: Projection end date
            entity: Entity for expenses
            payment_overrides: Optional list of payment overrides (for testing).
                              If None, loads from database.

        Returns:
            List of all expense events (sorted by date, then priority)
        """
        events = []

        # Add vendor events (includes payroll vendors)
        # Pass through payment_overrides to calculate_vendor_events
        vendor_events = self.calculate_vendor_events(
            vendor_contracts, start_date, end_date, entity, payment_overrides
        )
        events.extend(vendor_events)

        # Sort by date, then by priority (lower priority number = higher priority)
        events.sort(key=lambda x: (x.date, x.priority))

        return events

    def calculate_total_expenses_by_date(
        self,
        events: List[ExpenseEvent],
        target_date: date,
        entity: Optional[str] = None
    ) -> Decimal:
        """
        Calculate total expenses on a specific date.

        Args:
            events: List of expense events
            target_date: Date to calculate expenses for
            entity: Filter by entity (optional)

        Returns:
            Total expenses for that date
        """
        total = Decimal('0.00')

        for event in events:
            if event.date == target_date:
                if entity is None or event.entity == entity:
                    total += event.amount

        return total

    def calculate_total_expenses_by_period(
        self,
        events: List[ExpenseEvent],
        start_date: date,
        end_date: date,
        entity: Optional[str] = None
    ) -> Decimal:
        """
        Calculate total expenses during a period.

        Args:
            events: List of expense events
            start_date: Period start date
            end_date: Period end date
            entity: Filter by entity (optional)

        Returns:
            Total expenses for the period
        """
        total = Decimal('0.00')

        for event in events:
            if start_date <= event.date <= end_date:
                if entity is None or event.entity == entity:
                    total += event.amount

        return total

    def get_expense_breakdown_by_category(
        self,
        events: List[ExpenseEvent],
        entity: Optional[str] = None
    ) -> Dict[str, Decimal]:
        """
        Get expense breakdown by category.

        Args:
            events: List of expense events
            entity: Filter by entity (optional)

        Returns:
            Dictionary mapping category to total expenses
        """
        breakdown = {}

        for event in events:
            if entity is None or event.entity == entity:
                if event.category not in breakdown:
                    breakdown[event.category] = Decimal('0.00')
                breakdown[event.category] += event.amount

        return breakdown
