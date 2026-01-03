# Data Management Guide

**JESUS Company Cash Management System**

---

## Core Principle: Google Sheets is the Source of Truth

The system follows a **single source of truth** architecture:

```
┌─────────────────────┐
│  GOOGLE SHEETS      │  ← SOURCE OF TRUTH (CFO edits here)
│  - Customers        │
│  - Vendors          │
│  - Bank Balances    │
└──────────┬──────────┘
           │
           │ [Sync Button in Dashboard]
           ↓
┌─────────────────────┐
│  LOCAL DATABASE     │  ← READ-ONLY COPY (System reads from here)
│  (SQLite/PostgreSQL)│
└──────────┬──────────┘
           │
           │ [Automatic Calculation]
           ↓
┌─────────────────────┐
│  CASH PROJECTIONS   │  ← CALCULATED RESULTS (Displayed in dashboard)
└─────────────────────┘
```

**Critical Rules**:
1. ✅ **EDIT DATA**: Always edit in Google Sheets
2. ✅ **SYNC DATA**: Click "Sync from Google Sheets" to update system
3. ✅ **VIEW RESULTS**: Dashboard shows calculated projections
4. ❌ **NEVER**: Edit data directly in database (changes will be overwritten)

---

## Understanding Sample Data

### What is Sample Data?

The system includes **TEMPORARY PLACEHOLDER DATA** for testing and demonstration:

| Data Type | Count | Purpose |
|-----------|-------|---------|
| Sample Customers | 50 | Show how revenue projections work |
| Sample Vendors | 20 | Show how expense scheduling works |
| Sample Bank Balances | 2 | Starting cash for each entity |
| Sample Scenarios | 4 | Demonstrate what-if analysis |

**IMPORTANT**: This sample data is **NOT REAL** and will be **COMPLETELY REPLACED** when you connect your Google Sheets.

### When to Use Sample Data

✅ **Use Sample Data When**:
- Testing the system for the first time
- Learning how projections work
- Developing/debugging new features
- Training staff on the dashboard

❌ **Don't Use Sample Data When**:
- Making real business decisions
- Presenting to leadership
- Planning actual cash flow
- Tracking real bank balances

---

## Setting Up Your Google Sheets

### 1. Create Your Google Sheets Document

**Required Sheets** (exact names matter):

1. **Customer Contracts** - Revenue sources
2. **Vendor Contracts** - Expense sources
3. **Bank Balances** - Starting cash positions

### 2. Customer Contracts Sheet Structure

**Required Columns** (exact names matter):

| Column Name | Type | Example | Required | Notes |
|-------------|------|---------|----------|-------|
| Company Name | Text | "Acme Corp" | Yes | Customer name |
| Monthly Fee | Number | 100000 | Yes | Recurring monthly value (₱) |
| Payment Plan | Text | "Quarterly" | Yes | Monthly, Quarterly, Bi-annually, Annual, More than 1 year |
| Contract Start | Date | 2026-01-15 | Yes | YYYY-MM-DD format |
| Contract End | Date | 2027-01-15 | No | Leave blank for ongoing |
| Status | Text | "Active" | Yes | Active, Inactive, Pending, Cancelled |
| Who Acquired | Text | "RCBC Partner" | Yes | RCBC Partner, Globe Partner, YOWI, TAI, PEI |
| Invoice Day | Number | 15 | No | Defaults to 15 |
| Payment Terms Days | Number | 30 | No | Defaults to 30 (Net 30) |
| Reliability Score | Number | 0.80 | No | 0.00-1.00, defaults to 0.80 |

**Entity Assignment** (automatic based on "Who Acquired"):
- **YAHSHUA**: RCBC Partner, Globe Partner, YOWI
- **ABBA**: TAI, PEI

**Example Row**:
```
Company Name: Globe Telecom
Monthly Fee: 500000
Payment Plan: Quarterly
Contract Start: 2026-01-01
Contract End: (blank)
Status: Active
Who Acquired: Globe Partner
Invoice Day: 15
Payment Terms Days: 30
Reliability Score: 0.80
```

