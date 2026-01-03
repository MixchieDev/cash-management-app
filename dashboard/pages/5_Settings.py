"""
Settings Page - System Configuration Display
Shows all configuration values (read-only).
"""
import streamlit as st
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth
from config.constants import (
    PAYMENT_PLAN_FREQUENCIES,
    EXPENSE_CATEGORIES
)
from config.entity_mapping import ENTITY_MAPPING
from config.settings import (
    DEFAULT_PAYMENT_TERMS_DAYS,
    DEFAULT_RELIABILITY_SCORE,
    REALISTIC_PAYMENT_DELAY_DAYS,
    INVOICE_DAYS_BEFORE_MONTH
)
from utils.currency_formatter import format_currency

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Settings - JESUS Company",
    page_icon="⚙️",
    layout="wide"
)

require_auth()

st.title("⚙️ System Configuration")

st.info("""
📋 **Configuration Management**

These values are configured in the backend. To change them, edit `config/constants.py`
and restart the application.
""")

# ═══════════════════════════════════════════════════════════════════
# ENTITY MAPPING
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🏷️ Entity Assignment Rules")
st.markdown("Customers are automatically assigned to entities based on **Who acquired the client** column:")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### YAHSHUA Outsourcing")
    yahshua_sources = [k for k, v in ENTITY_MAPPING.items() if v == 'YAHSHUA']
    for source in yahshua_sources:
        st.markdown(f"- {source}")

with col2:
    st.markdown("### ABBA Initiative")
    abba_sources = [k for k, v in ENTITY_MAPPING.items() if v == 'ABBA']
    for source in abba_sources:
        st.markdown(f"- {source}")

st.caption("⚠️ Unrecognized acquisition sources will cause import errors")

# ═══════════════════════════════════════════════════════════════════
# PAYMENT TERMS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 📅 Payment Terms Configuration")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Invoice Lead Time", f"{INVOICE_DAYS_BEFORE_MONTH} days")
    st.caption("Days before billing to send invoice")

with col2:
    st.metric("Payment Terms", f"Net {DEFAULT_PAYMENT_TERMS_DAYS}")
    st.caption("Days customer has to pay")

with col3:
    st.metric("Default Reliability", f"{DEFAULT_RELIABILITY_SCORE * 100:.0f}%")
    st.caption("Expected on-time payment rate")

# ═══════════════════════════════════════════════════════════════════
# RELIABILITY / PAYMENT DELAY
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## ⏱️ Payment Reliability Settings")

st.markdown(f"""
**Projection Scenarios:**

| Scenario | Description | Expected Payment |
|----------|-------------|------------------|
| **Optimistic** | Customers pay on time | Invoice + {DEFAULT_PAYMENT_TERMS_DAYS} days |
| **Realistic** | Based on {DEFAULT_RELIABILITY_SCORE*100:.0f}% reliability | Invoice + {DEFAULT_PAYMENT_TERMS_DAYS + REALISTIC_PAYMENT_DELAY_DAYS} days |

The realistic scenario adds **{REALISTIC_PAYMENT_DELAY_DAYS} days** to account for typical payment delays.
""")

# ═══════════════════════════════════════════════════════════════════
# PAYMENT PLAN MULTIPLIERS
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 💵 Payment Plan Multipliers")
st.markdown("Revenue is calculated as: **Monthly Fee × Payment Plan Multiplier**")

import pandas as pd

multipliers_data = [
    {
        'Payment Plan': plan,
        'Multiplier': f'×{mult}',
        'Example': f"₱100K → {format_currency(Decimal('100000') * mult)} per {plan.lower()}"
    }
    for plan, mult in PAYMENT_PLAN_FREQUENCIES.items()
]

df_multipliers = pd.DataFrame(multipliers_data)
st.table(df_multipliers)

# ═══════════════════════════════════════════════════════════════════
# EXPENSE CATEGORIES
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 📁 Expense Categories")
st.markdown("Vendors are classified into categories with different priorities:")

categories_data = [
    {
        'Category': cat,
        'Priority': info['priority'],
        'Flexibility (Days)': info['flexibility_days'],
        'Description': info['description']
    }
    for cat, info in sorted(EXPENSE_CATEGORIES.items(), key=lambda x: x[1]['priority'])
]

df_categories = pd.DataFrame(categories_data)
st.table(df_categories)

st.caption("Priority 1 = Highest priority (must pay first), Priority 4 = Lowest priority (can delay if needed)")

# ═══════════════════════════════════════════════════════════════════
# HOW TO CHANGE
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 📝 How to Change Configuration")

st.code("""
# Example: Add new acquisition source
# Edit config/entity_mapping.py
ENTITY_MAPPING = {
    'RCBC Partner': 'YAHSHUA',
    'Globe Partner': 'YAHSHUA',
    'YOWI': 'YAHSHUA',
    'NEW_PARTNER': 'YAHSHUA',  # Add new partner
    'TAI': 'ABBA',
    'PEI': 'ABBA'
}

# After editing, restart the Streamlit app:
# streamlit run dashboard/app.py
""", language='python')

st.warning("⚠️ **Important**: Changes to configuration require application restart to take effect.")

# ═══════════════════════════════════════════════════════════════════
# CURRENT CONFIG FILE LOCATION
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 📁 Configuration File Locations")

config_files_data = [
    {
        'Configuration': 'Payroll',
        'File': '`config/constants.py`'
    },
    {
        'Configuration': 'Entity Mapping (Acquisition Sources)',
        'File': '`config/entity_mapping.py`'
    },
    {
        'Configuration': 'Payment Terms, Reliability',
        'File': '`config/settings.py`'
    },
    {
        'Configuration': 'Google Sheets ID',
        'File': '`config/google_sheets_config.py`'
    }
]

df_files = pd.DataFrame(config_files_data)
st.table(df_files)

st.caption("View these files to understand the current configuration values")
