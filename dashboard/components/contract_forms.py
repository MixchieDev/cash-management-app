"""
Reusable contract form components for the Contracts page.
Renders add/edit forms for customers, vendors, and bank balances.
"""
import streamlit as st
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict

from config.constants import (
    VALID_PAYMENT_PLANS,
    VALID_EXPENSE_CATEGORIES,
    VALID_EXPENSE_FREQUENCIES,
    VALID_CONTRACT_STATUSES,
)
from config.entity_mapping import get_valid_entities
from utils.currency_formatter import format_currency


def _parse_currency_input(value: str) -> Decimal:
    """Parse a currency string input to Decimal."""
    cleaned = str(value).replace('₱', '').replace(',', '').replace(' ', '').strip()
    if not cleaned:
        return Decimal('0')
    return Decimal(cleaned).quantize(Decimal('0.01'))


def render_customer_form(existing: Optional[Dict] = None, key_prefix: str = 'cust') -> Optional[Dict]:
    """
    Render a customer contract form.

    Args:
        existing: Existing customer data for editing (None for new)
        key_prefix: Unique key prefix for form widgets

    Returns:
        Dict of form data if submitted, None otherwise
    """
    is_edit = existing is not None
    title = f"Edit {existing['company_name']}" if is_edit else "Add Customer Contract"

    # Get entity options (just the codes, not Consolidated)
    entity_options = [e for e in get_valid_entities() if e not in ('Consolidated', 'All')]

    with st.form(key=f"{key_prefix}_form", clear_on_submit=not is_edit):
        st.markdown(f"#### {title}")

        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input(
                "Company Name *",
                value=existing['company_name'] if is_edit else '',
                key=f"{key_prefix}_name"
            )
            monthly_fee_str = st.text_input(
                "Monthly Fee (₱) *",
                value=str(existing['monthly_fee']) if is_edit else '',
                placeholder="50000.00",
                key=f"{key_prefix}_fee"
            )
            payment_plan = st.selectbox(
                "Payment Plan *",
                options=VALID_PAYMENT_PLANS,
                index=VALID_PAYMENT_PLANS.index(existing['payment_plan']) if is_edit and existing['payment_plan'] in VALID_PAYMENT_PLANS else 0,
                key=f"{key_prefix}_plan"
            )
            who_acquired = st.text_input(
                "Acquired By *",
                value=existing['who_acquired'] if is_edit else '',
                placeholder="e.g., RCBC Partner, Globe Partner, YOWI, TAI, PEI",
                key=f"{key_prefix}_acquired"
            )

        with col2:
            entity = st.selectbox(
                "Entity *",
                options=entity_options,
                index=entity_options.index(existing['entity']) if is_edit and existing['entity'] in entity_options else 0,
                key=f"{key_prefix}_entity"
            )
            contract_start = st.date_input(
                "Contract Start *",
                value=existing['contract_start'] if is_edit else date.today(),
                key=f"{key_prefix}_start"
            )
            contract_end = st.date_input(
                "Contract End (optional)",
                value=existing['contract_end'] if is_edit and existing.get('contract_end') else None,
                key=f"{key_prefix}_end"
            )
            status = st.selectbox(
                "Status",
                options=VALID_CONTRACT_STATUSES,
                index=VALID_CONTRACT_STATUSES.index(existing['status']) if is_edit and existing['status'] in VALID_CONTRACT_STATUSES else 0,
                key=f"{key_prefix}_status"
            )

        # Advanced fields
        with st.expander("Advanced Settings"):
            col3, col4 = st.columns(2)
            with col3:
                invoice_day = st.number_input(
                    "Invoice Day (1-28, blank=use global)",
                    min_value=0, max_value=28,
                    value=existing.get('invoice_day', 0) or 0 if is_edit else 0,
                    key=f"{key_prefix}_inv_day",
                    help="Day of month to invoice. 0 = use global setting."
                )
                reliability = st.slider(
                    "Reliability Score",
                    min_value=0.0, max_value=1.0,
                    value=float(existing.get('reliability_score', 0.80)) if is_edit else 0.80,
                    step=0.05,
                    key=f"{key_prefix}_reliability"
                )
            with col4:
                payment_terms = st.number_input(
                    "Payment Terms Days (blank=use global)",
                    min_value=0, max_value=120,
                    value=existing.get('payment_terms_days', 0) or 0 if is_edit else 0,
                    key=f"{key_prefix}_terms",
                    help="Net payment terms. 0 = use global setting."
                )
            notes = st.text_area(
                "Notes",
                value=existing.get('notes', '') or '' if is_edit else '',
                key=f"{key_prefix}_notes"
            )

        submitted = st.form_submit_button(
            "Update Contract" if is_edit else "Add Contract",
            type="primary"
        )

        if submitted:
            # Validate required fields
            errors = []
            if not company_name.strip():
                errors.append("Company Name is required")
            if not monthly_fee_str.strip():
                errors.append("Monthly Fee is required")
            if not who_acquired.strip():
                errors.append("Acquired By is required")

            try:
                monthly_fee = _parse_currency_input(monthly_fee_str)
                if monthly_fee < 0:
                    errors.append("Monthly Fee cannot be negative")
            except (InvalidOperation, ValueError):
                errors.append("Monthly Fee must be a valid number")
                monthly_fee = None

            if errors:
                for error in errors:
                    st.error(error)
                return None

            result = {
                'company_name': company_name.strip(),
                'monthly_fee': monthly_fee,
                'payment_plan': payment_plan,
                'contract_start': contract_start,
                'contract_end': contract_end if contract_end else None,
                'status': status,
                'who_acquired': who_acquired.strip(),
                'entity': entity,
                'invoice_day': invoice_day if invoice_day > 0 else None,
                'payment_terms_days': payment_terms if payment_terms > 0 else None,
                'reliability_score': Decimal(str(reliability)),
                'notes': notes.strip() if notes.strip() else None,
            }

            return result

    return None


