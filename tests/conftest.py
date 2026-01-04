"""
Pytest configuration and shared fixtures for testing.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import Base, CustomerContract, VendorContract, BankBalance
from database.db_manager import db_manager


@pytest.fixture
def test_db():
    """
    Create an in-memory test database for each test.

    Yields:
        DatabaseManager instance with fresh schema
    """
    # Use in-memory SQLite database for tests
    test_db_manager = db_manager
    test_db_manager.db_path = ':memory:'

    # Initialize schema
    test_db_manager.initialize_database()

    yield test_db_manager

    # Cleanup
    test_db_manager.close()


@pytest.fixture
def sample_customer_data():
    """
    Sample customer contract data for testing.

    Returns:
        Dictionary with customer contract fields
    """
    return {
        'company_name': 'Test Company Inc.',
        'monthly_fee': Decimal('50000.00'),
        'payment_plan': 'Monthly',
        'contract_start': date(2026, 1, 1),
        'contract_end': None,
        'status': 'Active',
        'who_acquired': 'YOWI',
        'entity': 'YAHSHUA',
        'invoice_day': 15,
        'payment_terms_days': 30,
        'reliability_score': Decimal('0.80'),
        'notes': 'Test customer'
    }


@pytest.fixture
def sample_vendor_data():
    """
    Sample vendor contract data for testing.

    Returns:
        Dictionary with vendor contract fields
    """
    return {
        'vendor_name': 'Test Vendor LLC',
        'category': 'Software/Tech',
        'amount': Decimal('10000.00'),
        'frequency': 'Monthly',
        'due_date': date(2026, 1, 21),
        'start_date': None,  # No start date = already active
        'entity': 'YAHSHUA',
        'priority': 3,
        'flexibility_days': 5,
        'status': 'Active',
        'notes': 'Test vendor'
    }


@pytest.fixture
def sample_vendor_with_future_start():
    """
    Sample vendor with future start date for testing.

    Returns:
        Dictionary with vendor contract fields including future start_date
    """
    return {
        'vendor_name': 'Future Vendor Inc.',
        'category': 'Software/Tech',
        'amount': Decimal('5000.00'),
        'frequency': 'Monthly',
        'due_date': date(2026, 3, 15),
        'start_date': date(2026, 3, 1),  # Starts in March
        'entity': 'YAHSHUA',
        'priority': 3,
        'flexibility_days': 0,
        'status': 'Active',
        'notes': 'Starts in the future'
    }


@pytest.fixture
def sample_bank_balance():
    """
    Sample bank balance data for testing.

    Returns:
        Dictionary with bank balance fields
    """
    return {
        'balance_date': date(2026, 1, 1),
        'entity': 'YAHSHUA',
        'balance': Decimal('5000000.00'),
        'source': 'Manual Entry',
        'notes': 'Test balance'
    }
