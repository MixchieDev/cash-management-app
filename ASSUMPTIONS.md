# Development Assumptions

This document tracks all assumptions made during autonomous development of the backend system.

## Business Logic Assumptions

### Revenue Calculations

1. **Invoice Timing**
   - **Assumption**: Invoice always sent on the 15th of the month before billing month
   - **Rationale**: Specified in requirements (15 days BEFORE the 1st)
   - **Example**: March billing → Invoice Feb 15

2. **Payment Delay**
   - **Assumption**: Optimistic = 0 days delay, Realistic = 10 days delay
   - **Rationale**: Specified in requirements (80% reliability = 10 days late)
   - **Impact**: Realistic projections show lower cash in early months

3. **Contract Renewals**
   - **Assumption**: Contracts with no end date renew automatically forever
   - **Rationale**: Requirements state "subscriptions renew automatically unless client disengages"
   - **Impact**: Revenue continues indefinitely for contracts without contract_end

4. **Monthly Fee and Payment Plans**
   - **Assumption**: "Monthly Fee" represents the MONTHLY recurring value; "Payment Plan" determines HOW OFTEN payment is collected
   - **Rationale**: Requirements specify "Use 'Monthly Fee' column as the actual recurring amount" - this means monthly value, not payment amount
   - **Formula**: Payment Amount = Monthly Fee × Number of Months in Payment Period
   - **Examples**:
     - ₱100K Monthly Fee + Monthly plan = ₱100K received monthly
     - ₱100K Monthly Fee + Quarterly plan = ₱300K received every quarter (₱100K × 3 months)
     - ₱100K Monthly Fee + Bi-annually plan = ₱600K received every 6 months (₱100K × 6 months)
     - ₱100K Monthly Fee + Annual plan = ₱1.2M received once per year (₱100K × 12 months)
   - **Annual Revenue**: ALWAYS = Monthly Fee × 12, regardless of payment plan
   - **Impact**: Payment plan affects CASH FLOW timing, not total annual revenue

### Expense Calculations

5. **Payroll Amounts (CONFIGURABLE PER ENTITY)**
   - **Assumption**: Payroll is ALWAYS paid on 15th and 30th of every month, but amounts are CONFIGURABLE per entity
   - **Rationale**: Different entities have different employee counts and payroll needs
   - **Configuration**: Set in `config/constants.py` → `PAYROLL_CONFIG`
   - **Default Values**:
     - YAHSHUA: ₱1M on 15th + ₱1M on 30th = ₱2M/month
     - ABBA: ₱500K on 15th + ₱500K on 30th = ₱1M/month
   - **CFO Control**: Change amounts by editing `PAYROLL_CONFIG` in config/constants.py (NO code changes needed)
   - **Priority**: Payroll is still Priority 1 (non-negotiable, ALWAYS paid first)

6. **Payroll for 30th in Short Months**
   - **Assumption**: February payroll on 28th (or 29th in leap years)
   - **Rationale**: Use last day of month if 30th doesn't exist
   - **Implementation**: `min(30, last_day_of_month)`

7. **Vendor Payment Frequency**
   - **Assumption**: Monthly = every 30 days (approximate), Quarterly = every 90 days
   - **Rationale**: Standard business practice for recurring expenses
   - **Alternative**: Could use exact month/quarter boundaries, but chosen simplicity

### Entity Assignment

8. **Acquisition Source Mapping**
   - **Assumption**: RCBC, Globe, YOWI → YAHSHUA; TAI, PEI → ABBA
   - **Rationale**: Specified in requirements and config/entity_mapping.py
   - **Validation**: Raises error if unmapped source encountered

9. **Entity Isolation**
   - **Assumption**: YAHSHUA cash CANNOT pay ABBA expenses (completely separate)
   - **Rationale**: CRITICAL requirement - "YAHSHUA data CANNOT leak into ABBA"
   - **Implementation**: Separate projections, separate bank balances

10. **Vendor Entity "Both" (SPLIT, NOT DOUBLE-COUNTED)**
    - **Assumption**: Vendors with entity "Both" are SPLIT between YAHSHUA and ABBA (NOT counted full in both)
    - **Rationale**: Common expenses (e.g., Google Workspace) shared by both entities should not be double-counted
    - **Configuration**: Set in `config/constants.py` → `VENDOR_BOTH_SPLIT`
    - **Default Split**: 50/50 (YAHSHUA: 50%, ABBA: 50%)
    - **CFO Control**: Adjust ratio by editing `VENDOR_BOTH_SPLIT` (e.g., 60/40, 70/30)
    - **Example**:
      - Google Workspace: ₱50K/month, entity="Both"
      - YAHSHUA projection: ₱25K expense (50%)
      - ABBA projection: ₱25K expense (50%)
      - Consolidated total: ₱50K (NOT ₱100K)
    - **Implementation**: Split ratio applied in expense_scheduler.py when calculating vendor events

## Technical Assumptions

### Database

11. **SQLite for Development**
    - **Assumption**: SQLite sufficient for development, PostgreSQL for production
    - **Rationale**: Easy setup, file-based, no server required
    - **Migration Path**: DATABASE_URL environment variable for switching

12. **Bank Balance as Source of Truth**
    - **Assumption**: ALWAYS use most recent bank_balances record as starting point
    - **Rationale**: CRITICAL requirement - "NEVER use projected cash as starting point"
    - **Validation**: Raises error if no bank balance found

