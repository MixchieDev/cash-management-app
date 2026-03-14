"""
Settings page for JESUS Company Cash Management System.
Allows CFO to edit all configuration directly from dashboard.
"""
import streamlit as st
from decimal import Decimal
import json

from database.settings_manager import (
    get_setting,
    set_setting,
    get_settings_by_category,
    get_audit_log,
    reset_to_defaults,
    init_settings_tables,
    get_entity_mapping,
    get_payment_terms_config,
    get_alert_thresholds,
    # Entity management functions
    init_entities_table,
    get_all_entities,
    create_entity,
    update_entity,
    get_valid_entity_codes,
)
from config.entity_mapping import get_entity_full_name, get_valid_entities
from utils.currency_formatter import format_currency
from auth.authentication import require_auth, check_permission


def check_admin_access() -> bool:
    """Check if current user has admin access (legacy compatibility)."""
    return check_permission('manage_settings')


def render_entities_tab(is_admin: bool) -> None:
    """Render entity management and mapping tab."""
    entity_codes = get_valid_entity_codes()

    # ── Entity Management ─────────────────────────────────────────
    st.subheader("Manage Entities")
    st.markdown("Add or edit legal entities.")

    init_entities_table()
    entities = get_all_entities(include_inactive=True)

    if entities:
        for entity in entities:
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
            with col1:
                st.markdown(f"**{entity['short_code']}**")
            with col2:
                new_full_name = st.text_input(
                    "Full Name",
                    value=entity['full_name'],
                    key=f"entity_name_{entity['short_code']}",
                    disabled=not is_admin,
                    label_visibility="collapsed"
                )
            with col3:
                is_active = st.checkbox(
                    "Active",
                    value=entity['is_active'],
                    key=f"entity_active_{entity['short_code']}",
                    disabled=not is_admin
                )
            with col4:
                if is_admin:
                    if st.button("Save", key=f"save_entity_{entity['short_code']}"):
                        if update_entity(entity['short_code'], full_name=new_full_name, is_active=is_active, updated_by='CFO'):
                            st.success(f"Updated {entity['short_code']}")
                            st.rerun()

    if is_admin:
        st.markdown("#### Add New Entity")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            new_code = st.text_input("Short Code", key="new_entity_code", max_chars=20)
        with col2:
            new_name = st.text_input("Full Legal Name", key="new_entity_name")
        with col3:
            st.write("")
            st.write("")
            if st.button("Add Entity", type="primary", key="add_entity"):
                if new_code and new_name:
                    if create_entity(new_code.strip().upper(), new_name.strip(), updated_by='CFO'):
                        st.success(f"Created entity: {new_code.upper()}")
                        st.rerun()
                    else:
                        st.error("Error creating entity. Code may already exist.")

    # ── Entity Mapping ────────────────────────────────────────────
    st.divider()
    st.subheader("Entity Mapping Rules")
    st.markdown("Map acquisition sources to legal entities.")

    mapping = get_entity_mapping()

    # Display current mappings grouped by entity
    entity_sources = {code: [] for code in entity_codes}
    for source, ent in mapping.items():
        if ent in entity_sources:
            entity_sources[ent].append(source)

    if entity_codes:
        cols = st.columns(len(entity_codes))
        for i, code in enumerate(entity_codes):
            with cols[i]:
                st.markdown(f"**{get_entity_full_name(code)}**")
                sources = entity_sources.get(code, [])
                if sources:
                    for source in sources:
                        st.markdown(f"- {source}")
                else:
                    st.caption("No mappings")

    if is_admin:
        st.markdown("---")
        updated_mapping = {}
        to_remove = []

        for source, ent in mapping.items():
            col1, col2, col3 = st.columns([2, 1, 0.5])
            with col1:
                st.text(source)
            with col2:
                new_entity = st.selectbox(
                    "Entity",
                    options=entity_codes,
                    index=entity_codes.index(ent) if ent in entity_codes else 0,
                    key=f"entity_map_{source}",
                    label_visibility="collapsed"
                )
                updated_mapping[source] = new_entity
            with col3:
                if st.button("X", key=f"remove_{source}", help=f"Remove {source}"):
                    to_remove.append(source)

        for source in to_remove:
            if source in updated_mapping:
                del updated_mapping[source]
            if set_setting('entity_mapping', updated_mapping, 'json', 'entity_mapping', updated_by='CFO'):
                st.success(f"Removed mapping: {source}")
                st.rerun()

        st.markdown("#### Add New Mapping")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_source = st.text_input("Acquisition Source", key="new_source")
        with col2:
            new_entity = st.selectbox("Entity", options=entity_codes, key="new_entity")
        with col3:
            st.write("")
            st.write("")
            if st.button("Add", key="add_mapping"):
                if new_source and new_source.strip():
                    updated_mapping[new_source.strip()] = new_entity
                    if set_setting('entity_mapping', updated_mapping, 'json', 'entity_mapping', updated_by='CFO'):
                        st.success(f"Added mapping: {new_source} -> {new_entity}")
                        st.rerun()

        if st.button("Save All Entity Mappings", type="primary", key="save_entity_mapping"):
            if set_setting('entity_mapping', updated_mapping, 'json', 'entity_mapping', updated_by='CFO'):
                st.success("Entity mappings saved!")
                st.rerun()


