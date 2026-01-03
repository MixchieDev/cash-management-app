"""
Currency formatting utilities for JESUS Company Cash Management System.
ALL currency displays MUST use these functions to ensure consistency.

Format: ₱X,XXX.XX (Philippine Peso with comma separators and 2 decimals)
"""
from decimal import Decimal
from typing import Union
from config.settings import (
    CURRENCY_SYMBOL,
    CURRENCY_DECIMAL_PLACES,
    CURRENCY_THOUSANDS_SEPARATOR
)


def format_currency(amount: Union[Decimal, float, int]) -> str:
    """
    Format amount as Philippine Peso currency.

    Args:
        amount: Numeric amount to format

    Returns:
        Formatted string: ₱X,XXX.XX

    Examples:
        >>> format_currency(Decimal('2500000'))
        '₱2,500,000.00'
        >>> format_currency(0)
        '₱0.00'
        >>> format_currency(Decimal('-150000.50'))
        '-₱150,000.50'
        >>> format_currency(1234567.89)
        '₱1,234,567.89'
    """
    # Convert to Decimal for precision
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    # Round to 2 decimal places
    amount = amount.quantize(Decimal('0.01'))

    # Handle negative amounts
    is_negative = amount < 0
    abs_amount = abs(amount)

    # Format with comma separators
    # Split into integer and decimal parts
    str_amount = f"{abs_amount:.2f}"
    integer_part, decimal_part = str_amount.split('.')

    # Add thousands separators
    formatted_integer = f"{int(integer_part):,}"

    # Combine with currency symbol
    formatted = f"{CURRENCY_SYMBOL}{formatted_integer}.{decimal_part}"

    # Add negative sign if needed
    if is_negative:
        formatted = f"-{formatted}"

    return formatted


def parse_currency(formatted_amount: str) -> Decimal:
    """
    Parse formatted currency string back to Decimal.

    Args:
        formatted_amount: Formatted currency string (₱X,XXX.XX)

    Returns:
        Decimal amount

    Examples:
        >>> parse_currency('₱2,500,000.00')
        Decimal('2500000.00')
        >>> parse_currency('-₱150,000.50')
        Decimal('-150000.50')
    """
    # Remove currency symbol, commas, and whitespace
    cleaned = formatted_amount.replace(CURRENCY_SYMBOL, '').replace(',', '').strip()

    # Convert to Decimal
    return Decimal(cleaned)


def format_currency_compact(amount: Union[Decimal, float, int]) -> str:
    """
    Format large amounts in compact form (K, M, B).

    Args:
        amount: Numeric amount to format

    Returns:
        Compact formatted string: ₱X.XXM

    Examples:
        >>> format_currency_compact(Decimal('2500000'))
        '₱2.50M'
        >>> format_currency_compact(50000)
        '₱50.00K'
        >>> format_currency_compact(1500000000)
        '₱1.50B'
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    is_negative = amount < 0
    abs_amount = abs(amount)

    if abs_amount >= Decimal('1000000000'):  # Billions
        value = abs_amount / Decimal('1000000000')
        suffix = 'B'
    elif abs_amount >= Decimal('1000000'):  # Millions
        value = abs_amount / Decimal('1000000')
        suffix = 'M'
    elif abs_amount >= Decimal('1000'):  # Thousands
        value = abs_amount / Decimal('1000')
        suffix = 'K'
    else:
        return format_currency(amount)

    formatted = f"{CURRENCY_SYMBOL}{value:.2f}{suffix}"

    if is_negative:
        formatted = f"-{formatted}"

    return formatted


def validate_currency_format(formatted_amount: str) -> bool:
    """
    Validate that a string is properly formatted as currency.

    Args:
        formatted_amount: String to validate

    Returns:
        True if properly formatted, False otherwise

    Examples:
        >>> validate_currency_format('₱2,500,000.00')
        True
        >>> validate_currency_format('2500000')
        False
        >>> validate_currency_format('₱2,500,000')
        False
    """
    import re

    # Pattern: Optional negative sign, ₱, digits with commas, period, 2 decimal places
    pattern = r'^-?₱\d{1,3}(,\d{3})*\.\d{2}$'

    return bool(re.match(pattern, formatted_amount))