**Payment Plan Logic**:
- "Monthly Fee" = the MONTHLY recurring value
- "Payment Plan" = how often payment is collected
- Example: ₱100K Monthly Fee with Quarterly plan = ₱300K received every quarter (₱100K × 3)
- Annual revenue is ALWAYS: Monthly Fee × 12, regardless of payment plan

### 3. Vendor Contracts Sheet Structure

**Required Columns**:

| Column Name | Type | Example | Required | Notes |
|-------------|------|---------|----------|-------|
| Vendor Name | Text | "Google Workspace" | Yes | Vendor/expense name |
| Amount | Number | 50000 | Yes | Expense amount (₱) |
| Frequency | Text | "Monthly" | Yes | One-time, Daily, Weekly, Bi-weekly, Monthly, Quarterly, Annual |
| Due Date | Date | 2026-01-21 | Yes | First payment date |
| Category | Text | "Software/Tech" | Yes | Payroll, Loans, Software/Tech, Operations, Rent, Utilities |
| Priority | Number | 3 | No | 1=Payroll (highest), 4=Operations (lowest) |
| Entity | Text | "YAHSHUA" | Yes | YAHSHUA, ABBA, or Both |
| Status | Text | "Active" | Yes | Active, Inactive |

**Entity Assignment**:
- **YAHSHUA**: Expense only for YAHSHUA
- **ABBA**: Expense only for ABBA
- **Both**: Shared expense, split according to `VENDOR_BOTH_SPLIT` ratio (default 50/50)

**Example Row (Single Entity)**:
```
Vendor Name: YAHSHUA Office Rent
Amount: 150000
Frequency: Monthly
Due Date: 2026-01-05
Category: Rent
Priority: 4
Entity: YAHSHUA
Status: Active
```

**Example Row (Shared Vendor)**:
```
Vendor Name: Google Workspace
Amount: 50000
Frequency: Monthly
Due Date: 2026-01-21
Category: Software/Tech
Priority: 3
Entity: Both
Status: Active
```

**Split Logic for "Both" Vendors**:
- Amount in sheet: ₱50,000 (total cost)
- YAHSHUA pays: ₱25,000 (50% per config)
- ABBA pays: ₱25,000 (50% per config)
- Consolidated total: ₱50,000 (not doubled)
- **CFO can adjust split ratio** in `config/constants.py` → `VENDOR_BOTH_SPLIT`

### 4. Bank Balances Sheet Structure

**Required Columns**:

| Column Name | Type | Example | Required | Notes |
|-------------|------|---------|----------|-------|
| Balance Date | Date | 2026-01-01 | Yes | Date of balance snapshot |
| Entity | Text | "YAHSHUA" | Yes | YAHSHUA or ABBA |
| Balance | Number | 15000000 | Yes | Cash balance (₱) |

**Example Rows**:
```
Balance Date: 2026-01-01
Entity: YAHSHUA
Balance: 15000000

Balance Date: 2026-01-01
Entity: ABBA
Balance: 8000000
```

**Important**: System uses the **MOST RECENT** bank balance for each entity as the starting point for projections.

---

## Data Management Operations

### Adding New Customers

**Steps**:
1. Open your Google Sheets document
2. Go to "Customer Contracts" sheet
3. Add a new row with customer details
4. Fill all required columns
5. Set "Who Acquired" to assign entity (YAHSHUA or ABBA)
6. Set "Status" to "Active"
7. In dashboard, click "Sync from Google Sheets"
8. Verify customer appears in customer list
9. Projections automatically recalculate

**Verification**:
```bash
# Check customer was imported
sqlite3 database/jesus_cash_management.db "SELECT company_name, entity, status FROM customer_contracts ORDER BY id DESC LIMIT 5;"
```

### Adding New Vendors

