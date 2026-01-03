# JESUS Company Strategic Cash Management System

**Version**: 1.0
**Status**: Backend Complete ✅ | Frontend In Progress
**Purpose**: Strategic financial planning tool for CFO to scale ₱50M → ₱250M revenue

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt --break-system-packages

# Initialize database with sample data
python3 scripts/generate_sample_data.py

# Run projection demo
python3 scripts/generate_projection_demo.py
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=projection_engine --cov=scenario_engine --cov-report=html
```

---

## Project Structure

```
cash-management-app/
├── config/                 # Configuration (settings, entity mapping, constants)
├── database/              # Database schema, models, manager
├── data_processing/       # Google Sheets import, data validation
├── projection_engine/     # Cash projection calculations
├── scenario_engine/       # What-if scenario modeling
├── utils/                 # Utilities (currency formatter)
├── tests/                 # Comprehensive test suite
├── scripts/              # Sample data, projection demos
├── docs/                 # Documentation
├── dashboard/            # Streamlit dashboard (TODO: Day 8+)
└── requirements.txt      # Python dependencies
```

---

## Core Features

### 1. Cash Flow Projections

Generate multi-year cash flow forecasts with:
- ✅ Daily, weekly, monthly, quarterly timeframes
- ✅ Optimistic vs Realistic scenarios (payment delay modeling)
- ✅ Multi-entity support (YAHSHUA, ABBA, Consolidated)
- ✅ Automatic revenue recognition (invoicing + payment terms)
- ✅ Expense scheduling (including ₱2M monthly payroll)

**Example**:
```python
from datetime import date
from projection_engine.cash_projector import CashProjector

projector = CashProjector()
projection = projector.calculate_cash_projection(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 12, 31),
    entity='YAHSHUA',
    timeframe='monthly',
    scenario_type='realistic'
)

for point in projection:
    print(f"{point.date}: {format_currency(point.ending_cash)}")
```

### 2. Scenario Modeling

What-if analysis for strategic decisions:
- ✅ Hiring scenarios (add employees × salary)
- ✅ Expense scenarios (add recurring costs)
- ✅ Revenue scenarios (add new clients)
- ✅ Investment scenarios (one-time cash outflows)
- ✅ Break-even analysis (when is it affordable?)

**Example**:
```python
from decimal import Decimal
from scenario_engine.scenario_storage import ScenarioStorage

# Create hiring scenario
scenario_id = ScenarioStorage.create_hiring_scenario(
    scenario_name='Hire 10 Engineers',
    entity='YAHSHUA',
    employees=10,
    salary_per_employee=Decimal('60000.00'),
    start_date=date(2026, 3, 1)
)
```

### 3. Entity Isolation

Complete separation between entities:
- ✅ YAHSHUA Outsourcing Worldwide Inc
- ✅ ABBA Initiative OPC
- ✅ Consolidated view (combined totals)

### 4. Google Sheets Integration (Source of Truth)

**Read-only sync** from Google Sheets:
- ✅ Customer contracts (revenue sources)
- ✅ Vendor contracts (expense sources)
- ✅ Bank balances (starting cash positions)

**System Design**:
- Google Sheets = **Source of truth** (CFO edits here)
- Local database = **Read-only copy** (system reads from here)
- Dashboard = **Calculated results** (projections and scenarios)

**Data never flows backwards** - system ONLY reads from Google Sheets, never writes back.

📖 See [DATA_MANAGEMENT_GUIDE.md](docs/DATA_MANAGEMENT_GUIDE.md) for complete sync instructions.

---

## Business Rules (CRITICAL)

### Revenue Model
- **Invoice Timing**: 15 days BEFORE the 1st of the month
- **Payment Terms**: Net 30 (customers should pay within 30 days)
- **Default Reliability**: 80% = 10 days late
  - Optimistic: Payment on time (Net 30)
  - Realistic: Payment 10 days late (Net 30 + 10)

### Expense Model
- **Payroll (Priority 1 - NON-NEGOTIABLE)**: ₱1M on 15th + ₱1M on 30th of EVERY month
- **Loans (Priority 2)**: Amortization + Interest
- **Software/Tech (Priority 3)**: AWS, Google Workspace, etc.
- **Operations (Priority 4)**: Rent, Utilities, Supplies

### Entity Assignment
- **YAHSHUA**: Customers from RCBC Partner, Globe Partner, YOWI
- **ABBA**: Customers from TAI, PEI

---

## Documentation

| Document | Purpose |
|----------|---------|
| [DATA_MANAGEMENT_GUIDE.md](docs/DATA_MANAGEMENT_GUIDE.md) | **How to manage data** (customers, vendors, sync) |
| [BACKEND_INTEGRATION_GUIDE.md](docs/BACKEND_INTEGRATION_GUIDE.md) | For frontend developers |
| [BACKEND_VALIDATION_REPORT.md](docs/BACKEND_VALIDATION_REPORT.md) | Validation results |
| [ASSUMPTIONS.md](ASSUMPTIONS.md) | Business logic decisions |
| [PROGRESS.md](PROGRESS.md) | Development progress |
| [CLAUDE.md](.claude/CLAUDE.md) | Project overview (from .claude/) |

---

## Tech Stack

- **Language**: Python 3.11+
- **Database**: SQLite (dev), PostgreSQL (prod)
- **ORM**: SQLAlchemy 2.0+
- **Testing**: pytest with 100% coverage on financial calculations
- **Frontend**: Streamlit (coming in Days 8+)
- **Data Source**: Google Sheets API
- **Deployment**: Streamlit Cloud

---

## Data Management: Sample vs Real Data

### ⚠️ IMPORTANT: Understanding Sample Data

The system ships with **SAMPLE DATA FOR TESTING ONLY**:
- **50 sample customers** - Fictional companies for demonstration
- **20 sample vendors** - Placeholder expenses
- **4 sample scenarios** - Example what-if analyses
- **Sample bank balances**: ₱15M (YAHSHUA), ₱8M (ABBA)

**This data is NOT REAL and will be COMPLETELY REPLACED when you connect your Google Sheets.**

### Google Sheets = Source of Truth

The system follows a **single source of truth** architecture:

```
Google Sheets (CFO edits here)
      ↓
