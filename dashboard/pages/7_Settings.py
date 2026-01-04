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
    get_payroll_config,
    get_payment_terms_config,
    get_alert_thresholds,
    get_google_sheets_config,
    extract_spreadsheet_id
)
from utils.currency_formatter import format_currency


def check_admin_access() -> bool:
    """
    Check if current user has admin access.

    Returns:
        True if user is admin, False if viewer only
    """
    # Check session state for user role
    if 'user_role' in st.session_state:
        return st.session_state.user_role == 'admin'
    # Default to admin if no auth system yet
    return True


def render_payroll_tab(is_admin: bool) -> None:
    """
    Render payroll configuration tab.

    Args:
        is_admin: Whether user has edit access
    """
    st.subheader("Payroll Configuration")
    st.markdown("Configure payroll amounts for each entity on 15th and 30th of each month.")

    config = get_payroll_config()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### YAHSHUA Outsourcing")
        yahshua_15th = st.number_input(
            "15th Payment Amount (₱)",
            value=float(config['YAHSHUA']['15th']),
            min_value=0.0,
            step=10000.0,
            format="%.2f",
            disabled=not is_admin,
            key="payroll_yahshua_15th_input"
        )
        yahshua_30th = st.number_input(
            "30th Payment Amount (₱)",
            value=float(config['YAHSHUA']['30th']),
            min_value=0.0,
            step=10000.0,
            format="%.2f",
            disabled=not is_admin,
            key="payroll_yahshua_30th_input"
        )
        yahshua_total = yahshua_15th + yahshua_30th
        st.metric("Monthly Total", format_currency(Decimal(str(yahshua_total))))

    with col2:
        st.markdown("### ABBA Initiative")
        abba_15th = st.number_input(
            "15th Payment Amount (₱)",
            value=float(config['ABBA']['15th']),
            min_value=0.0,
            step=10000.0,
            format="%.2f",
            disabled=not is_admin,
            key="payroll_abba_15th_input"
        )
        abba_30th = st.number_input(
            "30th Payment Amount (₱)",
            value=float(config['ABBA']['30th']),
            min_value=0.0,
            step=10000.0,
            format="%.2f",
            disabled=not is_admin,
            key="payroll_abba_30th_input"
        )
        abba_total = abba_15th + abba_30th
        st.metric("Monthly Total", format_currency(Decimal(str(abba_total))))

    st.divider()
    combined_total = yahshua_total + abba_total
    st.metric("Combined Monthly Payroll", format_currency(Decimal(str(combined_total))))

    if is_admin:
        if st.button("Save Payroll Settings", type="primary", key="save_payroll"):
            success = True
            success &= set_setting('payroll_yahshua_15th', Decimal(str(yahshua_15th)), 'decimal', 'payroll', updated_by='CFO')
            success &= set_setting('payroll_yahshua_30th', Decimal(str(yahshua_30th)), 'decimal', 'payroll', updated_by='CFO')
            success &= set_setting('payroll_abba_15th', Decimal(str(abba_15th)), 'decimal', 'payroll', updated_by='CFO')
            success &= set_setting('payroll_abba_30th', Decimal(str(abba_30th)), 'decimal', 'payroll', updated_by='CFO')

            if success:
                st.success("Payroll settings saved successfully!")
                st.rerun()
            else:
                st.error("Error saving payroll settings.")


