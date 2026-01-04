# JESUS Company Strategic Cash Management System

## Project Overview
**Purpose**: Strategic financial planning tool for CFO to scale ₱50M → ₱250M revenue
**Entities**: YAHSHUA Outsourcing Worldwide Inc, The ABBA Initiative OPC
**Stack**: Python 3.11+, Streamlit, Google Sheets API, SQLite/PostgreSQL
**Deployment**: Streamlit Cloud

This is a contract-based multi-year cash projection system with scenario modeling for strategic growth decisions.

---

## Business Rules

### Revenue Model
- **Invoice Timing**: 15 days BEFORE the 1st of the month
  - Example: Invoice on Feb 15 for March billing (due Apr 1)
- **Payment Terms**: Net 30 (customers should pay within 30 days of invoice)
- **Default Reliability**: 80% (expect payment 10 days LATER than Net 30)
  - Optimistic scenario: Payment on time (Net 30)
  - Realistic scenario: Payment 10 days late (Net 30 + 10 days)
- **Recurring Revenue**: Use "Monthly Fee" column as the actual recurring amount
- **Payment Plans**: Monthly, Quarterly, Annual, Bi-annually, More than 1 year
- **Renewal**: Subscriptions renew automatically unless client disengages

### Expense Model

**Payroll (Priority 1 - Non-negotiable)**:
- Fixed: ₱1M on 15th, ₱1M on 30th of every month
- ALWAYS pay first, never delay
- Scenario planning: Average ₱40K-60K per employee

**Loans (Priority 2 - Contractual)**:
- Amortization + Interest payments
- Must honor payment schedule
- Track principal vs interest separately for P&L

**Software/Tech (Priority 3 - Medium flexibility)**:
- Typical due date: 21st of month
- Can delay 5-10 days if cash tight
- Example: AWS, Google Workspace, SaaS tools

**Operations (Priority 4 - High flexibility)**:
- Categories: Rent, Utilities, Supplies, Meals, Fuel
- Can negotiate timing with most vendors
- Highest flexibility in cash crunch scenarios

### Entity Assignment

**YAHSHUA Outsourcing** = Customers acquired by:
- RCBC Partner
- Globe Partner
- YOWI

**ABBA Initiative** = Customers acquired by:
- TAI
- PEI

*(Configurable in `config/entity_mapping.py`)*

---

## Technical Standards

### Code Quality
- **Python Version**: 3.11+ required
- **Type Hints**: Required for all function signatures

```python
def calculate_projection(start: date, end: date) -> List[ProjectionDataPoint]:
    pass
```

- **Docstrings**: Google style for all public functions

```python
def calculate_cash_position(inflows: Decimal, outflows: Decimal) -> Decimal:
    """Calculate ending cash position.

    Args:
        inflows: Total revenue received in period
        outflows: Total expenses paid in period

    Returns:
        Ending cash balance (can be negative)
    """
    return starting_cash + inflows - outflows
```

### Currency Formatting
- **ALWAYS**: Philippine Peso (₱) symbol
- **ALWAYS**: Comma thousands separator
- **ALWAYS**: 2 decimal places

**Correct**: ₱2,500,000.00
**Wrong**: 2500000, ₱2500000, ₱2,500,000

```python
from utils.currency_formatter import format_currency
amount = Decimal('2500000')
display = format_currency(amount)  # Returns: ₱2,500,000.00
```

### Performance Requirements
- **Scenario Recalculation**: <2 seconds
- **Dashboard Load**: <3 seconds
- **Data Import**: <10 seconds for 500 contracts
- **Projection Generation**: <5 seconds for 3-year daily projection (1095 data points)

