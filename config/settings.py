"""
Configuration settings for JESUS Company Cash Management System.
Loads environment variables and provides application-wide settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ═══════════════════════════════════════════════════════════════════
# PROJECT PATHS
# ═══════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Determine writable database directory
_default_db_dir = PROJECT_ROOT / "database"
_tmp_db_dir = Path("/tmp/cash_management_db")
_default_db_file = _default_db_dir / "jesus_cash_management.db"

def _can_write_to_db() -> bool:
    """Check if we can actually write to the database file."""
    try:
        # If db file exists, check if we can open it for writing
        if _default_db_file.exists():
            with open(_default_db_file, 'a') as f:
                pass  # Just try to open for append
            return True
        else:
            # File doesn't exist, check if we can create in directory
            _default_db_dir.mkdir(exist_ok=True)
            test_file = _default_db_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            return True
    except (OSError, PermissionError, IOError):
        return False

# Multiple detection methods for cloud environment
_is_cloud = (
    os.path.exists("/mount/src") or  # Streamlit Cloud mount point
    os.getenv("HOME") == "/home/appuser" or  # Streamlit Cloud home
    not _can_write_to_db()  # Can't write = must use /tmp
)

if _is_cloud:
    # Cloud environment: use /tmp for writable database
    DATABASE_DIR = _tmp_db_dir
    DATABASE_DIR.mkdir(exist_ok=True)
    print(f"[DB] Using cloud database path: {DATABASE_DIR}")
else:
    DATABASE_DIR = _default_db_dir
    print(f"[DB] Using local database path: {DATABASE_DIR}")

# Create other directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR]:
    try:
        directory.mkdir(exist_ok=True)
    except OSError:
        pass  # Directory may be read-only on cloud deployments

# ═══════════════════════════════════════════════════════════════════
# DATABASE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATABASE_DIR}/jesus_cash_management.db"
)

# ═══════════════════════════════════════════════════════════════════
# GOOGLE SHEETS CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
GOOGLE_SHEETS_CREDS_PATH = os.getenv(
    "GOOGLE_SHEETS_CREDS_PATH",
    str(PROJECT_ROOT / "credentials" / "google_sheets_credentials.json")
)

# Extract spreadsheet ID from URL in google_sheets_config.py
from config.google_sheets_config import SHEETS_URL

def extract_spreadsheet_id(url: str) -> str:
    """Extract spreadsheet ID from Google Sheets URL."""
    # Format: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit...
    try:
        return url.split("/d/")[1].split("/")[0]
    except (IndexError, AttributeError):
        raise ValueError(f"Invalid Google Sheets URL: {url}")

SPREADSHEET_ID = extract_spreadsheet_id(SHEETS_URL)

# ═══════════════════════════════════════════════════════════════════
# BUSINESS RULES CONSTANTS
# ═══════════════════════════════════════════════════════════════════
# Invoice timing
INVOICE_DAYS_BEFORE_MONTH = 15  # Invoice 15 days before 1st of month

# Payment terms
DEFAULT_PAYMENT_TERMS_DAYS = 30  # Net 30
DEFAULT_RELIABILITY_SCORE = 0.80  # 80% reliability = 10 days late
OPTIMISTIC_PAYMENT_DELAY_DAYS = 0  # On-time payment
REALISTIC_PAYMENT_DELAY_DAYS = 10  # 10 days late

# ═══════════════════════════════════════════════════════════════════
# DEPRECATED: Payroll configuration has been moved to config/constants.py
# ═══════════════════════════════════════════════════════════════════
# These values are kept for backward compatibility only.
# CFO: To change payroll amounts, edit PAYROLL_CONFIG in config/constants.py
# The new config allows different payroll amounts per entity (YAHSHUA vs ABBA)
#
# Old (DEPRECATED):
#   PAYROLL_FIRST_PAYMENT_AMOUNT = 1_000_000.00  # Same for all entities
#   PAYROLL_SECOND_PAYMENT_AMOUNT = 1_000_000.00  # Same for all entities
#
# New (config/constants.py):
#   PAYROLL_CONFIG = {
#       "YAHSHUA": {"15th": Decimal('1000000'), "30th": Decimal('1000000')},
#       "ABBA": {"15th": Decimal('500000'), "30th": Decimal('500000')}
#   }
PAYROLL_FIRST_PAYMENT_DAY = 15  # Still used for date calculation
PAYROLL_FIRST_PAYMENT_AMOUNT = 1_000_000.00  # DEPRECATED - Use PAYROLL_CONFIG
PAYROLL_SECOND_PAYMENT_DAY = 30  # Still used for date calculation
PAYROLL_SECOND_PAYMENT_AMOUNT = 1_000_000.00  # DEPRECATED - Use PAYROLL_CONFIG
PAYROLL_MONTHLY_TOTAL = PAYROLL_FIRST_PAYMENT_AMOUNT + PAYROLL_SECOND_PAYMENT_AMOUNT  # DEPRECATED

# Expense priorities
PRIORITY_PAYROLL = 1  # Non-negotiable
PRIORITY_LOANS = 2  # Contractual
PRIORITY_SOFTWARE = 3  # Medium flexibility
PRIORITY_OPERATIONS = 4  # High flexibility

# ═══════════════════════════════════════════════════════════════════
# CURRENCY FORMATTING
# ═══════════════════════════════════════════════════════════════════
CURRENCY_SYMBOL = "₱"
CURRENCY_DECIMAL_PLACES = 2
CURRENCY_THOUSANDS_SEPARATOR = ","

# ═══════════════════════════════════════════════════════════════════
# PERFORMANCE REQUIREMENTS
# ═══════════════════════════════════════════════════════════════════
MAX_SCENARIO_RECALC_TIME = 2.0  # seconds
MAX_DASHBOARD_LOAD_TIME = 3.0  # seconds
MAX_DATA_IMPORT_TIME = 10.0  # seconds
MAX_PROJECTION_GENERATION_TIME = 5.0  # seconds

# ═══════════════════════════════════════════════════════════════════
# SECURITY
# ═══════════════════════════════════════════════════════════════════
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# ═══════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════
TESTING = os.getenv("TESTING", "false").lower() == "true"
