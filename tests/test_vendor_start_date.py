"""
Tests for vendor start_date feature.

Tests coverage:
- VendorContract model has start_date column
- start_date is nullable (backward compatible)
- Import parses start_date from Google Sheets
- Expense scheduler respects start_date
- Individual payment dates filtered by start_date
- Projections exclude vendors before their start_date
"""
import pytest
from datetime import date
from decimal import Decimal
from typing import List

from database.models import VendorContract
from projection_engine.expense_scheduler import ExpenseScheduler, ExpenseEvent


class TestVendorStartDateModel:
    """Test suite for VendorContract start_date column."""

    def test_vendor_model_has_start_date_column(self):
        """Test that VendorContract model has start_date column."""
        assert hasattr(VendorContract, 'start_date')

    def test_vendor_start_date_is_nullable(self):
        """Test that start_date column is nullable for backward compatibility."""
        start_date_column = VendorContract.__table__.columns.get('start_date')
        assert start_date_column is not None
        assert start_date_column.nullable is True, "start_date must be nullable"

    def test_vendor_start_date_is_date_type(self):
        """Test that start_date is a Date column."""
        from sqlalchemy import Date
        start_date_column = VendorContract.__table__.columns.get('start_date')
        assert start_date_column is not None
        assert isinstance(start_date_column.type, Date)

    def test_create_vendor_without_start_date(self):
        """Test creating vendor without start_date (backward compatible)."""
        vendor = VendorContract(
            vendor_name='Test Vendor',
            category='Software/Tech',
            amount=Decimal('10000.00'),
            frequency='Monthly',
            due_date=date(2026, 1, 21),
            start_date=None,  # No start date = already active
            entity='YAHSHUA',
            status='Active'
        )
        assert vendor.start_date is None

    def test_create_vendor_with_start_date(self):
        """Test creating vendor with future start_date."""
        start = date(2026, 3, 1)
        vendor = VendorContract(
            vendor_name='Future Vendor',
            category='Software/Tech',
            amount=Decimal('5000.00'),
            frequency='Monthly',
            due_date=date(2026, 3, 15),
            start_date=start,
            entity='YAHSHUA',
            status='Active'
        )
        assert vendor.start_date == start