13. **Decimal Precision**
    - **Assumption**: All currency values use Python Decimal with 2 decimal places
    - **Rationale**: Avoid floating-point precision errors in financial calculations
    - **Implementation**: `Decimal.quantize(Decimal('0.01'))`

### Date Handling

14. **Projection Period Boundaries**
    - **Assumption**: Periods are inclusive (start_date <= event_date <= end_date)
    - **Rationale**: Standard practice for date range queries
    - **Example**: Jan 1 to Jan 31 includes both Jan 1 and Jan 31

15. **Monthly Timeframe**
    - **Assumption**: Monthly periods end on last day of month
    - **Rationale**: Most natural aggregation for monthly projections
    - **Example**: January period = Jan 1-31, February = Feb 1-28/29

16. **Quarterly Timeframe**
    - **Assumption**: Quarters are 3-month periods from projection start
    - **Rationale**: Simplifies calculation vs calendar quarters
    - **Example**: Start Jan 1 → Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec

### Scenario Modeling

17. **Scenario Changes Apply Immediately**
    - **Assumption**: Changes take effect on start_date (not pro-rated)
    - **Rationale**: Simplifies calculations, reasonable approximation
    - **Example**: Hiring 10 employees on March 15 → Full ₱500K increase starting March

18. **Hiring Scenario Payroll**
    - **Assumption**: New employees add to TOTAL payroll (don't replace ₱2M baseline)
    - **Rationale**: ₱2M baseline is minimum, hiring is ADDITIONAL
    - **Example**: Hire 10 @ ₱50K = ₱2M baseline + ₱500K = ₱2.5M total payroll

19. **Investment Scenarios**
    - **Assumption**: One-time investments occur on exact start_date
    - **Rationale**: Simplest interpretation of one-time expense
    - **Example**: ₱10M investment on June 1 → ₱10M outflow on June 1 only

20. **Scenario End Dates**
    - **Assumption**: If end_date is None, change continues forever
    - **Rationale**: Allows modeling permanent changes
    - **Example**: Hiring with no end_date = permanent employees

### Google Sheets Import

21. **Read-Only Access**
    - **Assumption**: System ONLY reads from Google Sheets, NEVER writes back
    - **Rationale**: CRITICAL requirement - "Read-only access to preserve source of truth"
    - **Implementation**: No write methods in google_sheets_import.py

22. **Date Format Parsing**
    - **Assumption**: Try multiple date formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
    - **Rationale**: Google Sheets may export in various formats
    - **Fallback**: Raise clear error if format not recognized

23. **Missing Fields**
    - **Assumption**: Raise validation error for missing required fields
    - **Rationale**: Better to fail fast than make assumptions about data
    - **Alternative**: Could use defaults, but chose strict validation

### Testing

24. **Sample Data Quantities**
    - **Assumption**: 50 customers and 20 vendors is realistic for testing
    - **Rationale**: Large enough to test performance, small enough to debug
    - **Actual Data**: Will vary, system handles any quantity

25. **Test Database Reset**
    - **Assumption**: Each test starts with clean database
    - **Rationale**: Ensures test isolation and reproducibility
    - **Implementation**: `clean_database` fixture in pytest

## Performance Assumptions

26. **Projection Calculation Speed**
    - **Assumption**: In-memory calculation faster than database queries
    - **Rationale**: Events calculated once, then iterated in memory
    - **Validation**: Performance tests verify <5 second requirement

27. **Caching Strategy**
    - **Assumption**: Projections can be cached in database after calculation
    - **Rationale**: Dashboard may request same projection multiple times
    - **Future**: Implement cache invalidation when data changes

## Data Quality Assumptions

28. **Contract Dates**
    - **Assumption**: contract_start always before contract_end (if end exists)
    - **Rationale**: Business logic constraint
    - **Validation**: Data validator checks this

29. **Positive Amounts**
    - **Assumption**: Monthly fees and vendor amounts are always positive
    - **Rationale**: Negative amounts don't make business sense
    - **Validation**: Data validator enforces this

30. **Bank Balance Can Be Negative**
    - **Assumption**: Bank balances can be negative (overdraft)
    - **Rationale**: Real-world scenario, system should handle it
    - **Implementation**: No validation preventing negative balances

## Deployment Assumptions

31. **Environment Variables**
    - **Assumption**: Production uses .env file or environment variables
    - **Rationale**: Security best practice (no secrets in code)
    - **Defaults**: Provided for development, must override for production

32. **Streamlit Cloud Deployment**
    - **Assumption**: Streamlit Cloud supports SQLite or provides PostgreSQL
    - **Rationale**: Specified in requirements
    - **Migration**: DATABASE_URL environment variable makes switching easy

## Assumptions NOT Made (Conservative Choices)

- **NOT assuming** payment terms other than Net 30 (used actual payment_terms_days field)
- **NOT assuming** all contracts are monthly (used actual payment_plan field)
- **NOT assuming** all vendors are active (checked status field)
- **NOT assuming** Google Sheets structure (validated all required fields)
- **NOT assuming** timezone (using date objects, not datetime)

---

**Document Purpose**: Track all decisions for future reference and validation
**Review Status**: Ready for CFO review
**Last Updated**: 2026-01-03
