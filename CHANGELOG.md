# CHANGELOG

All notable changes to the JESUS Company Cash Management System.

## [Unreleased]

### Removed
- **⚠️ BREAKING CHANGE: Vendor "Both" entity option**: Removed the ability to assign vendors to entity="Both" with automatic split logic. See migration details below.

### Changed
- **Vendor entity assignment**: Vendors must now be directly assigned to either 'YAHSHUA' or 'ABBA' - no more shared "Both" entity
- **Expense calculations**: Removed split logic from projections and queries - vendor amounts now used directly

### Configuration
- **REMOVED: VENDOR_BOTH_SPLIT**: This configuration has been removed from `config/constants.py`

### Migration
- **Automatic migration script**: `scripts/migrate_both_vendors.py` splits existing "Both" vendors into separate YAHSHUA and ABBA entries
- **How to migrate**:
  1. Backup database: `cp database/jesus_cash_management.db database/jesus_cash_management.db.backup`
  2. Run migration: `python scripts/migrate_both_vendors.py --yes`
  3. Verify: Check that all "Both" vendors have been split into separate entries
- **Impact**: Shared vendors (like AWS Cloud) will now appear as two separate entries in the database
- **Example**: "AWS Cloud" (₱100K, Both) → "AWS Cloud - YAHSHUA" (₱50K, YAHSHUA) + "AWS Cloud - ABBA" (₱50K, ABBA)

---

## [1.0.0] - 2026-01-03

### Added
- Complete backend system (database, projections, scenarios)
- 7-page Streamlit dashboard
- Authentication system (admin/viewer roles)
- Settings page showing configuration
- Google Sheets sync capability
- Strategic planning calculators
- **Scenario combining logic**: New `apply_multiple_scenarios_to_projection()` method to combine/stack multiple scenarios together (`scenario_engine/scenario_calculator.py:91`)
- **Monthly Expenses column**: Scenario Comparison page now displays detailed monthly expense breakdown for each scenario, showing individual line items for recurring expenses (hiring, recurring costs) and one-time investments separately (`dashboard/pages/3_Scenario_Comparison.py:101`)
- **Monthly Revenue column**: Scenario Comparison page now displays revenue impact for each scenario, showing revenue additions (new clients) and revenue reductions (customer churn) with clear formatting (`dashboard/pages/3_Scenario_Comparison.py:166`)

### Fixed
- Revenue calculation: Now properly multiplies Monthly Fee × billing frequency
- Vendor "Both" split: No longer double-counts, uses configurable ratio
- Authentication: Default users now created properly
- Payroll: Now configurable per entity (not hard-coded)
- **Scenario Comparison error**: Fixed SQLAlchemy `DetachedInstanceError` when comparing scenarios - now eagerly loads scenario changes using `joinedload()` before detaching from session (`scenario_engine/scenario_calculator.py:39`)
- **Scenario Comparison logic**: Fixed to show Baseline + Combined (all scenarios stacked together) instead of individual scenario lines - provides true cumulative impact analysis (`dashboard/pages/3_Scenario_Comparison.py`)
- **Baseline labeling**: Baseline now clearly labeled as "Baseline (No Changes)" for clarity
- **Database queries bug**: Fixed `get_scenario_by_id()` to reference correct model fields - changed `amount_per_month` to `expense_amount`, removed non-existent `customer_name` and `investment_name` fields, changed `revenue_lost` to `lost_revenue`, added `notes` field (`database/queries.py:209-217`)
- **Test data payroll**: Fixed test data generator to create TWO payroll entries per entity (15th + 30th) totaling ₱2M/month for YAHSHUA and ₱1M/month for ABBA, matching business rules (`scripts/generate_simple_test_data.py`)

### Changed
- Payroll amounts moved to config/constants.py
- Vendor split ratios moved to config/constants.py
- Entity mapping configurable in config/entity_mapping.py
- **Scenario Comparison behavior**: Now combines all selected scenarios into ONE projection showing cumulative effect, instead of showing each scenario separately
- **Scenario Comparison UI**: Updated to support 1-3 scenarios (previously required minimum 2), clearer messaging about combining logic

### Configuration
- PAYROLL_CONFIG: Set payroll per entity
- VENDOR_BOTH_SPLIT: Set split ratio for shared vendors

---

## How to Update This File

When you fix a bug or add a feature, tell Claude Code:
```
Add to CHANGELOG: [describe the change]
```

Categories:
- **Added**: New features
- **Fixed**: Bug fixes
- **Changed**: Changes to existing features
- **Removed**: Removed features
- **Security**: Security updates
- **Configuration**: New configuration options

---

## Quick Reference - How to Remember Things:

| Method | Best For | How to Use |
|--------|----------|------------|
| `CLAUDE.md` | Project rules & standards | Claude Code reads automatically |
| `# note` | Quick facts during session | Type `#` then your note |
| `PROGRESS.md` | Daily accomplishments | Update at end of each day |
| `CHANGELOG.md` | Version history & bug fixes | Update after each fix |
| `ASSUMPTIONS.md` | Business logic decisions | Already exists! |

---

## Going Forward - Simple Habit:

**After EVERY bug fix or change, tell Claude Code:**
```
Add to CHANGELOG: Fixed [describe bug] by [describe fix]
```

**Example:**
```
Add to CHANGELOG: Fixed scenario comparison - now shows interactive Plotly chart comparing multiple scenarios side-by-side
```

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.*
*This project uses [Semantic Versioning](https://semver.org/).*
