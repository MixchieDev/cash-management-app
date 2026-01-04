# Backend Integration Guide for Frontend Crew

**Version**: 1.0
**Date**: 2026-01-03
**For**: Dashboard/Frontend Development (Days 8+)

This document provides everything needed to integrate with the backend cash projection and scenario modeling system.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Core Modules](#core-modules)
3. [API Reference](#api-reference)
4. [Data Structures](#data-structures)
5. [Usage Examples](#usage-examples)
6. [Error Handling](#error-handling)
7. [Performance Tips](#performance-tips)

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt --break-system-packages

# Initialize database
python -c "from database.db_manager import db_manager; db_manager.init_schema()"

# Load sample data (for development)
python scripts/generate_sample_data.py

# Run tests to verify
pytest tests/ -v
```

### First Projection

```python
from datetime import date
from projection_engine.cash_projector import CashProjector

# Initialize projector
projector = CashProjector()

# Generate 12-month projection
projection = projector.calculate_cash_projection(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 12, 31),
    entity='YAHSHUA',
    timeframe='monthly',
    scenario_type='realistic'
)

# Display results
for point in projection:
    print(f"{point.date}: {point.ending_cash}")
```

---

## Core Modules

### 1. Cash Projector (`projection_engine/cash_projector.py`)

**Purpose**: Generate cash flow projections for any period

**Key Method**: `calculate_cash_projection()`

**When to Use**:
- Dashboard home page (show current projection)
- Projection comparison page
- Export to Excel/PDF

### 2. Scenario Calculator (`scenario_engine/scenario_calculator.py`)

**Purpose**: Apply what-if scenarios to projections

**Key Methods**:
- `apply_scenario_to_projection()` - Apply changes to baseline
- `calculate_break_even()` - Determine affordability
- `calculate_scenario_impact_summary()` - Compare scenarios

**When to Use**:
- Scenario modeling page
- What-if analysis
- Break-even calculations

### 3. Scenario Storage (`scenario_engine/scenario_storage.py`)

**Purpose**: Save and retrieve scenarios

**Key Methods**:
- `create_hiring_scenario()` - Create hiring scenario
- `create_expense_scenario()` - Create expense scenario
- `create_revenue_scenario()` - Create revenue scenario
- `get_all_scenarios()` - List all scenarios
- `delete_scenario()` - Delete scenario

**When to Use**:
- Scenario management page
- Save/load user scenarios

### 4. Currency Formatter (`utils/currency_formatter.py`)

**Purpose**: Format all currency displays

**Key Methods**:
- `format_currency()` - Format as ₱X,XXX.XX
- `format_currency_compact()` - Format as ₱X.XXM
- `parse_currency()` - Parse formatted string back to Decimal

**When to Use**: EVERYWHERE - all currency displays

### 5. Google Sheets Import (`data_processing/google_sheets_import.py`)

**Purpose**: Sync data from Google Sheets

**Key Method**: `sync_all_data()`

**When to Use**:
- "Sync Data" button in dashboard
- Scheduled sync (if implemented)

---

## API Reference

### CashProjector.calculate_cash_projection()

Generate cash flow projection for a period.

**Parameters**:
```python
start_date: date          # Projection start date
end_date: date            # Projection end date
entity: str               # 'YAHSHUA', 'ABBA', or 'Consolidated'
timeframe: str            # 'daily', 'weekly', 'monthly', 'quarterly'
scenario_type: str        # 'optimistic' or 'realistic'
scenario_id: int = None   # Custom scenario ID (optional)
```

**Returns**: `List[ProjectionDataPoint]`

**Example**:
```python
projection = projector.calculate_cash_projection(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 12, 31),
    entity='YAHSHUA',
    timeframe='monthly',
    scenario_type='realistic'
)
```

### ScenarioStorage.create_hiring_scenario()

Create a hiring scenario.

**Parameters**:
```python
scenario_name: str                  # Scenario name
entity: str                          # Entity
employees: int                       # Number of employees
salary_per_employee: Decimal         # Salary per employee
start_date: date                     # Start date
end_date: date = None                # End date (optional)
description: str = None              # Description (optional)
```

**Returns**: `int` (scenario ID)

**Example**:
```python
from decimal import Decimal
from scenario_engine.scenario_storage import ScenarioStorage

scenario_id = ScenarioStorage.create_hiring_scenario(
    scenario_name='Hire 10 Engineers',
    entity='YAHSHUA',
    employees=10,
    salary_per_employee=Decimal('60000.00'),
    start_date=date(2026, 3, 1),
    description='Scale engineering team for new contracts'
)
```

### ScenarioCalculator.calculate_break_even()

Calculate when scenario becomes affordable.

**Parameters**:
```python
baseline_projection: List[ProjectionDataPoint]  # Baseline projection
scenario_id: int                                 # Scenario to analyze
```

**Returns**: `Dict` with:
```python
{
    'affordable': bool,                      # Is scenario affordable?
    'start_date': date,                      # When can we start (if affordable)
    'first_negative_date': date,             # When does cash go negative (if not)
    'additional_revenue_needed': Decimal,     # How much more revenue needed
    'message': str                           # Human-readable summary
}
```

**Example**:
```python
from scenario_engine.scenario_calculator import ScenarioCalculator

calculator = ScenarioCalculator()
baseline = projector.calculate_cash_projection(...)

break_even = calculator.calculate_break_even(baseline, scenario_id)

if break_even['affordable']:
    print(f"✓ Scenario is affordable starting {break_even['start_date']}")
else:
    print(f"⚠ Need additional revenue: {format_currency(break_even['additional_revenue_needed'])}")
```

### format_currency()

Format amount as Philippine Peso.

**Parameters**:
```python
amount: Union[Decimal, float, int]  # Amount to format
```

**Returns**: `str` (e.g., '₱2,500,000.00')

**Example**:
```python
from decimal import Decimal
from utils.currency_formatter import format_currency

amount = Decimal('2500000')
formatted = format_currency(amount)  # '₱2,500,000.00'
```

---

## Data Structures

### ProjectionDataPoint

Single point in a cash projection.

```python
@dataclass
class ProjectionDataPoint:
    date: date                  # Period end date
    starting_cash: Decimal      # Cash at start of period
    inflows: Decimal            # Revenue received in period
    outflows: Decimal           # Expenses paid in period
    ending_cash: Decimal        # Cash at end of period
    entity: str                 # Entity ('YAHSHUA', 'ABBA', 'Consolidated')
    timeframe: str              # Timeframe ('daily', 'weekly', 'monthly', 'quarterly')
    scenario_type: str          # Scenario type ('optimistic', 'realistic')
    is_negative: bool           # Is ending cash negative?
```

**Usage**:
```python
for point in projection:
    print(f"{point.date}: {format_currency(point.ending_cash)}")
    if point.is_negative:
        print("  ⚠ WARNING: Negative cash!")
```

### Scenario Model

Scenario for what-if analysis.

```python
class Scenario:
    id: int
    scenario_name: str
    entity: str
    description: str
    created_by: str
    created_at: datetime
    changes: List[ScenarioChange]  # List of changes in scenario
```

---

## Usage Examples

### Example 1: Generate and Display Projection

```python
from datetime import date
from projection_engine.cash_projector import CashProjector
from utils.currency_formatter import format_currency

projector = CashProjector()

# Generate projection
projection = projector.calculate_cash_projection(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 12, 31),
    entity='YAHSHUA',
    timeframe='monthly',
    scenario_type='realistic'
)

# Display in Streamlit
import streamlit as st
import pandas as pd

# Convert to DataFrame
df = pd.DataFrame([{
    'Month': p.date.strftime('%B %Y'),
    'Starting Cash': format_currency(p.starting_cash),
    'Inflows': format_currency(p.inflows),
    'Outflows': format_currency(p.outflows),
    'Ending Cash': format_currency(p.ending_cash),
    'Status': '⚠ Negative' if p.is_negative else '✓ Positive'
} for p in projection])

st.dataframe(df)
```

### Example 2: Create and Apply Scenario

```python
from decimal import Decimal
from scenario_engine.scenario_storage import ScenarioStorage
from scenario_engine.scenario_calculator import ScenarioCalculator

# Create scenario
scenario_id = ScenarioStorage.create_hiring_scenario(
    scenario_name='Hire 5 Employees',
    entity='YAHSHUA',
    employees=5,
    salary_per_employee=Decimal('50000.00'),
    start_date=date(2026, 3, 1)
)

# Get baseline projection
projector = CashProjector()
baseline = projector.calculate_cash_projection(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 12, 31),
    entity='YAHSHUA',
    timeframe='monthly',
    scenario_type='realistic'
)

# Apply scenario
calculator = ScenarioCalculator()
scenario_projection = calculator.apply_scenario_to_projection(baseline, scenario_id)

# Compare
for base, scenario in zip(baseline, scenario_projection):
    print(f"{base.date}: {format_currency(base.ending_cash)} → {format_currency(scenario.ending_cash)}")
```

### Example 3: Optimistic vs Realistic Comparison

```python
# Optimistic projection
optimistic = projector.calculate_cash_projection(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 12, 31),
    entity='YAHSHUA',
    timeframe='monthly',
    scenario_type='optimistic'  # Payments on time
)

# Realistic projection
realistic = projector.calculate_cash_projection(
    start_date=date(2026, 1, 1),
    end_date=date(2026, 12, 31),
    entity='YAHSHUA',
    timeframe='monthly',
    scenario_type='realistic'  # 10-day payment delay
)

# Display comparison chart
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[p.date for p in optimistic],
    y=[float(p.ending_cash) for p in optimistic],
    name='Optimistic',
    line=dict(color='green')
))
fig.add_trace(go.Scatter(
    x=[p.date for p in realistic],
    y=[float(p.ending_cash) for p in realistic],
    name='Realistic',
    line=dict(color='orange')
))
st.plotly_chart(fig)
```

### Example 4: Sync Data from Google Sheets

```python
from data_processing.google_sheets_import import sync_all_data