def render_payment_terms_tab(is_admin: bool) -> None:
    """Render payment terms and alert thresholds configuration tab."""
    st.subheader("Realistic Scenario Settings")
    st.markdown("Control how the **Realistic** projection differs from the Optimistic one.")

    config = get_payment_terms_config()

    realistic_delay_days = st.number_input(
        "Late Payment Delay (days)",
        value=config['realistic_delay_days'],
        min_value=0, max_value=60, step=1,
        disabled=not is_admin,
        key="realistic_delay_days_input",
        help="In the Realistic scenario, customer payments are delayed by this many days beyond their due date."
    )

    st.info(f"""
    **Optimistic** — customers pay on their due date (no delay)
    **Realistic** — customers pay **{realistic_delay_days} days late**
    """)

    with st.expander("How this affects projections"):
        st.markdown(f"""
- This delay is added to **every customer payment date** when you select the "Realistic" scenario on the Home dashboard
- Example: A customer due on the 5th of the month will show as paying on the **{5 + realistic_delay_days}th** in Realistic mode
- Vendor expenses are **not affected** — they always pay on schedule
- Adjust this based on your actual collection experience (e.g. set to 15 if clients typically pay 2 weeks late)
""")

    if is_admin:
        if st.button("Save", type="primary", key="save_payment_terms"):
            if set_setting('realistic_delay_days', realistic_delay_days, 'integer', 'payment_terms', updated_by='CFO'):
                st.success("Saved!")
                st.rerun()

    # Alert Thresholds (within this tab)
    st.divider()
    st.markdown("### Alert Thresholds")
    st.markdown("Configure warning and critical alert thresholds for cash monitoring.")

    thresholds = get_alert_thresholds()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Cash Balance Alerts")
        cash_warning = st.number_input(
            "Warning threshold",
            value=float(thresholds['cash_warning']),
            min_value=0.0, step=100000.0, format="%.2f",
            disabled=not is_admin,
            key="alert_cash_warning_input",
            help="Yellow warning when cash falls below this amount"
        )
        cash_critical = st.number_input(
            "Critical threshold",
            value=float(thresholds['cash_critical']),
            min_value=0.0, step=100000.0, format="%.2f",
            disabled=not is_admin,
            key="alert_cash_critical_input",
            help="Red alert when cash falls below this amount"
        )

    with col2:
        st.markdown("#### Advance Warnings")
        days_advance = st.number_input(
            "Days in advance to warn",
            value=thresholds['days_advance'],
            min_value=1, max_value=180, step=1,
            disabled=not is_admin,
            key="alert_days_advance_input"
        )
        contract_expiry_days = st.number_input(
            "Contract expiry warning (days)",
            value=thresholds['contract_expiry_days'],
            min_value=1, max_value=365, step=1,
            disabled=not is_admin,
            key="alert_contract_expiry_input"
        )

    # Preview
    col1, col2 = st.columns(2)
    with col1:
        st.warning(f"Warning level: {format_currency(Decimal(str(cash_warning)))}")
    with col2:
        st.error(f"Critical level: {format_currency(Decimal(str(cash_critical)))}")

    if is_admin:
        if st.button("Save Alert Thresholds", type="primary", key="save_alerts"):
            success = True
            success &= set_setting('alert_cash_warning', Decimal(str(cash_warning)), 'decimal', 'alerts', updated_by='CFO')
            success &= set_setting('alert_cash_critical', Decimal(str(cash_critical)), 'decimal', 'alerts', updated_by='CFO')
            success &= set_setting('alert_days_advance', days_advance, 'integer', 'alerts', updated_by='CFO')
            success &= set_setting('alert_contract_expiry_days', contract_expiry_days, 'integer', 'alerts', updated_by='CFO')
            if success:
                st.success("Alert thresholds saved!")
                st.rerun()