**Steps**:
1. Open your Google Sheets document
2. Go to "Vendor Contracts" sheet
3. Add a new row with vendor details
4. Fill all required columns
5. Set "Entity" (YAHSHUA, ABBA, or Both)
6. Set "Status" to "Active"
7. In dashboard, click "Sync from Google Sheets"
8. Verify vendor appears in vendor list
9. Projections automatically recalculate

**For Shared Vendors (Entity="Both")**:
- Enter the TOTAL amount in the "Amount" column
- System will automatically split according to configured ratio
- Default: 50/50 split between YAHSHUA and ABBA
- To change ratio: Edit `VENDOR_BOTH_SPLIT` in `config/constants.py`

### Updating Bank Balances

**Steps**:
1. Open your Google Sheets document
2. Go to "Bank Balances" sheet
3. Add a new row with today's date
4. Enter current balances for each entity
5. In dashboard, click "Sync from Google Sheets"
6. System uses most recent balance as starting point

**Example**:
```
# Old balance
Balance Date: 2026-01-01
Entity: YAHSHUA
Balance: 15000000

# New balance (after month ends)
Balance Date: 2026-02-01
Entity: YAHSHUA
Balance: 18500000  ← System will use this (most recent)
```

### Editing Existing Data

**To Edit Customer/Vendor**:
1. Find the row in Google Sheets
2. Make your changes (amount, status, dates, etc.)
3. Click "Sync from Google Sheets" in dashboard
4. Changes are immediately reflected in projections

**To Deactivate Customer/Vendor**:
1. Find the row in Google Sheets
2. Change "Status" column to "Inactive"
3. Click "Sync from Google Sheets"
4. Revenue/expense stops appearing in future projections

**To Delete Customer/Vendor**:
1. Delete the entire row in Google Sheets
2. Click "Sync from Google Sheets"
3. Data is removed from system
4. **WARNING**: Cannot be undone! Consider "Inactive" status instead.

---

## Syncing Data from Google Sheets

### Using the Dashboard (Recommended)

1. Open dashboard: `streamlit run dashboard/app.py`
2. Navigate to "Data Management" page
3. Click "Sync from Google Sheets" button
4. Wait for confirmation message
5. Verify import summary (X customers, Y vendors, Z balances)

### Using Python Script (Advanced)

```bash
# Sync all data
python3 -c "from data_processing.google_sheets_import import sync_all_data; sync_all_data()"
```

### What Happens During Sync?

1. **Connects** to Google Sheets using credentials
2. **Reads** all three sheets (Customers, Vendors, Balances)
3. **Validates** data (required fields, date formats, entity assignments)
4. **Replaces** existing data in local database
5. **Confirms** import with summary
6. **Triggers** automatic recalculation of projections

**Important**: Sync **REPLACES** all data. Any manual database changes will be overwritten.

---

## Clearing Sample Data

### Why Clear Sample Data?

Before connecting your real Google Sheets, you should clear the sample data to avoid confusion.

### Method 1: Reset Database (Complete Wipe)

```bash
# WARNING: This deletes EVERYTHING (sample data, scenarios, all data)
python3 -c "from database.db_manager import db_manager; db_manager.reset_database()"
```

**What Gets Deleted**:
- ✅ All sample customers
- ✅ All sample vendors
- ✅ All sample bank balances
- ✅ All sample scenarios
- ✅ All projections
- ✅ All metadata

**What Survives**:
- ✅ Configuration files (payroll amounts, split ratios)
- ✅ Code and business logic
- ✅ Google Sheets credentials

### Method 2: Sync Real Data (Automatic Replacement)

```bash
# Just sync your Google Sheets - it will replace sample data
python3 -c "from data_processing.google_sheets_import import sync_all_data; sync_all_data()"
```

**What Happens**:
- Sample data is replaced with real data from Google Sheets
- Much safer than Method 1 (no risk of empty database)

**Recommended**: Use Method 2 (sync real data) instead of Method 1 (reset).

---

## Verifying Data Imported Correctly

### Check Customer Contracts

