"""
Business constants for JESUS Company Cash Management System.
Centralized constants to ensure consistency across the application.
"""
from decimal import Decimal

# ═══════════════════════════════════════════════════════════════════
# PAYMENT PLANS
# ═══════════════════════════════════════════════════════════════════
PAYMENT_PLAN_FREQUENCIES = {
    "Monthly": 1,  # Every month
    "Quarterly": 3,  # Every 3 months
    "Bi-annually": 6,  # Every 6 months
    "Annual": 12,  # Every 12 months
    "More than 1 year": 12,  # Treat as annual for projection purposes
}

VALID_PAYMENT_PLANS = list(PAYMENT_PLAN_FREQUENCIES.keys())

# ═══════════════════════════════════════════════════════════════════
# VENDOR EXPENSE FREQUENCIES
# ═══════════════════════════════════════════════════════════════════
EXPENSE_FREQUENCIES = {
    "One-time": None,  # One-time payment
    "Daily": 1,  # Every day
    "Weekly": 7,  # Every 7 days
    "Bi-weekly": 14,  # Every 14 days
    "Monthly": 30,  # Every 30 days (approximate)
    "Quarterly": 90,  # Every 90 days (approximate)
    "Annual": 365,  # Every 365 days
}

VALID_EXPENSE_FREQUENCIES = list(EXPENSE_FREQUENCIES.keys())

# ═══════════════════════════════════════════════════════════════════
# EXPENSE CATEGORIES
# ═══════════════════════════════════════════════════════════════════
EXPENSE_CATEGORIES = {
    "Payroll": {
        "priority": 1,
        "flexibility_days": 0,
        "description": "Employee salaries and benefits"
    },
    "Loans": {
        "priority": 2,
        "flexibility_days": 2,
        "description": "Loan amortization and interest"
    },
    "Software/Tech": {
        "priority": 3,
        "flexibility_days": 7,
        "description": "SaaS, AWS, Google Workspace, etc."
    },
    "Operations": {
        "priority": 4,
        "flexibility_days": 14,
        "description": "Rent, utilities, supplies, meals, fuel"
    },
    "Rent": {
        "priority": 4,
        "flexibility_days": 5,
        "description": "Office rent"
    },
    "Utilities": {
        "priority": 4,
        "flexibility_days": 10,
        "description": "Electricity, water, internet"
    }
}

VALID_EXPENSE_CATEGORIES = list(EXPENSE_CATEGORIES.keys())

# ═══════════════════════════════════════════════════════════════════
# CONTRACT STATUSES
# ═══════════════════════════════════════════════════════════════════
VALID_CONTRACT_STATUSES = ["Active", "Inactive", "Pending", "Cancelled"]

# ═══════════════════════════════════════════════════════════════════
# SCENARIO CHANGE TYPES
# ═══════════════════════════════════════════════════════════════════
VALID_SCENARIO_CHANGE_TYPES = [
    "hiring",           # Add employees
    "expense",          # Add recurring expense
    "revenue",          # Add new clients
    "customer_loss",    # Lose existing revenue
    "investment"        # One-time cash outflow
]

# ═══════════════════════════════════════════════════════════════════
# PROJECTION TIMEFRAMES
# ═══════════════════════════════════════════════════════════════════
VALID_TIMEFRAMES = ["daily", "weekly", "monthly", "quarterly"]

# ═══════════════════════════════════════════════════════════════════
# SCENARIO TYPES
# ═══════════════════════════════════════════════════════════════════
VALID_SCENARIO_TYPES = ["optimistic", "realistic"]

# ═══════════════════════════════════════════════════════════════════
# DECIMAL PRECISION
# ═══════════════════════════════════════════════════════════════════
DECIMAL_PLACES = Decimal("0.01")  # 2 decimal places for currency

# ═══════════════════════════════════════════════════════════════════
# PROJECTION DEFAULTS
# ═══════════════════════════════════════════════════════════════════
DEFAULT_PROJECTION_MONTHS = 12  # 12-month default projection
MAX_PROJECTION_MONTHS = 36  # Maximum 3-year projection