def render_data_import_tab(is_admin: bool) -> None:
    """Render CSV data import tab."""
    import pandas as pd
    from datetime import datetime
    from database.queries import (
        create_customer_contract, create_vendor_contract, create_bank_balance
    )
    from config.constants import (
        VALID_PAYMENT_PLANS, VALID_EXPENSE_CATEGORIES,
        VALID_EXPENSE_FREQUENCIES, VALID_CONTRACT_STATUSES
    )
    from config.entity_mapping import get_valid_entities

    st.subheader("Data Import")
    st.markdown("Upload CSV files to seed or bulk-import data into the system.")

    valid_entities = get_valid_entities()

    # ── Customer Contracts ────────────────────────────────────────
    st.markdown("### Customer Contracts")
    with st.expander("Expected columns", expanded=False):
        st.markdown("""
        | Column | Required | Notes |
        |--------|----------|-------|
        | Company Name | Yes | |
        | Monthly Fee | Yes | e.g. `50000` or `₱50,000` |
        | Payment Plan | Yes | """ + ", ".join(VALID_PAYMENT_PLANS) + """ |
        | Contract Start | Yes | `YYYY-MM-DD` or `MM/DD/YYYY` |
        | Contract End | No | `YYYY-MM-DD` or blank |
        | Status | Yes | """ + ", ".join(VALID_CONTRACT_STATUSES) + """ |
        | Who Acquired | Yes | Acquisition source |
        | Entity | Yes | """ + ", ".join(valid_entities) + """ |
        | Invoice Day | No | 1-28 |
        """)

    cust_file = st.file_uploader("Upload Customer Contracts CSV", type=['csv'], key="csv_customers")
    if cust_file is not None:
        try:
            df = pd.read_csv(cust_file)
            st.dataframe(df.head(10), width='stretch', hide_index=True)
            st.caption(f"{len(df)} rows found")

            if st.button("Import Customers", type="primary", key="import_customers"):
                created, skipped, errors = 0, 0, []
                for idx, row in df.iterrows():
                    try:
                        monthly_fee = _parse_csv_currency(row.get('Monthly Fee', 0))
                        contract_start = pd.to_datetime(row['Contract Start']).date()
                        contract_end = None
                        if pd.notna(row.get('Contract End', None)):
                            contract_end = pd.to_datetime(row['Contract End']).date()
                        invoice_day = int(row['Invoice Day']) if pd.notna(row.get('Invoice Day', None)) else None

                        data = {
                            'company_name': str(row['Company Name']).strip(),
                            'monthly_fee': monthly_fee,
                            'payment_plan': str(row['Payment Plan']).strip(),
                            'contract_start': contract_start,
                            'contract_end': contract_end,
                            'status': str(row.get('Status', 'Active')).strip(),
                            'who_acquired': str(row['Who Acquired']).strip(),
                            'entity': str(row['Entity']).strip(),
                            'invoice_day': invoice_day,
                            'source': 'csv_import',
                            'created_by': 'CSV Import',
                        }
                        create_customer_contract(data)
                        created += 1
                    except Exception as e:
                        errors.append(f"Row {idx + 2}: {e}")

                st.success(f"Imported {created} customer contracts.")
                if errors:
                    with st.expander(f"{len(errors)} errors"):
                        for err in errors:
                            st.text(err)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    # ── Vendor Contracts ──────────────────────────────────────────
    st.divider()
    st.markdown("### Vendor Contracts")
    with st.expander("Expected columns", expanded=False):
        st.markdown("""
        | Column | Required | Notes |
        |--------|----------|-------|
        | Vendor Name | Yes | |
        | Category | Yes | """ + ", ".join(VALID_EXPENSE_CATEGORIES) + """ |
        | Amount | Yes | e.g. `50000` or `₱50,000` |
        | Frequency | Yes | """ + ", ".join(VALID_EXPENSE_FREQUENCIES) + """ |
        | Due Date | Yes | `YYYY-MM-DD` |
        | Entity | Yes | """ + ", ".join(valid_entities) + """ or `Both` |
        | Priority | No | 1-4 |
        | Status | No | Active/Inactive |
        """)

    vendor_file = st.file_uploader("Upload Vendor Contracts CSV", type=['csv'], key="csv_vendors")
    if vendor_file is not None:
        try:
            df = pd.read_csv(vendor_file)
            st.dataframe(df.head(10), width='stretch', hide_index=True)
            st.caption(f"{len(df)} rows found")

            if st.button("Import Vendors", type="primary", key="import_vendors"):
                created, skipped, errors = 0, 0, []
                for idx, row in df.iterrows():
                    try:
                        amount = _parse_csv_currency(row.get('Amount', 0))
                        due_date = pd.to_datetime(row['Due Date']).date()
                        priority = int(row['Priority']) if pd.notna(row.get('Priority', None)) else 3

                        data = {
                            'vendor_name': str(row['Vendor Name']).strip(),
                            'category': str(row['Category']).strip(),
                            'amount': amount,
                            'frequency': str(row['Frequency']).strip(),
                            'due_date': due_date,
                            'entity': str(row['Entity']).strip(),
                            'priority': priority,
                            'status': str(row.get('Status', 'Active')).strip(),
                            'source': 'csv_import',
                            'created_by': 'CSV Import',
                        }
                        create_vendor_contract(data)
                        created += 1
                    except Exception as e:
                        errors.append(f"Row {idx + 2}: {e}")

                st.success(f"Imported {created} vendor contracts.")
                if errors:
                    with st.expander(f"{len(errors)} errors"):
                        for err in errors:
                            st.text(err)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    # ── Bank Balances ─────────────────────────────────────────────
    st.divider()
    st.markdown("### Bank Balances")
    with st.expander("Expected columns", expanded=False):
        st.markdown("""
        | Column | Required | Notes |
        |--------|----------|-------|
        | Date | Yes | `YYYY-MM-DD` |
        | Entity | Yes | """ + ", ".join(valid_entities) + """ |
        | Balance | Yes | e.g. `1500000` or `₱1,500,000` |
        """)

    balance_file = st.file_uploader("Upload Bank Balances CSV", type=['csv'], key="csv_balances")
    if balance_file is not None:
        try:
            df = pd.read_csv(balance_file)
            st.dataframe(df.head(10), width='stretch', hide_index=True)
            st.caption(f"{len(df)} rows found")

            if st.button("Import Balances", type="primary", key="import_balances"):
                created, errors = 0, []
                for idx, row in df.iterrows():
                    try:
                        balance = _parse_csv_currency(row.get('Balance', 0))
                        balance_date = pd.to_datetime(row['Date']).date()

                        data = {
                            'balance_date': balance_date,
                            'entity': str(row['Entity']).strip(),
                            'balance': balance,
                            'source': 'csv_import',
                        }
                        create_bank_balance(data)
                        created += 1
                    except Exception as e:
                        errors.append(f"Row {idx + 2}: {e}")

                st.success(f"Imported {created} bank balances.")
                if errors:
                    with st.expander(f"{len(errors)} errors"):
                        for err in errors:
                            st.text(err)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")