def render_entity_mapping_tab(is_admin: bool) -> None:
    """
    Render entity mapping configuration tab.

    Args:
        is_admin: Whether user has edit access
    """
    st.subheader("Entity Mapping Rules")
    st.markdown("Map acquisition sources to legal entities (YAHSHUA or ABBA).")

    mapping = get_entity_mapping()

    # Display current mappings
    st.markdown("### Current Mappings")

    # Group by entity
    yahshua_sources = [k for k, v in mapping.items() if v == 'YAHSHUA']
    abba_sources = [k for k, v in mapping.items() if v == 'ABBA']

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**YAHSHUA Outsourcing**")
        for source in yahshua_sources:
            st.markdown(f"- {source}")

    with col2:
        st.markdown("**ABBA Initiative**")
        for source in abba_sources:
            st.markdown(f"- {source}")

    st.divider()

    if is_admin:
        st.markdown("### Edit Mappings")

        # Edit existing mappings
        updated_mapping = {}
        for source, entity in mapping.items():
            col1, col2 = st.columns([2, 1])
            with col1:
                st.text(source)
            with col2:
                new_entity = st.selectbox(
                    "Entity",
                    options=['YAHSHUA', 'ABBA'],
                    index=0 if entity == 'YAHSHUA' else 1,
                    key=f"entity_map_{source}",
                    label_visibility="collapsed"
                )
                updated_mapping[source] = new_entity

        st.divider()

        # Add new mapping
        st.markdown("### Add New Mapping")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_source = st.text_input("Acquisition Source", key="new_source")
        with col2:
            new_entity = st.selectbox("Entity", options=['YAHSHUA', 'ABBA'], key="new_entity")
        with col3:
            st.write("")
            st.write("")
            if st.button("Add", key="add_mapping"):
                if new_source and new_source.strip():
                    updated_mapping[new_source.strip()] = new_entity
                    if set_setting('entity_mapping', updated_mapping, 'json', 'entity_mapping', updated_by='CFO'):
                        st.success(f"Added mapping: {new_source} → {new_entity}")
                        st.rerun()
                else:
                    st.warning("Please enter an acquisition source name.")

        st.divider()

        if st.button("Save Entity Mappings", type="primary", key="save_entity_mapping"):
            if set_setting('entity_mapping', updated_mapping, 'json', 'entity_mapping', updated_by='CFO'):
                st.success("Entity mappings saved successfully!")
                st.rerun()
            else:
                st.error("Error saving entity mappings.")


def render_payment_terms_tab(is_admin: bool) -> None:
    """
    Render payment terms configuration tab.

    Args:
        is_admin: Whether user has edit access
    """
    st.subheader("Payment Terms Configuration")
    st.markdown("Configure invoice timing and payment expectations.")

    config = get_payment_terms_config()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Invoice Timing")
        invoice_lead_days = st.number_input(
            "Invoice sent X days before month",
            value=config['invoice_lead_days'],
            min_value=1,
            max_value=28,
            step=1,
            disabled=not is_admin,
            key="invoice_lead_days_input",
            help="Invoice is sent this many days before the 1st of the billing month"
        )

        payment_terms_days = st.number_input(
            "Payment terms (Net X days)",
            value=config['payment_terms_days'],
            min_value=1,
            max_value=90,
            step=1,
            disabled=not is_admin,
            key="payment_terms_days_input",
            help="Standard payment terms in days from invoice date"
        )

    with col2:
        st.markdown("### Realistic Scenario Settings")
        realistic_delay_days = st.number_input(
            "Realistic payment delay (days)",
            value=config['realistic_delay_days'],
            min_value=0,
            max_value=30,
            step=1,
            disabled=not is_admin,
            key="realistic_delay_days_input",
            help="Extra days delay for realistic scenario projections"
        )

        default_reliability = st.number_input(
            "Default reliability (%)",
            value=config['default_reliability'],
            min_value=0,
            max_value=100,
            step=5,
            disabled=not is_admin,
            key="default_reliability_input",
            help="Default customer reliability score (100% = always on time)"
        )

    st.divider()

    # Show example calculation
    st.markdown("### Payment Timeline Example")
    st.info(f"""
    **For March billing:**
    - Invoice sent: Feb {28 - invoice_lead_days + 1} (15 days before Mar 1)
    - Optimistic payment: Mar {invoice_lead_days + payment_terms_days - 28 + 1} (Net {payment_terms_days})
    - Realistic payment: Mar {invoice_lead_days + payment_terms_days + realistic_delay_days - 28 + 1} (Net {payment_terms_days} + {realistic_delay_days} days delay)
    """)

    if is_admin:
        if st.button("Save Payment Terms", type="primary", key="save_payment_terms"):
            success = True
            success &= set_setting('invoice_lead_days', invoice_lead_days, 'integer', 'payment_terms', updated_by='CFO')
            success &= set_setting('payment_terms_days', payment_terms_days, 'integer', 'payment_terms', updated_by='CFO')
            success &= set_setting('realistic_delay_days', realistic_delay_days, 'integer', 'payment_terms', updated_by='CFO')
            success &= set_setting('default_reliability', default_reliability, 'integer', 'payment_terms', updated_by='CFO')

            if success:
                st.success("Payment terms saved successfully!")
                st.rerun()
            else:
                st.error("Error saving payment terms.")