### Testing Requirements
- **Coverage**: 100% on all financial calculation modules
- **Test Data**: Use realistic data (1000+ data points for stress testing)
- **Edge Cases**: Must test:
  - Contract gaps (no revenue for period)
  - Contract renewals (mid-projection expiration)
  - Negative cash scenarios
  - Multi-entity isolation (YAHSHUA data doesn't leak into ABBA)
  - Scenario accuracy (hiring/expense/revenue changes apply correctly)
  - Currency rounding (no precision errors)

```python
# Example test structure
def test_payroll_always_2m_per_month():
    """Payroll must be exactly ₱2M per month (₱1M on 15th + ₱1M on 30th)."""
    projection = calculate_projection('2026-01-01', '2026-12-31', 'YAHSHUA')
    for month_data in group_by_month(projection):
        payroll_total = sum(p.outflows for p in month_data if p.category == 'Payroll')
        assert payroll_total == Decimal('2000000.00'), \
            f"Payroll must be ₱2M per month, got ₱{payroll_total:,.2f}"
```

---

## Development Workflow

### Git Worktrees (Parallel Development)

Use Git worktrees to enable 3 simultaneous development sessions without switching branches.

```bash
# Main worktree (backend development)
cd jesus-company-cash-management

# Create worktree for frontend development
git worktree add ../cash-mgmt-frontend frontend-dashboard

# Create worktree for testing
git worktree add ../cash-mgmt-testing feature-tests

# Now you can work in 3 terminal sessions simultaneously:
# Session 1: Backend in main directory
# Session 2: Frontend in ../cash-mgmt-frontend
# Session 3: Testing in ../cash-mgmt-testing
```

### Commit Standards
- **Frequency**: Commit after each logical unit of work (every 30-60 minutes)
- **Messages**: Descriptive and specific
  - Good: "Implement realistic payment delay (10-day lag) in projection engine"
  - Bad: "Update projections"

### Test-Driven Development
1. Write test first
2. Run test (should fail)
3. Write minimal code to pass test
4. Refactor
5. Repeat

### Auto-Testing Hooks

```bash
# Set up pre-commit hook to run tests
echo "pytest tests/" > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## Deployment

### Environment Variables

```bash
# Never commit these to git
GOOGLE_SHEETS_CREDS_PATH=/path/to/credentials.json
SPREADSHEET_ID=1abc123xyz...
SECRET_KEY=random_secret_for_sessions
DATABASE_URL=sqlite:///jesus_cash_management.db  # or PostgreSQL URL
```

### Streamlit Cloud Deployment
1. Push to GitHub repository
2. Connect repository in Streamlit Cloud
3. Add environment variables in Streamlit Cloud dashboard
4. Deploy

### Security Checklist
- Google Sheets credentials in environment variables (not in code)
- User passwords hashed with bcrypt
- Session secret key in environment variables
- No sensitive data in Git history
- `.env` file in `.gitignore`

---

## Never Do (Critical Don'ts)

1. **DON'T start Streamlit server automatically**
   - CFO runs manually: `streamlit run dashboard/app.py`
   - Don't add `if __name__ == '__main__': streamlit.run()`

2. **DON'T guess at entity assignments**
   - Always use config/entity_mapping.py
   - Raise error if acquisition source is unmapped

3. **DON'T deploy without tests passing**
   - Run `pytest tests/` before every deployment
   - CI/CD should block deployment if tests fail

4. **DON'T modify projection formulas without CFO approval**
   - Financial calculations are sacred
   - Document any formula changes in CHANGELOG.md

5. **DON'T expose raw numbers without ₱ formatting**
   - Every currency display must use format_currency()
   - No naked Decimals in dashboard

6. **DON'T write back to Google Sheets**
   - Read-only access to preserve source of truth
   - All edits happen in dashboard → save to local DB

---

## Biblical Principle

> **"Suppose one of you wants to build a tower. Won't you first sit down and estimate the cost to see if you have enough money to complete it?"**
> — Luke 14:28

This tool helps CFO Mich "count the cost" of growth decisions:
- Can we afford to hire 10 employees?
- What revenue do we need to partner with CyTech?
- When can we invest ₱10M in a new office?

Financial planning is stewardship. This system enables wise stewardship of ₱50M → ₱250M growth.

---

## Quick Reference

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt --break-system-packages

# Run tests
pytest tests/ -v

# Run dashboard
streamlit run dashboard/app.py

# Sync data from Google Sheets
python -c "from data_processing.google_sheets_import import sync_all_data; sync_all_data()"
```

### Common Tasks

**Add a new scenario**:
1. Navigate to Scenarios page
2. Fill out scenario form (Hiring/Expenses/Revenue tabs)
3. Click "Run Scenario" to see impact
4. Click "Save Scenario" to persist

**Compare scenarios**:
1. Navigate to Scenario Comparison page
2. Select 2-3 scenarios to compare
3. View side-by-side charts and metrics
4. Export to PDF/Excel if needed

**Update contracts**:
1. Edit Google Sheets (source of truth)
2. In dashboard, click "Sync from Google Sheets"
3. Verify import was successful
4. Projections auto-update

---

## Support

For technical issues, check:
1. Test suite: `pytest tests/ -v`
2. Logs: `streamlit run dashboard/app.py --logger.level=debug`
3. Database: `sqlite3 jesus_cash_management.db`

For business logic questions, consult CFO Mich.

---

## Work Log

### January 3, 2026

**Transaction Breakdown Modal Feature** (Commit: `eb9e863`)

Added the ability to click on any data point in the cash flow projection chart to see a detailed breakdown of transactions for that period.

**Files Added/Modified:**
- `dashboard/pages/1_Home.py` - Added chart click handler and modal trigger
- `projection_engine/cash_projector.py` - Added `calculate_cash_projection_detailed()` and `ProjectionResult.get_events_for_period()`
- `dashboard/components/transaction_modal.py` - New modal component showing revenue inflows and expense outflows
- `utils/period_helpers.py` - Helper functions for calculating period ranges (daily/weekly/monthly/quarterly)
- `tests/test_period_helpers.py` - 10 tests for period helper functions
- `tests/test_projection_detailed.py` - 6 tests for detailed projection functionality

**How it works:**
1. User clicks on a data point in the cash flow chart
2. System calculates the period range based on timeframe (e.g., "Week of Jan 12-18")
3. Modal displays all revenue events (customer payments) and expense events (vendor payments) for that period
4. Shows totals and net cash flow for the period

**Status:** Committed to master, no remote configured for push.

---

**Vendor Contract End Date Feature** (Commit: `cd3ca64`)

Added optional `end_date` field to vendor contracts. If blank, expenses continue indefinitely. If set, expenses stop after that date.

**Files Added/Modified:**
- `database/models.py` - Added `end_date` column to VendorContract
- `projection_engine/expense_scheduler.py` - Updated to respect both `start_date` and `end_date`
- `data_processing/google_sheets_import.py` - Handles "End Date" column from Google Sheets
- `database/migrations/002_add_vendor_end_date.sql` - Migration to add the column
- `tests/test_vendor_end_date.py` - 9 comprehensive tests

**How it works:**
- If `end_date` is NULL/blank → expense continues indefinitely (current behavior)
- If `end_date` is set → expense payments stop after that date
- Works with all frequencies (monthly, quarterly, annual, one-time)
- Properly handles both `start_date` and `end_date` together

**Google Sheets:** Add an "End Date" column to your Vendors sheet.

---

**Monthly Equivalent Column** (Commit: `5a86664`)

Added a "Monthly Equiv." column to the Vendor Contracts table that shows the normalized monthly cost for each expense, regardless of payment frequency.

**Files Modified:**
- `dashboard/pages/4_Contracts.py` - Added Monthly Equiv. column with frequency multipliers

**Calculation:**
| Frequency | Multiplier | Example |
|-----------|------------|---------|
| Monthly | ×1 | ₱50K → ₱50K/mo |
| Quarterly | ÷3 | ₱150K → ₱50K/mo |
| Annual | ÷12 | ₱600K → ₱50K/mo |
| Bi-annually | ÷6 | ₱300K → ₱50K/mo |
| One-time | — | Shows "—" |

---

**Payment Override System** (Commit: `ee1a070`)

Added complete system for one-off payment date adjustments. Allows users to move or skip specific customer/vendor payments without changing the recurring schedule.

**Files Added/Modified:**
- `database/models.py` - New `PaymentOverride` model with unique constraint
- `database/queries.py` - CRUD functions: `get_payment_overrides()`, `create_payment_override()`, `delete_payment_override()`, `get_overrides_for_contract()`, `get_customer_by_id()`, `get_vendor_by_id()`
- `projection_engine/revenue_calculator.py` - Added `payment_overrides` parameter to `calculate_revenue_events()`
- `projection_engine/expense_scheduler.py` - Added `payment_overrides` parameter to `calculate_vendor_events()`
- `projection_engine/cash_projector.py` - Fetches overrides and passes to calculators
- `dashboard/pages/8_Payment_Overrides.py` - NEW dashboard page for managing overrides
- `database/migrations/003_add_payment_overrides.sql` - Migration file
- `tests/test_payment_overrides.py` - 7 tests covering move, skip, and multi-vendor scenarios

**PaymentOverride Model:**
| Field | Type | Purpose |
|-------|------|---------|
| `override_type` | String | 'customer' or 'vendor' |
| `contract_id` | Integer | Reference to customer/vendor contract |
| `original_date` | Date | The scheduled payment date being overridden |
| `new_date` | Date (nullable) | New payment date (null if skipping) |
| `action` | String | 'move' or 'skip' |
| `entity` | String | 'YAHSHUA' or 'ABBA' |
| `reason` | Text | Optional notes |

**How it works:**
1. Go to "Payment Overrides" page in dashboard
2. Select Customer or Vendor type
3. Select the contract and upcoming payment date
4. Choose action: Move to new date OR Skip entirely
5. Add optional reason
6. Override automatically reflects in cash flow projections

**Example use cases:**
- Client requested payment delay → Move customer payment from Jan 15 to Jan 25
- Billing dispute with vendor → Skip February AWS payment
- Holiday timing adjustment → Move payroll from Dec 31 to Dec 28

---

*Last Updated: January 3, 2026*
*Prepared by: Master Orchestrator AI*
