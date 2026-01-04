"""
Tests for period helper functions.
"""
import pytest
from datetime import date

from utils.period_helpers import calculate_period_range, get_period_description


def test_daily_period_range():
    """Daily period should be single day."""
    start, end, label = calculate_period_range(
        clicked_date=date(2026, 1, 15),
        timeframe='daily',
        projection_start=date(2026, 1, 1)
    )

    assert start == date(2026, 1, 15)
    assert end == date(2026, 1, 15)
    assert label == 'Jan 15, 2026'


def test_weekly_period_range():
    """Weekly period should be 7 days ending on clicked date."""
    start, end, label = calculate_period_range(
        clicked_date=date(2026, 1, 18),  # Saturday
        timeframe='weekly',
        projection_start=date(2026, 1, 1)
    )

    assert end == date(2026, 1, 18)
    assert start == date(2026, 1, 12)  # 6 days earlier
    assert 'Week of Jan 12-18' in label


def test_weekly_period_boundary():
    """Weekly period should adjust to not go before projection start."""
    start, end, label = calculate_period_range(
        clicked_date=date(2026, 1, 3),  # 3rd day of month
        timeframe='weekly',
        projection_start=date(2026, 1, 1)
    )

    assert end == date(2026, 1, 3)
    # Should be capped at projection start, not go to Dec 28
    assert start == date(2026, 1, 1)


def test_monthly_period_range():
    """Monthly period should be full month."""
    start, end, label = calculate_period_range(
        clicked_date=date(2026, 1, 31),
        timeframe='monthly',
        projection_start=date(2026, 1, 1)
    )

    assert start == date(2026, 1, 1)
    assert end == date(2026, 1, 31)
    assert label == 'January 2026'


def test_quarterly_period_range():
    """Quarterly period should be 3 months."""
    start, end, label = calculate_period_range(
        clicked_date=date(2026, 3, 31),
        timeframe='quarterly',
        projection_start=date(2026, 1, 1)
    )

    assert start == date(2026, 1, 1)
    assert end == date(2026, 3, 31)
    assert label == 'Q1 2026'


def test_quarterly_period_q2():
    """Q2 should be labeled correctly."""
    start, end, label = calculate_period_range(
        clicked_date=date(2026, 6, 30),
        timeframe='quarterly',
        projection_start=date(2026, 1, 1)
    )

    assert 'Q2 2026' in label


def test_get_period_description_single_day():
    """Single day period description."""
    desc = get_period_description(date(2026, 1, 15), date(2026, 1, 15))

    assert desc == 'Jan 15, 2026'


def test_get_period_description_same_month():
    """Period within same month."""
    desc = get_period_description(date(2026, 1, 12), date(2026, 1, 18))

    assert 'Jan 12-18, 2026' in desc


def test_get_period_description_cross_month():
    """Period spanning multiple months."""
    desc = get_period_description(date(2026, 1, 25), date(2026, 2, 5))

    assert 'Jan 25' in desc
    assert 'Feb 05' in desc


def test_invalid_timeframe():
    """Should raise error for invalid timeframe."""
    with pytest.raises(ValueError, match="Invalid timeframe"):
        calculate_period_range(
            clicked_date=date(2026, 1, 15),
            timeframe='invalid',
            projection_start=date(2026, 1, 1)
        )