```bash
# List all customers
sqlite3 database/jesus_cash_management.db "SELECT company_name, monthly_fee, payment_plan, entity, status FROM customer_contracts;"

# Count by entity
sqlite3 database/jesus_cash_management.db "SELECT entity, COUNT(*) FROM customer_contracts GROUP BY entity;"
```

**Expected Output**:
```
YAHSHUA|25
ABBA|15
```

### Check Vendor Contracts

```bash
# List all vendors
sqlite3 database/jesus_cash_management.db "SELECT vendor_name, amount, frequency, entity, status FROM vendor_contracts;"

# Check shared vendors
sqlite3 database/jesus_cash_management.db "SELECT vendor_name, amount, entity FROM vendor_contracts WHERE entity='Both';"
```

### Check Bank Balances

```bash
# List most recent balances
sqlite3 database/jesus_cash_management.db "SELECT balance_date, entity, balance FROM bank_balances ORDER BY balance_date DESC LIMIT 10;"
```

### Check Import Metadata

```bash
# Check last sync time
sqlite3 database/jesus_cash_management.db "SELECT key, value, updated_at FROM system_metadata WHERE key LIKE 'last_sync_%';"
```

**Expected Output**:
```
last_sync_customers|2026-01-03 10:30:00|2026-01-03 10:30:00
last_sync_vendors|2026-01-03 10:30:00|2026-01-03 10:30:00
last_sync_bank_balances|2026-01-03 10:30:00|2026-01-03 10:30:00
```

---

## Configuration vs Data

### CONFIGURATION (in `config/constants.py`)

**What It Controls**: Business rules, ratios, defaults

**Examples**:
- Payroll amounts per entity (YAHSHUA: ₱2M/month, ABBA: ₱1M/month)
- Vendor "Both" split ratio (YAHSHUA: 50%, ABBA: 50%)
- Payment plan frequencies (Quarterly = 3 months)
- Expense priorities (Payroll = 1, Operations = 4)

**How to Edit**: Edit `config/constants.py` file directly

**Example Change**:
```python
# Change ABBA payroll to ₱750K on 15th and 30th
PAYROLL_CONFIG = {
    "YAHSHUA": {
        "15th": Decimal('1000000.00'),
        "30th": Decimal('1000000.00'),
    },
    "ABBA": {
        "15th": Decimal('750000.00'),  # Changed from 500000
        "30th": Decimal('750000.00'),  # Changed from 500000
    }
}
```

**Impact**: Affects ALL projections (past and future)

### DATA (from Google Sheets)

**What It Contains**: Actual customers, vendors, balances

**Examples**:
- Globe Telecom contract: ₱500K/month
- Google Workspace vendor: ₱50K/month
- YAHSHUA bank balance: ₱15M as of Jan 1

**How to Edit**: Edit Google Sheets, then sync

**Impact**: Only affects projections after sync

### Key Difference

| Aspect | Configuration | Data |
|--------|--------------|------|
| **Location** | `config/constants.py` | Google Sheets |
| **Contains** | Business rules | Actual contracts |
| **Edit How** | Edit Python file | Edit Google Sheets + Sync |
| **Frequency** | Rarely (only when rules change) | Often (as business changes) |
| **Example** | "Payroll is ₱2M/month" | "We hired 5 new employees" |

---

## Common Data Management Tasks

### Task 1: Add a New Customer (Revenue Source)

1. Open Google Sheets → "Customer Contracts"
2. Add row:
   - Company Name: "New Client Inc"
   - Monthly Fee: 200000 (₱200K/month)
   - Payment Plan: "Quarterly"
   - Contract Start: 2026-03-01
   - Status: "Active"
   - Who Acquired: "RCBC Partner" (assigns to YAHSHUA)
3. Dashboard → "Sync from Google Sheets"
4. Check projections → See ₱600K (₱200K × 3) received every quarter starting March

### Task 2: Deactivate an Expired Contract

1. Open Google Sheets → "Customer Contracts"
2. Find customer row
3. Change "Status" to "Inactive"
4. Dashboard → "Sync from Google Sheets"
5. Revenue stops in future projections