def render_vendor_form(existing: Optional[Dict] = None, key_prefix: str = 'vend') -> Optional[Dict]:
    """
    Render a vendor contract form.

    Args:
        existing: Existing vendor data for editing (None for new)
        key_prefix: Unique key prefix for form widgets

    Returns:
        Dict of form data if submitted, None otherwise
    """
    is_edit = existing is not None
    title = f"Edit {existing['vendor_name']}" if is_edit else "Add Vendor Contract"

    entity_options = [e for e in get_valid_entities() if e not in ('Consolidated', 'All')]
    vendor_statuses = ['Active', 'Inactive', 'Paid', 'Pending']

    with st.form(key=f"{key_prefix}_form", clear_on_submit=not is_edit):
        st.markdown(f"#### {title}")

        col1, col2 = st.columns(2)

        with col1:
            vendor_name = st.text_input(
                "Vendor Name *",
                value=existing['vendor_name'] if is_edit else '',
                key=f"{key_prefix}_name"
            )
            category = st.selectbox(
                "Category *",
                options=VALID_EXPENSE_CATEGORIES,
                index=VALID_EXPENSE_CATEGORIES.index(existing['category']) if is_edit and existing['category'] in VALID_EXPENSE_CATEGORIES else 0,
                key=f"{key_prefix}_cat"
            )
            amount_str = st.text_input(
                "Amount (₱) *",
                value=str(existing['amount']) if is_edit else '',
                placeholder="10000.00",
                key=f"{key_prefix}_amt"
            )
            frequency = st.selectbox(
                "Frequency *",
                options=VALID_EXPENSE_FREQUENCIES,
                index=VALID_EXPENSE_FREQUENCIES.index(existing['frequency']) if is_edit and existing['frequency'] in VALID_EXPENSE_FREQUENCIES else 4,  # Monthly default
                key=f"{key_prefix}_freq"
            )

        with col2:
            entity = st.selectbox(
                "Entity *",
                options=entity_options,
                index=entity_options.index(existing['entity']) if is_edit and existing['entity'] in entity_options else 0,
                key=f"{key_prefix}_entity"
            )
            due_date = st.date_input(
                "Due Date *",
                value=existing['due_date'] if is_edit else date.today(),
                key=f"{key_prefix}_due"
            )
            start_date = st.date_input(
                "Start Date (optional)",
                value=existing['start_date'] if is_edit and existing.get('start_date') else None,
                key=f"{key_prefix}_start"
            )
            end_date = st.date_input(
                "End Date (optional)",
                value=existing['end_date'] if is_edit and existing.get('end_date') else None,
                key=f"{key_prefix}_end"
            )

        col3, col4 = st.columns(2)
        with col3:
            priority = st.selectbox(
                "Priority",
                options=[1, 2, 3, 4],
                index=(existing['priority'] - 1) if is_edit else 2,
                format_func=lambda x: {1: "1 - Critical (Payroll)", 2: "2 - Contractual (Loans)", 3: "3 - Medium (Software)", 4: "4 - Flexible (Operations)"}[x],
                key=f"{key_prefix}_priority"
            )
        with col4:
            status = st.selectbox(
                "Status",
                options=vendor_statuses,
                index=vendor_statuses.index(existing['status']) if is_edit and existing['status'] in vendor_statuses else 0,
                key=f"{key_prefix}_status"
            )

        notes = st.text_area(
            "Notes",
            value=existing.get('notes', '') or '' if is_edit else '',
            key=f"{key_prefix}_notes"
        )

        submitted = st.form_submit_button(
            "Update Vendor" if is_edit else "Add Vendor",
            type="primary"
        )

        if submitted:
            errors = []
            if not vendor_name.strip():
                errors.append("Vendor Name is required")
            if not amount_str.strip():
                errors.append("Amount is required")

            try:
                amount = _parse_currency_input(amount_str)
                if amount < 0:
                    errors.append("Amount cannot be negative")
            except (InvalidOperation, ValueError):
                errors.append("Amount must be a valid number")
                amount = None

            if errors:
                for error in errors:
                    st.error(error)
                return None

            result = {
                'vendor_name': vendor_name.strip(),
                'category': category,
                'amount': amount,
                'frequency': frequency,
                'due_date': due_date,
                'start_date': start_date if start_date else None,
                'end_date': end_date if end_date else None,
                'entity': entity,
                'priority': priority,
                'flexibility_days': 0,
                'status': status,
                'notes': notes.strip() if notes.strip() else None,
            }

            return result

    return None