def render_alerts_tab(is_admin: bool) -> None:
    """
    Render alert thresholds configuration tab.

    Args:
        is_admin: Whether user has edit access
    """
    st.subheader("Alert Thresholds")
    st.markdown("Configure warning and critical alert thresholds for cash monitoring.")

    thresholds = get_alert_thresholds()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Cash Balance Alerts")
        cash_warning = st.number_input(
            "Warning threshold (₱)",
            value=float(thresholds['cash_warning']),
            min_value=0.0,
            step=100000.0,
            format="%.2f",
            disabled=not is_admin,
            key="alert_cash_warning_input",
            help="Yellow warning when cash falls below this amount"
        )

        cash_critical = st.number_input(
            "Critical threshold (₱)",
            value=float(thresholds['cash_critical']),
            min_value=0.0,
            step=100000.0,
            format="%.2f",
            disabled=not is_admin,
            key="alert_cash_critical_input",
            help="Red alert when cash falls below this amount"
        )

    with col2:
        st.markdown("### Advance Warnings")
        days_advance = st.number_input(
            "Days in advance to warn",
            value=thresholds['days_advance'],
            min_value=1,
            max_value=180,
            step=1,
            disabled=not is_admin,
            key="alert_days_advance_input",
            help="Days before a cash crunch to show warning"
        )

        contract_expiry_days = st.number_input(
            "Contract expiry warning (days)",
            value=thresholds['contract_expiry_days'],
            min_value=1,
            max_value=365,
            step=1,
            disabled=not is_admin,
            key="alert_contract_expiry_input",
            help="Days before contract expiry to show warning"
        )

    st.divider()

    # Preview thresholds
    st.markdown("### Alert Preview")
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
                st.success("Alert thresholds saved successfully!")
                st.rerun()
            else:
                st.error("Error saving alert thresholds.")


