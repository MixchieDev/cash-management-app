"""
Tests for detailed projection functionality.
"""
import pytest
from datetime import date
from decimal import Decimal

from projection_engine.cash_projector import CashProjector, ProjectionResult


def test_projection_result_structure():
    """ProjectionResult should contain data_points and events."""
    projector = CashProjector()
    result = projector.calculate_cash_projection_detailed(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        entity='YAHSHUA',
        timeframe='monthly',
        scenario_type='realistic'
    )

    assert isinstance(result, ProjectionResult)
    assert hasattr(result, 'data_points')
    assert hasattr(result, 'revenue_events')
    assert hasattr(result, 'expense_events')
    assert len(result.data_points) == 3  # Jan, Feb, Mar


def test_get_events_for_period():
    """Should filter events correctly by period."""
    projector = CashProjector()
    result = projector.calculate_cash_projection_detailed(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        entity='YAHSHUA',
        timeframe='daily',
        scenario_type='realistic'
    )

    # Get events for January only
    revenue, expenses = result.get_events_for_period(
        date(2026, 1, 1), date(2026, 1, 31)
    )

    # All events should be in January
    for event in revenue:
        assert date(2026, 1, 1) <= event.date <= date(2026, 1, 31)

    for event in expenses:
        assert date(2026, 1, 1) <= event.date <= date(2026, 1, 31)


def test_get_events_for_date():
    """Should filter events for a specific date."""
    projector = CashProjector()
    result = projector.calculate_cash_projection_detailed(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        entity='YAHSHUA',
        timeframe='daily',
        scenario_type='realistic'
    )

    # Get events for specific date
    revenue, expenses = result.get_events_for_date(date(2026, 1, 15))

    # All events should be on Jan 15
    for event in revenue:
        assert event.date == date(2026, 1, 15)

    for event in expenses:
        assert event.date == date(2026, 1, 15)


def test_consolidated_events_merged():
    """Consolidated projection should merge events from both entities."""
    projector = CashProjector()
    result = projector.calculate_cash_projection_detailed(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        entity='Consolidated',
        timeframe='monthly',
        scenario_type='realistic'
    )

    # Should have events from both YAHSHUA and ABBA
    yahshua_revenue = [e for e in result.revenue_events if e.entity == 'YAHSHUA']
    abba_revenue = [e for e in result.revenue_events if e.entity == 'ABBA']

    assert len(yahshua_revenue) > 0, "Should have YAHSHUA revenue events"
    assert len(abba_revenue) > 0, "Should have ABBA revenue events"


def test_event_totals_match_aggregated():
    """Sum of event amounts should match aggregated inflows/outflows."""
    projector = CashProjector()
    result = projector.calculate_cash_projection_detailed(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        entity='YAHSHUA',
        timeframe='monthly',
        scenario_type='realistic'
    )

    # Get January data point
    jan_point = result.data_points[0]

    # Get January events
    revenue, expenses = result.get_events_for_period(
        date(2026, 1, 1), date(2026, 1, 31)
    )

    # Sum events
    total_revenue = sum(e.amount for e in revenue)
    total_expenses = sum(e.amount for e in expenses)

    # Should match aggregated amounts
    assert total_revenue == jan_point.inflows, \
        f"Revenue events total {total_revenue} != aggregated {jan_point.inflows}"
    assert total_expenses == jan_point.outflows, \
        f"Expense events total {total_expenses} != aggregated {jan_point.outflows}"


def test_detailed_projection_non_breaking():
    """Existing calculate_cash_projection() should still work (non-breaking)."""
    projector = CashProjector()

    # Old method should still work
    old_result = projector.calculate_cash_projection(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        entity='YAHSHUA',
        timeframe='monthly',
        scenario_type='realistic'
    )

    # New method should work
    new_result = projector.calculate_cash_projection_detailed(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        entity='YAHSHUA',
        timeframe='monthly',
        scenario_type='realistic'
    )

    # Data points should match
    assert len(old_result) == len(new_result.data_points)

    for old_point, new_point in zip(old_result, new_result.data_points):
        assert old_point.date == new_point.date
        assert old_point.inflows == new_point.inflows
        assert old_point.outflows == new_point.outflows
        assert old_point.ending_cash == new_point.ending_cash
