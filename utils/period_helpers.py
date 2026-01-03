"""
Helper functions for calculating period ranges from aggregated data points.
Used for mapping clicked chart points to event date ranges.
"""
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Tuple


def calculate_period_range(
    clicked_date: date,
    timeframe: str,
    projection_start: date
) -> Tuple[date, date, str]:
    """
    Calculate the date range for a clicked period.

    Args:
        clicked_date: The date from the clicked data point (period END date)
        timeframe: 'daily', 'weekly', 'monthly', or 'quarterly'
        projection_start: The projection start date (needed for calculating period start)

    Returns:
        Tuple of (period_start, period_end, period_label)

    Examples:
        >>> # Daily click on Jan 15, 2026
        >>> calculate_period_range(date(2026, 1, 15), 'daily', date(2026, 1, 1))
        (date(2026, 1, 15), date(2026, 1, 15), 'Jan 15, 2026')

        >>> # Weekly click on Jan 18, 2026 (end of week Jan 12-18)
        >>> calculate_period_range(date(2026, 1, 18), 'weekly', date(2026, 1, 1))
        (date(2026, 1, 12), date(2026, 1, 18), 'Week of Jan 12-18, 2026')

        >>> # Monthly click on Jan 31, 2026 (end of January)
        >>> calculate_period_range(date(2026, 1, 31), 'monthly', date(2026, 1, 1))
        (date(2026, 1, 1), date(2026, 1, 31), 'January 2026')
    """
    if timeframe == 'daily':
        # For daily, clicked date is both start and end
        period_start = clicked_date
        period_end = clicked_date
        period_label = clicked_date.strftime('%b %d, %Y')

    elif timeframe == 'weekly':
        # Week ends on clicked_date, so calculate 6 days back
        period_end = clicked_date
        period_start = clicked_date - timedelta(days=6)

        # Adjust if period_start is before projection start
        period_start = max(period_start, projection_start)

        period_label = f"Week of {period_start.strftime('%b %d')}-{period_end.strftime('%d, %Y')}"

    elif timeframe == 'monthly':
        # Month ends on clicked_date, start is 1st of that month
        period_end = clicked_date
        period_start = date(clicked_date.year, clicked_date.month, 1)
        period_label = clicked_date.strftime('%B %Y')

    elif timeframe == 'quarterly':
        # Quarter ends on clicked_date, start is 3 months back
        period_end = clicked_date
        period_start = clicked_date - relativedelta(months=3) + timedelta(days=1)

        # Adjust if period_start is before projection start
        period_start = max(period_start, projection_start)

        # Determine quarter
        quarter = (clicked_date.month - 1) // 3 + 1
        period_label = f"Q{quarter} {clicked_date.year}"

    else:
        raise ValueError(f"Invalid timeframe: {timeframe}")

    return period_start, period_end, period_label


def get_period_description(period_start: date, period_end: date) -> str:
    """
    Get human-readable description of a period.

    Args:
        period_start: Period start date
        period_end: Period end date

    Returns:
        Description string

    Examples:
        >>> get_period_description(date(2026, 1, 15), date(2026, 1, 15))
        'Jan 15, 2026'

        >>> get_period_description(date(2026, 1, 12), date(2026, 1, 18))
        'Jan 12-18, 2026'
    """
    if period_start == period_end:
        return period_start.strftime('%b %d, %Y')
    elif period_start.month == period_end.month:
        return f"{period_start.strftime('%b %d')}-{period_end.strftime('%d, %Y')}"
    else:
        return f"{period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}"