[Sync Button]
      ↓
Local Database (read-only copy)
      ↓
Cash Projections (calculated results)
```

**How It Works**:
1. ✅ **EDIT**: Add/update customers and vendors in Google Sheets
2. ✅ **SYNC**: Click "Sync from Google Sheets" in dashboard
3. ✅ **VIEW**: Projections automatically update with your real data
4. ❌ **NEVER**: Edit database directly (changes will be overwritten)

### Getting Started with Real Data

**First Time Setup**:
```bash
# 1. Test with sample data (safe to explore)
python3 scripts/generate_sample_data.py
python3 scripts/generate_projection_demo.py

# 2. When ready for real data, sync from your Google Sheets
python3 -c "from data_processing.google_sheets_import import sync_all_data; sync_all_data()"
```

**Next Steps**:
1. Set up your Google Sheets with required structure (see DATA_MANAGEMENT_GUIDE.md)
2. Add Google Sheets credentials to system
3. Sync your real data
4. Start making real cash flow projections!

📖 **Full Guide**: See [docs/DATA_MANAGEMENT_GUIDE.md](docs/DATA_MANAGEMENT_GUIDE.md) for complete instructions.

---

## Testing

### Test Coverage
- ✅ Currency formatting: 100%
- ✅ Payroll calculations: 100%
- ✅ Revenue calculations: Comprehensive
- ✅ Scenario calculations: Comprehensive
- ✅ Entity isolation: Verified
- ✅ Performance: All targets met

### Run Tests
```bash
pytest tests/ -v
pytest tests/test_currency_formatting.py -v
pytest tests/test_projections.py -v
pytest tests/test_scenarios.py -v
```

---

## Environment Variables

```bash
# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///database/jesus_cash_management.db

# Google Sheets (required for sync)
GOOGLE_SHEETS_CREDS_PATH=/path/to/credentials.json

# Security (required for production)
SECRET_KEY=your-random-secret-key

# Testing flag
TESTING=false
```

---

## Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| Scenario recalculation | <2s | ✅ <1s |
| Dashboard load | <3s | ⏳ TBD |
| Data import (500 contracts) | <10s | ✅ <5s |
| Projection (3yr daily) | <5s | ✅ ~3s |

---

## Biblical Principle

> **"Suppose one of you wants to build a tower. Won't you first sit down and estimate the cost to see if you have enough money to complete it?"**
> — Luke 14:28

This tool helps CFO Mich "count the cost" of growth decisions, enabling wise stewardship of ₱50M → ₱250M growth.

---

## Support

For technical issues:
1. Check tests: `pytest tests/ -v`
2. Review ASSUMPTIONS.md for business logic
3. Review PROGRESS.md for known issues
4. Check logs: `--logger.level=debug`

---

## Next Steps

- [ ] **Days 8-10**: Build Streamlit dashboard UI
- [ ] **Days 11-12**: Implement scenario management UI
- [ ] **Day 13**: Testing and refinement
- [ ] **Day 14**: CFO review and deployment

---

**Last Updated**: 2026-01-03
**Backend Status**: ✅ Complete
**Frontend Status**: ⏳ Pending (Days 8+)
