"""
Tests for vendor contract end_date functionality.
Ensures expenses stop after the contract end_date.
"""
import pytest
from datetime import date
from decimal import Decimal

from projection_engine.expense_scheduler import ExpenseScheduler
from database.models import VendorContract


class MockVendorContract:
    """Mock vendor contract for testing."""
    def __init__(
        self,
        vendor_name: str,
        amount: Decimal,
        frequency: str,
        due_date: date,
        entity: str = 'YAHSHUA',
        category: str = 'Operations',
        priority: int = 3,
        status: str = 'Active',
        start_date: date = None,
        end_date: date = None,
        id: int = 1
    ):
        self.id = id
        self.vendor_name = vendor_name
        self.amount = amount
        self.frequency = frequency
        self.due_date = due_date
        self.entity = entity
        self.category = category
        self.priority = priority
        self.status = status
        self.start_date = start_date
        self.end_date = end_date


class TestVendorEndDate:
    """Test end_date functionality for vendor contracts."""

    def test_vendor_without_end_date_continues_indefinitely(self):
        """Vendor with no end_date should continue for entire projection period."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            vendor_name="AWS",
            amount=Decimal("50000.00"),
            frequency="Monthly",
            due_date=date(2026, 1, 15),
            end_date=None  # No end date - continues indefinitely
        )

        payment_dates = scheduler.get_vendor_payment_dates(
            contract,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30)
        )

        # Should have 6 payments (Jan-Jun)
        assert len(payment_dates) == 6
        assert payment_dates[0] == date(2026, 1, 15)
        assert payment_dates[-1] == date(2026, 6, 15)

    def test_vendor_with_end_date_stops_at_end_date(self):
        """Vendor with end_date should stop generating payments after that date."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            vendor_name="Contractor",
            amount=Decimal("100000.00"),
            frequency="Monthly",
            due_date=date(2026, 1, 15),
            end_date=date(2026, 3, 31)  # Contract ends March 31
        )

        payment_dates = scheduler.get_vendor_payment_dates(
            contract,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30)
        )

        # Should only have 3 payments (Jan, Feb, Mar) - not Apr, May, Jun
        assert len(payment_dates) == 3
        assert payment_dates[0] == date(2026, 1, 15)
        assert payment_dates[-1] == date(2026, 3, 15)

    def test_vendor_end_date_mid_month(self):
        """Vendor with end_date before next payment should not include that payment."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            vendor_name="Short Term Vendor",
            amount=Decimal("25000.00"),
            frequency="Monthly",
            due_date=date(2026, 1, 20),
            end_date=date(2026, 2, 15)  # Ends before Feb 20 payment
        )

        payment_dates = scheduler.get_vendor_payment_dates(
            contract,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30)
        )

        # Should only have 1 payment (Jan 20) - Feb 20 is after end_date
        assert len(payment_dates) == 1
        assert payment_dates[0] == date(2026, 1, 20)

    def test_vendor_one_time_payment_before_end_date(self):
        """One-time payment before end_date should be included."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            vendor_name="One-time Vendor",
            amount=Decimal("500000.00"),
            frequency="One-time",
            due_date=date(2026, 2, 15),
            end_date=date(2026, 3, 31)  # Ends after payment date
        )

        payment_dates = scheduler.get_vendor_payment_dates(
            contract,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30)
        )

        # Payment should be included
        assert len(payment_dates) == 1
        assert payment_dates[0] == date(2026, 2, 15)

    def test_vendor_one_time_payment_after_end_date(self):
        """One-time payment after end_date should NOT be included."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            vendor_name="One-time Vendor",
            amount=Decimal("500000.00"),
            frequency="One-time",
            due_date=date(2026, 4, 15),
            end_date=date(2026, 3, 31)  # Ends before payment date
        )

        payment_dates = scheduler.get_vendor_payment_dates(
            contract,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30)
        )

        # Payment should NOT be included (due_date > end_date)
        assert len(payment_dates) == 0

    def test_vendor_quarterly_with_end_date(self):
        """Quarterly vendor with end_date should respect the end date."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            vendor_name="Quarterly Vendor",
            amount=Decimal("150000.00"),
            frequency="Quarterly",
            due_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30)  # Ends mid-year
        )

        payment_dates = scheduler.get_vendor_payment_dates(
            contract,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )

        # Should have 2 payments (Jan 1, Apr 1) - Jul 1 is after end_date
        assert len(payment_dates) == 2
        assert payment_dates[0] == date(2026, 1, 1)
        assert payment_dates[1] == date(2026, 4, 1)

    def test_vendor_end_date_same_as_projection_end(self):
        """End_date same as projection end should work correctly."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            vendor_name="Matching End",
            amount=Decimal("50000.00"),
            frequency="Monthly",
            due_date=date(2026, 1, 15),
            end_date=date(2026, 3, 31)
        )

        payment_dates = scheduler.get_vendor_payment_dates(
            contract,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31)  # Same as contract end_date
        )

        # Should have 3 payments
        assert len(payment_dates) == 3

    def test_calculate_vendor_events_respects_end_date(self):
        """calculate_vendor_events should respect end_date."""
        scheduler = ExpenseScheduler()

        contracts = [
            MockVendorContract(
                id=1,
                vendor_name="Ongoing Vendor",
                amount=Decimal("50000.00"),
                frequency="Monthly",
                due_date=date(2026, 1, 15),
                end_date=None  # Continues indefinitely
            ),
            MockVendorContract(
                id=2,
                vendor_name="Ending Vendor",
                amount=Decimal("100000.00"),
                frequency="Monthly",
                due_date=date(2026, 1, 20),
                end_date=date(2026, 2, 28)  # Ends in Feb
            ),
        ]

        events = scheduler.calculate_vendor_events(
            contracts,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 4, 30)
        )

        # Count events per vendor
        ongoing_events = [e for e in events if e.vendor_name == "Ongoing Vendor"]
        ending_events = [e for e in events if e.vendor_name == "Ending Vendor"]

        # Ongoing should have 4 events (Jan-Apr)
        assert len(ongoing_events) == 4

        # Ending should have 2 events (Jan, Feb) - Mar and Apr are after end_date
        assert len(ending_events) == 2


class TestVendorStartAndEndDate:
    """Test start_date and end_date together."""

    def test_vendor_with_both_start_and_end_date(self):
        """Vendor with both start_date and end_date should only include payments in that range."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            vendor_name="Limited Contract",
            amount=Decimal("75000.00"),
            frequency="Monthly",
            due_date=date(2026, 1, 15),
            start_date=date(2026, 2, 1),  # Starts Feb
            end_date=date(2026, 4, 30)    # Ends Apr
        )

        payment_dates = scheduler.get_vendor_payment_dates(
            contract,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30)
        )

        # Should have 3 payments (Feb, Mar, Apr) - Jan is before start, May/Jun after end
        assert len(payment_dates) == 3
        assert payment_dates[0] == date(2026, 2, 15)
        assert payment_dates[-1] == date(2026, 4, 15)