def render_data_source_tab(is_admin: bool) -> None:
    """
    Render data source (Google Sheets) configuration tab.

    Args:
        is_admin: Whether user has edit access
    """
    st.subheader("Data Source Configuration")
    st.markdown("Configure Google Sheets connection for importing data.")

    config = get_google_sheets_config()

    st.markdown("### Google Sheets URL")
    sheets_url = st.text_input(
        "Spreadsheet URL",
        value=config['url'],
        disabled=not is_admin,
        key="sheets_url_input",
        help="Full URL to your Google Sheets spreadsheet"
    )

    # Extract and display spreadsheet ID
    spreadsheet_id = extract_spreadsheet_id(sheets_url)
    if spreadsheet_id:
        st.caption(f"Spreadsheet ID: `{spreadsheet_id}`")
    else:
        st.warning("Could not extract spreadsheet ID from URL")

    st.divider()

    st.markdown("### Sheet Tab Names")
    st.caption("These must match the exact tab names in your Google Sheets")

    col1, col2, col3 = st.columns(3)

    with col1:
        customers_sheet = st.text_input(
            "Customers Tab",
            value=config['customers_sheet'],
            disabled=not is_admin,
            key="customers_sheet_input"
        )

    with col2:
        vendors_sheet = st.text_input(
            "Vendors Tab",
            value=config['vendors_sheet'],
            disabled=not is_admin,
            key="vendors_sheet_input"
        )

    with col3:
        bank_balances_sheet = st.text_input(
            "Bank Balances Tab",
            value=config['bank_balances_sheet'],
            disabled=not is_admin,
            key="bank_balances_sheet_input"
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Test Connection", key="test_connection"):
            # Try to fetch data from Google Sheets
            try:
                import pandas as pd
                if spreadsheet_id:
                    # Try to read the first few rows
                    test_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={customers_sheet.replace(' ', '%20')}"
                    df = pd.read_csv(test_url, nrows=5)
                    st.success(f"Connection successful! Found {len(df.columns)} columns in {customers_sheet}")
                else:
                    st.error("Invalid spreadsheet URL")
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")

    with col2:
        if st.button("Sync Data Now", key="sync_data"):
            try:
                from data_processing.google_sheets_import import sync_all_data
                with st.spinner("Syncing data from Google Sheets..."):
                    sync_all_data()
                st.success("Data synced successfully!")
            except Exception as e:
                st.error(f"Sync failed: {str(e)}")

    if is_admin:
        st.divider()
        if st.button("Save Data Source Settings", type="primary", key="save_data_source"):
            success = True
            success &= set_setting('google_sheets_url', sheets_url, 'string', 'data_source', updated_by='CFO')
            success &= set_setting('sheet_name_customers', customers_sheet, 'string', 'data_source', updated_by='CFO')
            success &= set_setting('sheet_name_vendors', vendors_sheet, 'string', 'data_source', updated_by='CFO')
            success &= set_setting('sheet_name_bank_balances', bank_balances_sheet, 'string', 'data_source', updated_by='CFO')

            if success:
                st.success("Data source settings saved successfully!")
                st.rerun()
            else:
                st.error("Error saving data source settings.")


def render_audit_log_tab() -> None:
    """Render settings audit log tab."""
    st.subheader("Settings Change History")
    st.markdown("View all changes made to settings.")

    # Get audit log
    audit_entries = get_audit_log(limit=100)

    if not audit_entries:
        st.info("No settings changes recorded yet.")
        return

    # Display as table
    import pandas as pd
    df = pd.DataFrame(audit_entries)
    df.columns = ['Setting', 'Old Value', 'New Value', 'Changed By', 'Changed At']

    st.dataframe(df, use_container_width=True, hide_index=True)


def main() -> None:
    """Main settings page."""
    st.set_page_config(
        page_title="Settings - JESUS Cash Management",
        page_icon="",
        layout="wide"
    )

    st.title("Settings")
    st.markdown("Configure all application settings. Changes take effect immediately.")

    # Initialize settings tables if needed
    init_settings_tables()

    # Check admin access
    is_admin = check_admin_access()

    if not is_admin:
        st.warning("You have viewer access only. Contact an admin to make changes.")

    # Create tabs
    tabs = st.tabs([
        "Payroll",
        "Entity Mapping",
        "Payment Terms",
        "Alerts",
        "Data Source",
        "Audit Log"
    ])

    with tabs[0]:
        render_payroll_tab(is_admin)

    with tabs[1]:
        render_entity_mapping_tab(is_admin)

    with tabs[2]:
        render_payment_terms_tab(is_admin)

    with tabs[3]:
        render_alerts_tab(is_admin)

    with tabs[4]:
        render_data_source_tab(is_admin)

    with tabs[5]:
        render_audit_log_tab()

    # Admin-only reset option
    if is_admin:
        st.divider()
        with st.expander("Danger Zone", expanded=False):
            st.warning("These actions cannot be undone!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Reset All Settings to Defaults", type="secondary", key="reset_all"):
                    if reset_to_defaults(updated_by='CFO'):
                        st.success("All settings reset to defaults.")
                        st.rerun()
                    else:
                        st.error("Error resetting settings.")


if __name__ == "__main__":
    main()