### Task 3: Add a Shared Vendor (Split Expense)

1. Open Google Sheets → "Vendor Contracts"
2. Add row:
   - Vendor Name: "Shared Software License"
   - Amount: 100000 (₱100K/month total)
   - Frequency: "Monthly"
   - Due Date: 2026-01-15
   - Category: "Software/Tech"
   - Entity: "Both"
   - Status: "Active"
3. Dashboard → "Sync from Google Sheets"
4. Check projections:
   - YAHSHUA pays ₱50K (50%)
   - ABBA pays ₱50K (50%)
   - Consolidated total: ₱100K (not ₱200K)

### Task 4: Update Bank Balance (Month-End)

1. Check actual bank balances (from bank statements)
2. Open Google Sheets → "Bank Balances"
3. Add new rows:
   - Balance Date: 2026-02-01
   - Entity: YAHSHUA, Balance: 18500000
   - Entity: ABBA, Balance: 9200000
4. Dashboard → "Sync from Google Sheets"
5. New projections start from updated balances

### Task 5: Change Payroll Amount (Configuration Change)

**Scenario**: ABBA hired 5 more employees, payroll increases to ₱750K per payroll date

1. Open `config/constants.py`
2. Find `PAYROLL_CONFIG`
3. Update ABBA amounts:
   ```python
   "ABBA": {
       "15th": Decimal('750000.00'),  # Was 500000
       "30th": Decimal('750000.00'),  # Was 500000
   }
   ```
4. Save file
5. Restart dashboard (if running)
6. Projections automatically use new amounts

### Task 6: Adjust Vendor Split Ratio

**Scenario**: YAHSHUA grows larger, should pay 60% of shared costs (ABBA pays 40%)

1. Open `config/constants.py`
2. Find `VENDOR_BOTH_SPLIT`
3. Update ratios:
   ```python
   VENDOR_BOTH_SPLIT = {
       "YAHSHUA": Decimal('0.6'),  # Was 0.5 (50%)
       "ABBA": Decimal('0.4'),     # Was 0.5 (50%)
   }
   ```
4. Save file
5. Restart dashboard (if running)
6. All "Both" vendor expenses now split 60/40

---

## Data Quality Checklist

Before syncing data, verify:

**Customer Contracts**:
- [ ] All required columns filled
- [ ] Dates in YYYY-MM-DD format
- [ ] Monthly Fee is positive number
- [ ] Payment Plan is valid (Monthly, Quarterly, Bi-annually, Annual, More than 1 year)
- [ ] Status is valid (Active, Inactive, Pending, Cancelled)
- [ ] Who Acquired is valid (RCBC Partner, Globe Partner, YOWI, TAI, PEI)
- [ ] Contract Start is before Contract End (if end exists)

**Vendor Contracts**:
- [ ] All required columns filled
- [ ] Dates in YYYY-MM-DD format
- [ ] Amount is positive number
- [ ] Frequency is valid (One-time, Daily, Weekly, Bi-weekly, Monthly, Quarterly, Annual)
- [ ] Entity is valid (YAHSHUA, ABBA, Both)
- [ ] Status is valid (Active, Inactive)
- [ ] Category is valid (Payroll, Loans, Software/Tech, Operations, Rent, Utilities)

**Bank Balances**:
- [ ] Balance Date is valid date
- [ ] Entity is valid (YAHSHUA, ABBA)
- [ ] Balance is a number (can be negative for overdraft)
- [ ] Most recent balance exists for each entity

---

## Troubleshooting

### Problem: "No customers imported"

**Possible Causes**:
1. Sheet name doesn't match exactly (must be "Customer Contracts")
2. Required columns missing or misspelled
3. No "Active" customers in sheet
4. Google Sheets credentials not set up

**Solution**:
1. Check sheet name spelling
2. Verify all required columns exist
3. Check at least one customer has Status="Active"
4. Verify credentials file at path in `config/settings.py`

