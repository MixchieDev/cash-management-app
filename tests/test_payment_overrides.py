"""
Tests for payment override functionality.
Ensures overrides correctly move or skip payments in projections.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from projection_engine.revenue_calculator import RevenueCalculator
from projection_engine.expense_scheduler import ExpenseScheduler


class MockCustomerContract:
    """Mock customer contract for testing."""
    def __init__(
        self,
        id: int,
        company_name: str,
        monthly_fee: Decimal,
        payment_plan: str = 'Monthly',
        contract_start: date = date(2026, 1, 1),
        contract_end: date = None,
        entity: str = 'YAHSHUA',
        status: str = 'Active',
        payment_terms_days: int = 30
    ):
        self.id = id
        self.company_name = company_name
        self.monthly_fee = monthly_fee
        self.payment_plan = payment_plan
        self.contract_start = contract_start
        self.contract_end = contract_end
        self.entity = entity
        self.status = status
        self.payment_terms_days = payment_terms_days


class MockVendorContract:
    """Mock vendor contract for testing."""
    def __init__(
        self,
        id: int,
        vendor_name: str,
        amount: Decimal,
        frequency: str = 'Monthly',
        due_date: date = date(2026, 1, 15),
        entity: str = 'YAHSHUA',
        category: str = 'Operations',
        priority: int = 3,
        status: str = 'Active',
        start_date: date = None,
        end_date: date = None
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


class TestCustomerPaymentOverrides:
    """Test payment overrides for customer payments."""

    def test_move_customer_payment_to_new_date(self):
        """Override should move customer payment to new date."""
        revenue_calc = RevenueCalculator(scenario_type='realistic')

        contract = MockCustomerContract(
            id=1,
            company_name="ACME Corp",
            monthly_fee=Decimal("100000.00"),
            payment_plan='Monthly',
            contract_start=date(2026, 1, 1)
        )

        # Calculate the original payment date for February billing
        # Invoice: Jan 15, Payment: Feb 14 + 10 days delay = Feb 24 (realistic)
        original_date = date(2026, 2, 24)
        new_date = date(2026, 3, 5)

        # Create override to move payment
        overrides = [{
            'override_type': 'customer',
            'contract_id': 1,
            'original_date': original_date,
            'new_date': new_date,
            'action': 'move',
            'entity': 'YAHSHUA'
        }]

        events = revenue_calc.calculate_revenue_events(
            [contract],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            payment_overrides=overrides
        )

        # Check that original date has no payment
        original_payments = [e for e in events if e.date == original_date]
        assert len(original_payments) == 0, f"Should have no payment on original date {original_date}"

        # Check that new date has the payment
        new_payments = [e for e in events if e.date == new_date]
        assert len(new_payments) == 1, f"Should have payment on new date {new_date}"
        assert new_payments[0].amount == Decimal("100000.00")

    def test_skip_customer_payment(self):
        """Override with action='skip' should exclude payment entirely."""
        revenue_calc = RevenueCalculator(scenario_type='realistic')

        contract = MockCustomerContract(
            id=1,
            company_name="ACME Corp",
            monthly_fee=Decimal("100000.00"),
            payment_plan='Monthly',
            contract_start=date(2026, 1, 1)
        )

        # Skip February payment
        skip_date = date(2026, 2, 24)

        overrides = [{
            'override_type': 'customer',
            'contract_id': 1,
            'original_date': skip_date,
            'new_date': None,
            'action': 'skip',
            'entity': 'YAHSHUA'
        }]

        events = revenue_calc.calculate_revenue_events(
            [contract],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            payment_overrides=overrides
        )

        # Should have 2 payments (Jan and Mar), not 3
        assert len(events) == 2, f"Should have 2 payments after skipping, got {len(events)}"

        # Check skipped date has no payment
        skipped_payments = [e for e in events if e.date == skip_date]
        assert len(skipped_payments) == 0, "Skipped payment should not appear"

    def test_no_override_does_not_affect_payments(self):
        """Without overrides, payments should be unchanged."""
        revenue_calc = RevenueCalculator(scenario_type='realistic')

        contract = MockCustomerContract(
            id=1,
            company_name="ACME Corp",
            monthly_fee=Decimal("100000.00"),
            payment_plan='Monthly',
            contract_start=date(2026, 1, 1)
        )

        # No overrides
        events_without = revenue_calc.calculate_revenue_events(
            [contract],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            payment_overrides=None
        )

        events_with_empty = revenue_calc.calculate_revenue_events(
            [contract],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            payment_overrides=[]
        )

        # Both should produce same number of events
        assert len(events_without) == len(events_with_empty)
        assert len(events_without) == 3  # Jan, Feb, Mar


class TestVendorPaymentOverrides:
    """Test payment overrides for vendor payments."""

    def test_move_vendor_payment_to_new_date(self):
        """Override should move vendor payment to new date."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            id=1,
            vendor_name="AWS",
            amount=Decimal("50000.00"),
            frequency='Monthly',
            due_date=date(2026, 1, 15)
        )

        original_date = date(2026, 2, 15)
        new_date = date(2026, 2, 25)

        overrides = [{
            'override_type': 'vendor',
            'contract_id': 1,
            'original_date': original_date,
            'new_date': new_date,
            'action': 'move',
            'entity': 'YAHSHUA'
        }]

        events = scheduler.calculate_vendor_events(
            [contract],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            entity='YAHSHUA',
            payment_overrides=overrides
        )

        # Check original date has no payment
        original_payments = [e for e in events if e.date == original_date]
        assert len(original_payments) == 0

        # Check new date has the payment
        new_payments = [e for e in events if e.date == new_date]
        assert len(new_payments) == 1
        assert new_payments[0].amount == Decimal("50000.00")

    def test_skip_vendor_payment(self):
        """Override with action='skip' should exclude vendor payment."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            id=1,
            vendor_name="AWS",
            amount=Decimal("50000.00"),
            frequency='Monthly',
            due_date=date(2026, 1, 15)
        )

        skip_date = date(2026, 2, 15)

        overrides = [{
            'override_type': 'vendor',
            'contract_id': 1,
            'original_date': skip_date,
            'new_date': None,
            'action': 'skip',
            'entity': 'YAHSHUA'
        }]

        events = scheduler.calculate_vendor_events(
            [contract],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            entity='YAHSHUA',
            payment_overrides=overrides
        )

        # Should have 2 payments (Jan 15 and Mar 15), not 3
        assert len(events) == 2

        # Check skipped date has no payment
        skipped_payments = [e for e in events if e.date == skip_date]
        assert len(skipped_payments) == 0

    def test_override_only_affects_specified_vendor(self):
        """Override for one vendor should not affect other vendors."""
        scheduler = ExpenseScheduler()

        contract1 = MockVendorContract(
            id=1,
            vendor_name="AWS",
            amount=Decimal("50000.00"),
            frequency='Monthly',
            due_date=date(2026, 1, 15)
        )

        contract2 = MockVendorContract(
            id=2,
            vendor_name="Google",
            amount=Decimal("30000.00"),
            frequency='Monthly',
            due_date=date(2026, 1, 15)
        )

        # Skip AWS Feb payment only
        overrides = [{
            'override_type': 'vendor',
            'contract_id': 1,  # Only AWS
            'original_date': date(2026, 2, 15),
            'new_date': None,
            'action': 'skip',
            'entity': 'YAHSHUA'
        }]

        events = scheduler.calculate_vendor_events(
            [contract1, contract2],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            entity='YAHSHUA',
            payment_overrides=overrides
        )

        # AWS should have 2 payments
        aws_events = [e for e in events if e.vendor_name == "AWS"]
        assert len(aws_events) == 2

        # Google should still have 3 payments
        google_events = [e for e in events if e.vendor_name == "Google"]
        assert len(google_events) == 3


class TestMultipleOverrides:
    """Test multiple overrides on same contract."""

    def test_multiple_overrides_same_vendor(self):
        """Multiple overrides for different dates on same vendor."""
        scheduler = ExpenseScheduler()

        contract = MockVendorContract(
            id=1,
            vendor_name="AWS",
            amount=Decimal("50000.00"),
            frequency='Monthly',
            due_date=date(2026, 1, 15)
        )

        # Skip Jan, move Feb
        overrides = [
            {
                'override_type': 'vendor',
                'contract_id': 1,
                'original_date': date(2026, 1, 15),
                'new_date': None,
                'action': 'skip',
                'entity': 'YAHSHUA'
            },
            {
                'override_type': 'vendor',
                'contract_id': 1,
                'original_date': date(2026, 2, 15),
                'new_date': date(2026, 2, 28),
                'action': 'move',
                'entity': 'YAHSHUA'
            }
        ]

        events = scheduler.calculate_vendor_events(
            [contract],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            entity='YAHSHUA',
            payment_overrides=overrides
        )

        # Should have 2 payments: Feb 28 (moved) and Mar 15 (unchanged)
        assert len(events) == 2

        event_dates = [e.date for e in events]
        assert date(2026, 1, 15) not in event_dates  # Skipped
        assert date(2026, 2, 15) not in event_dates  # Original moved
        assert date(2026, 2, 28) in event_dates      # New date
        assert date(2026, 3, 15) in event_dates      # Unchanged