class TestExpenseSchedulerStartDate:
    """Test suite for expense scheduler with start_date."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scheduler = ExpenseScheduler()

    def create_vendor(
        self,
        vendor_name: str,
        amount: Decimal,
        due_date: date,
        start_date: date = None,
        frequency: str = 'Monthly'
    ) -> VendorContract:
        """Helper to create vendor contract."""
        vendor = VendorContract(
            vendor_name=vendor_name,
            category='Software/Tech',
            amount=amount,
            frequency=frequency,
            due_date=due_date,
            start_date=start_date,
            entity='YAHSHUA',
            status='Active'
        )
        vendor.id = 1  # Mock ID
        return vendor

    def test_vendor_without_start_date_always_included(self):
        """Test that vendor without start_date is always included in projections."""
        # Vendor with no start_date (already active)
        vendor = self.create_vendor(
            vendor_name='Active Vendor',
            amount=Decimal('10000.00'),
            due_date=date(2026, 1, 21),
            start_date=None
        )

        # Project for January 2026
        events = self.scheduler.calculate_vendor_events(
            contracts=[vendor],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            entity='YAHSHUA'
        )

        # Should have 1 event on Jan 21
        assert len(events) == 1
        assert events[0].date == date(2026, 1, 21)
        assert events[0].amount == Decimal('10000.00')

    def test_vendor_before_start_date_excluded(self):
        """Test that vendor is excluded if projection is before start_date."""
        # Vendor starts in March
        vendor = self.create_vendor(
            vendor_name='Future Vendor',
            amount=Decimal('5000.00'),
            due_date=date(2026, 3, 15),
            start_date=date(2026, 3, 1)
        )

        # Project for January (before start_date)
        events = self.scheduler.calculate_vendor_events(
            contracts=[vendor],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            entity='YAHSHUA'
        )

        # Should have NO events (vendor not started yet)
        assert len(events) == 0

    def test_vendor_after_start_date_included(self):
        """Test that vendor is included after its start_date."""
        # Vendor starts in March
        vendor = self.create_vendor(
            vendor_name='Future Vendor',
            amount=Decimal('5000.00'),
            due_date=date(2026, 3, 15),
            start_date=date(2026, 3, 1)
        )

        # Project for March-April (after start_date)
        events = self.scheduler.calculate_vendor_events(
            contracts=[vendor],
            start_date=date(2026, 3, 1),
            end_date=date(2026, 4, 30),
            entity='YAHSHUA'
        )

        # Should have 2 events (March 15, April 15)
        assert len(events) == 2
        assert events[0].date == date(2026, 3, 15)
        assert events[1].date == date(2026, 4, 15)

    def test_payment_dates_respect_start_date(self):
        """Test that individual payment dates before start_date are filtered."""
        # Vendor with recurring payments starting March 15
        # But first payment is Feb 15 (should be skipped)
        vendor = self.create_vendor(
            vendor_name='Vendor with Past Due Date',
            amount=Decimal('8000.00'),
            due_date=date(2026, 2, 15),  # First payment in Feb
            start_date=date(2026, 3, 1),  # But vendor starts in March
            frequency='Monthly'
        )

        # Project for Feb-Apr
        events = self.scheduler.calculate_vendor_events(
            contracts=[vendor],
            start_date=date(2026, 2, 1),
            end_date=date(2026, 4, 30),
            entity='YAHSHUA'
        )

        # Feb 15 should be skipped (before start_date)
        # Only March 15 and April 15 should appear
        assert len(events) == 2
        assert events[0].date == date(2026, 3, 15)
        assert events[1].date == date(2026, 4, 15)

    def test_multiple_vendors_mixed_start_dates(self):
        """Test projection with multiple vendors having different start_dates."""
        vendors = [
            # Vendor 1: No start_date (already active)
            self.create_vendor(
                vendor_name='Existing Vendor',
                amount=Decimal('10000.00'),
                due_date=date(2026, 1, 10),
                start_date=None
            ),
            # Vendor 2: Starts in February
            self.create_vendor(
                vendor_name='Feb Vendor',
                amount=Decimal('5000.00'),
                due_date=date(2026, 2, 15),
                start_date=date(2026, 2, 1)
            ),
            # Vendor 3: Starts in March
            self.create_vendor(
                vendor_name='Mar Vendor',
                amount=Decimal('3000.00'),
                due_date=date(2026, 3, 20),
                start_date=date(2026, 3, 1)
            ),
        ]

        # Assign different IDs
        for idx, vendor in enumerate(vendors, start=1):
            vendor.id = idx

        # Project for January-March
        events = self.scheduler.calculate_vendor_events(
            contracts=vendors,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            entity='YAHSHUA'
        )

        # Expected:
        # Jan: Vendor 1 (Jan 10)
        # Feb: Vendor 1 (Feb 10), Vendor 2 (Feb 15)
        # Mar: Vendor 1 (Mar 10), Vendor 2 (Mar 15), Vendor 3 (Mar 20)
        # Total: 6 events

        assert len(events) == 6

        # Verify January has only Vendor 1
        jan_events = [e for e in events if e.date.month == 1]
        assert len(jan_events) == 1
        assert jan_events[0].vendor_name == 'Existing Vendor'

        # Verify February has Vendors 1 and 2
        feb_events = [e for e in events if e.date.month == 2]
        assert len(feb_events) == 2
        vendor_names = {e.vendor_name for e in feb_events}
        assert vendor_names == {'Existing Vendor', 'Feb Vendor'}

        # Verify March has all 3 vendors
        mar_events = [e for e in events if e.date.month == 3]
        assert len(mar_events) == 3
        vendor_names = {e.vendor_name for e in mar_events}
        assert vendor_names == {'Existing Vendor', 'Feb Vendor', 'Mar Vendor'}

    def test_vendor_start_date_on_projection_start(self):
        """Test vendor with start_date exactly on projection start date."""
        vendor = self.create_vendor(
            vendor_name='Start on Day 1',
            amount=Decimal('7000.00'),
            due_date=date(2026, 1, 15),
            start_date=date(2026, 1, 1)  # Starts exactly on projection start
        )

        events = self.scheduler.calculate_vendor_events(
            contracts=[vendor],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            entity='YAHSHUA'
        )

        # Should include payment on Jan 15
        assert len(events) == 1
        assert events[0].date == date(2026, 1, 15)

    def test_vendor_start_date_in_past(self):
        """Test vendor with start_date in the past (already started)."""
        vendor = self.create_vendor(
            vendor_name='Started Last Year',
            amount=Decimal('12000.00'),
            due_date=date(2025, 12, 10),
            start_date=date(2025, 1, 1),  # Started in 2025
            frequency='Monthly'
        )

        # Project for Jan 2026
        events = self.scheduler.calculate_vendor_events(
            contracts=[vendor],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            entity='YAHSHUA'
        )

        # Should include payment (start_date is in past)
        assert len(events) == 1
        assert events[0].date == date(2026, 1, 10)

    def test_one_time_vendor_before_start_date(self):
        """Test one-time vendor payment before its start_date is excluded."""
        vendor = self.create_vendor(
            vendor_name='One-time Future Vendor',
            amount=Decimal('50000.00'),
            due_date=date(2026, 5, 15),  # Payment in May
            start_date=date(2026, 5, 1),  # Starts in May
            frequency='One-time'
        )

        # Project for April (before start_date)
        events = self.scheduler.calculate_vendor_events(
            contracts=[vendor],
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
            entity='YAHSHUA'
        )

        # Should have NO events
        assert len(events) == 0

    def test_one_time_vendor_after_start_date(self):
        """Test one-time vendor payment after its start_date is included."""
        vendor = self.create_vendor(
            vendor_name='One-time Future Vendor',
            amount=Decimal('50000.00'),
            due_date=date(2026, 5, 15),
            start_date=date(2026, 5, 1),
            frequency='One-time'
        )

        # Project for May (includes start_date)
        events = self.scheduler.calculate_vendor_events(
            contracts=[vendor],
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 31),
            entity='YAHSHUA'
        )

        # Should have 1 event on May 15
        assert len(events) == 1
        assert events[0].date == date(2026, 5, 15)


class TestBackwardCompatibility:
    """Test suite for backward compatibility with existing vendors."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scheduler = ExpenseScheduler()

    def test_existing_vendors_without_start_date_work(self):
        """Test that existing vendors (start_date = None) continue to work."""
        vendor = VendorContract(
            vendor_name='Legacy Vendor',
            category='Software/Tech',
            amount=Decimal('15000.00'),
            frequency='Monthly',
            due_date=date(2026, 1, 5),
            start_date=None,  # No start date = already active
            entity='YAHSHUA',
            status='Active'
        )
        vendor.id = 1

        events = self.scheduler.calculate_vendor_events(
            contracts=[vendor],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            entity='YAHSHUA'
        )

        # Should have 3 monthly payments (Jan, Feb, Mar)
        assert len(events) == 3
        assert events[0].date == date(2026, 1, 5)
        assert events[1].date == date(2026, 2, 5)
        assert events[2].date == date(2026, 3, 5)