# Sync all data
try:
    result = sync_all_data()
    st.success(f"✓ Synced {result['customers']} customers, {result['vendors']} vendors, {result['balances']} balances")
except Exception as e:
    st.error(f"✗ Sync failed: {e}")
```

---

## Error Handling

### Common Errors and Solutions

**1. "No bank balance found for entity"**
```python
# Solution: Add bank balance
with db_manager.session_scope() as session:
    balance = BankBalance(
        balance_date=date(2026, 1, 1),
        entity='YAHSHUA',
        balance=Decimal('10000000.00')
    )
    session.add(balance)
```

**2. "Unmapped acquisition source"**
```python
# Solution: Add to config/entity_mapping.py
ENTITY_MAPPING = {
    ...
    "New Partner": "YAHSHUA",  # Add new source
}
```

**3. "Invalid entity"**
```python
# Solution: Use valid entity
# Valid: 'YAHSHUA', 'ABBA', 'Consolidated'
# Invalid: 'yahshua', 'Both', anything else
```

---

## Performance Tips

### 1. Cache Projections

```python
# Don't recalculate on every page load
if 'projection' not in st.session_state:
    st.session_state.projection = projector.calculate_cash_projection(...)

projection = st.session_state.projection
```

### 2. Use Appropriate Timeframes

```python
# For overview: monthly
projection = projector.calculate_cash_projection(..., timeframe='monthly')

# For detailed analysis: daily
projection = projector.calculate_cash_projection(..., timeframe='daily')
```

### 3. Limit Projection Period

```python
# For dashboard: 12 months
end_date = start_date + relativedelta(months=12)

# For detailed planning: 36 months
end_date = start_date + relativedelta(months=36)
```

---

## Testing Your Integration

### Verify Basic Integration

```python
# Test 1: Can generate projection?
projection = projector.calculate_cash_projection(
    date(2026, 1, 1), date(2026, 12, 31), 'YAHSHUA', 'monthly', 'realistic'
)
assert len(projection) == 12

# Test 2: Can format currency?
formatted = format_currency(Decimal('2500000'))
assert formatted == '₱2,500,000.00'

# Test 3: Can create scenario?
scenario_id = ScenarioStorage.create_hiring_scenario(...)
assert scenario_id > 0
```

---

## Support

For issues or questions:
1. Check tests: `pytest tests/ -v`
2. Review ASSUMPTIONS.md for business logic
3. Check PROGRESS.md for known issues

---

**Ready for Integration**: ✅
**Last Updated**: 2026-01-03
**Backend Version**: 1.0