### Problem: "Vendor split not working correctly"

**Possible Causes**:
1. Entity column not set to "Both" (case-sensitive)
2. Split ratio not configured correctly
3. Dashboard not restarted after config change

**Solution**:
1. Check Entity column is exactly "Both" (not "both" or "BOTH")
2. Verify `VENDOR_BOTH_SPLIT` ratios sum to 1.0
3. Restart dashboard after config changes

### Problem: "Projections showing old data"

**Possible Causes**:
1. Forgot to sync after editing Google Sheets
2. Caching in dashboard
3. Edited local database instead of Google Sheets

**Solution**:
1. Click "Sync from Google Sheets" in dashboard
2. Refresh dashboard page
3. **NEVER** edit database directly - always edit Google Sheets

### Problem: "Bank balance not updated"

**Possible Causes**:
1. New balance has older date than existing balance
2. Entity name doesn't match exactly
3. Balance not imported from sheets

**Solution**:
1. System uses MOST RECENT balance - ensure new date is later
2. Check Entity is exactly "YAHSHUA" or "ABBA" (case-sensitive)
3. Verify balance row exists in Google Sheets, then sync

---

## Best Practices

### DO ✅

1. **Always edit in Google Sheets** - It's the source of truth
2. **Sync after every change** - Keep system up to date
3. **Use "Inactive" status** - Instead of deleting rows (preserves history)
4. **Verify after sync** - Check import summary for errors
5. **Test with sample data first** - Before using real data
6. **Backup your Google Sheets** - File → Make a copy (monthly)
7. **Document configuration changes** - Add comments in `config/constants.py`
8. **Use consistent date format** - YYYY-MM-DD (2026-01-15)

### DON'T ❌

1. **Don't edit database directly** - Changes will be overwritten on next sync
2. **Don't delete rows in sheets** - Use "Inactive" status instead
3. **Don't skip syncing** - System won't know about your changes
4. **Don't use sample data for real decisions** - Replace with real data first
5. **Don't change sheet names** - Must match exactly (case-sensitive)
6. **Don't forget to restart dashboard** - After config file changes
7. **Don't mix data and config** - Know which file to edit
8. **Don't assume sync happened** - Always verify import summary

---

## Quick Reference

### Data Flow Summary

```
CFO Edits → Google Sheets → Sync Button → Local Database → Projections
   ↑                                                            ↓
   └──────────────── View in Dashboard ←─────────────────────┘
```

### File Locations

| What | Where |
|------|-------|
| **Google Sheets URL** | `config/google_sheets_config.py` |
| **Google Credentials** | Path in `config/settings.py` |
| **Payroll Config** | `config/constants.py` → `PAYROLL_CONFIG` |
| **Vendor Split Ratio** | `config/constants.py` → `VENDOR_BOTH_SPLIT` |
| **Local Database** | `database/jesus_cash_management.db` |
| **Sample Data Generator** | `scripts/generate_sample_data.py` |
| **Import Logic** | `data_processing/google_sheets_import.py` |

### Common Commands

```bash
# Generate sample data (for testing)
python3 scripts/generate_sample_data.py

# Sync from Google Sheets
python3 -c "from data_processing.google_sheets_import import sync_all_data; sync_all_data()"

# Reset database (WARNING: deletes everything)
python3 -c "from database.db_manager import db_manager; db_manager.reset_database()"

# Verify data
sqlite3 database/jesus_cash_management.db "SELECT COUNT(*) FROM customer_contracts WHERE status='Active';"

# Run dashboard
streamlit run dashboard/app.py
```

---

## Next Steps

1. **If using sample data**: Explore the system, run projections, test scenarios
2. **When ready for real data**:
   - Set up your Google Sheets with the required structure
   - Add your credentials to the system
   - Sync your real data
   - Verify import was successful
   - Start making real cash flow projections!

---

**Last Updated**: 2026-01-03
**For Support**: Check test suite (`pytest tests/ -v`) and ASSUMPTIONS.md