def _parse_csv_currency(value) -> 'Decimal':
    """Parse a CSV currency value (e.g. '₱50,000' or '50000') to Decimal."""
    from decimal import Decimal
    cleaned = str(value).replace('₱', '').replace(',', '').replace(' ', '').strip()
    if not cleaned:
        return Decimal('0')
    return Decimal(cleaned).quantize(Decimal('0.01'))


def render_audit_log_tab() -> None:
    """Render settings audit log tab."""
    st.subheader("Settings Change History")
    st.markdown("View all changes made to settings.")

    audit_entries = get_audit_log(limit=100)

    if not audit_entries:
        st.info("No settings changes recorded yet.")
        return

    import pandas as pd
    df = pd.DataFrame(audit_entries)
    df.columns = ['Setting', 'Old Value', 'New Value', 'Changed By', 'Changed At']
    st.dataframe(df, width='stretch', hide_index=True)


def main() -> None:
    """Main settings page."""
    st.set_page_config(
        page_title="Settings - JESUS Cash Management",
        page_icon="",
        layout="wide"
    )

    require_auth()

    st.title("Settings")
    st.markdown("Configure all application settings. Changes take effect immediately.")

    init_settings_tables()

    is_admin = check_admin_access()
    can_import = check_permission('import_data')
    can_delete = check_permission('delete_data')

    if not is_admin:
        st.warning("You have viewer access only. Contact an admin to make changes.")

    tabs = st.tabs([
        "Payment Terms",
        "Entities",
        "Data Import",
        "Audit Log"
    ])

    with tabs[0]:
        render_payment_terms_tab(is_admin)

    with tabs[1]:
        render_entities_tab(is_admin)

    with tabs[2]:
        render_data_import_tab(can_import)

    with tabs[3]:
        render_audit_log_tab()

    # Danger Zone - requires delete_data permission
    if can_delete:
        st.divider()
        with st.expander("Danger Zone", expanded=False):
            st.warning("These actions cannot be undone!")

            from database.queries import (
                delete_all_customer_contracts, delete_all_vendor_contracts,
                delete_all_bank_balances, delete_all_payment_overrides,
                delete_all_scenarios, delete_all_data
            )

            st.markdown("#### Delete Specific Data")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Delete All Customers", key="del_customers"):
                    st.session_state.confirm_delete = 'customers'
                if st.button("Delete All Vendors", key="del_vendors"):
                    st.session_state.confirm_delete = 'vendors'

            with col2:
                if st.button("Delete All Bank Balances", key="del_balances"):
                    st.session_state.confirm_delete = 'balances'
                if st.button("Delete All Overrides", key="del_overrides"):
                    st.session_state.confirm_delete = 'overrides'

            with col3:
                if st.button("Delete All Scenarios", key="del_scenarios"):
                    st.session_state.confirm_delete = 'scenarios'

            st.markdown("#### Delete Everything")
            if st.button("Delete ALL Data", type="primary", key="del_all"):
                st.session_state.confirm_delete = 'all'

            # Confirmation step
            if st.session_state.get('confirm_delete'):
                target = st.session_state.confirm_delete
                labels = {
                    'customers': 'all customer contracts',
                    'vendors': 'all vendor contracts',
                    'balances': 'all bank balances',
                    'overrides': 'all payment overrides',
                    'scenarios': 'all scenarios',
                    'all': 'ALL data (customers, vendors, balances, overrides, scenarios)',
                }
                st.error(f"Are you sure you want to permanently delete **{labels[target]}**? This cannot be undone.")

                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes, delete permanently", type="primary", key="confirm_yes"):
                        delete_fns = {
                            'customers': lambda: {'customers': delete_all_customer_contracts()},
                            'vendors': lambda: {'vendors': delete_all_vendor_contracts()},
                            'balances': lambda: {'bank_balances': delete_all_bank_balances()},
                            'overrides': lambda: {'overrides': delete_all_payment_overrides()},
                            'scenarios': lambda: {'scenarios': delete_all_scenarios()},
                            'all': delete_all_data,
                        }
                        results = delete_fns[target]()
                        summary = ", ".join(f"{v} {k}" for k, v in results.items())
                        st.success(f"Deleted: {summary}")
                        st.session_state.confirm_delete = None
                        st.rerun()
                with col_no:
                    if st.button("Cancel", key="confirm_no"):
                        st.session_state.confirm_delete = None
                        st.rerun()

            st.divider()
            st.markdown("#### Reset Settings")
            if st.button("Reset All Settings to Defaults", type="secondary", key="reset_all"):
                if reset_to_defaults(updated_by='CFO'):
                    st.success("All settings reset to defaults.")
                    st.rerun()


if __name__ == "__main__":
    main()