def render_bank_balance_form(existing: Optional[Dict] = None, key_prefix: str = 'bal') -> Optional[Dict]:
    """
    Render a bank balance form.

    Args:
        existing: Existing balance data for editing (None for new)
        key_prefix: Unique key prefix for form widgets

    Returns:
        Dict of form data if submitted, None otherwise
    """
    is_edit = existing is not None
    title = "Edit Bank Balance" if is_edit else "Add Bank Balance"

    entity_options = [e for e in get_valid_entities() if e not in ('Consolidated', 'All')]

    with st.form(key=f"{key_prefix}_form", clear_on_submit=not is_edit):
        st.markdown(f"#### {title}")

        col1, col2, col3 = st.columns(3)

        with col1:
            balance_date = st.date_input(
                "Date *",
                value=existing['balance_date'] if is_edit else date.today(),
                key=f"{key_prefix}_date"
            )
        with col2:
            entity = st.selectbox(
                "Entity *",
                options=entity_options,
                index=entity_options.index(existing['entity']) if is_edit and existing['entity'] in entity_options else 0,
                key=f"{key_prefix}_entity"
            )
        with col3:
            balance_str = st.text_input(
                "Balance (₱) *",
                value=str(existing['balance']) if is_edit else '',
                placeholder="5000000.00",
                key=f"{key_prefix}_amount"
            )

        notes = st.text_input(
            "Notes",
            value=existing.get('notes', '') or '' if is_edit else '',
            key=f"{key_prefix}_notes"
        )

        submitted = st.form_submit_button(
            "Update Balance" if is_edit else "Add Balance",
            type="primary"
        )

        if submitted:
            errors = []
            if not balance_str.strip():
                errors.append("Balance amount is required")

            try:
                balance = _parse_currency_input(balance_str)
            except (InvalidOperation, ValueError):
                errors.append("Balance must be a valid number")
                balance = None

            if errors:
                for error in errors:
                    st.error(error)
                return None

            return {
                'balance_date': balance_date,
                'entity': entity,
                'balance': balance,
                'source': 'Manual Entry',
                'notes': notes.strip() if notes.strip() else None,
            }

    return None
