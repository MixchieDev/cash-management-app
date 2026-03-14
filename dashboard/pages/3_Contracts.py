"""
Contracts Page - Full CRUD for Customer Contracts, Vendor Contracts,
Bank Balances, and Payment Overrides.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import date, timedelta
from decimal import Decimal

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.authentication import require_auth, require_permission, check_permission
from config.constants import PAYMENT_PLAN_FREQUENCIES
from database.queries import (
    get_customers, get_vendors, get_customer_by_id, get_vendor_by_id,
    create_customer_contract, update_customer_contract, delete_customer_contract,
    create_vendor_contract, update_vendor_contract, delete_vendor_contract,
    get_all_bank_balances, create_bank_balance, update_bank_balance, delete_bank_balance,
    get_payment_overrides, create_payment_override, delete_payment_override,
)
from utils.currency_formatter import format_currency
from dashboard.components.styling import load_css, page_header, kpi_card, empty_state
from dashboard.components.shared_state import get_entity_options, get_selected_entity
from dashboard.components.contract_forms import (
    render_customer_form, render_vendor_form, render_bank_balance_form,
)
from dashboard.components.export import export_to_csv
from dashboard.theme import COLORS

# ═══════════════════════════════════════════════════════════════════
# PAGE SETUP
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Contracts - JESUS Company",
    page_icon="₱",
    layout="wide"
)

load_css()
require_auth()
require_permission('view_contracts')

can_edit_contracts = check_permission('edit_contracts')
can_manage_overrides = check_permission('manage_overrides')

page_header("Contract Management", "Add, edit, and manage all contracts and balances")

# ═══════════════════════════════════════════════════════════════════
# ENTITY FILTER (prominent, on-page)
# ═══════════════════════════════════════════════════════════════════
entity_options = get_entity_options()
current_entity = get_selected_entity()
if current_entity not in entity_options:
    current_entity = entity_options[0]

selected_entity = st.selectbox(
    "Filter by Entity",
    options=entity_options,
    index=entity_options.index(current_entity),
    key="contracts_entity_filter",
)
st.session_state['global_entity'] = selected_entity

entity_query = None if selected_entity in ('Consolidated', 'All') else selected_entity

# ═══════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════
tab_customers, tab_vendors, tab_balances, tab_overrides = st.tabs([
    "Customer Contracts", "Vendor Contracts", "Bank Balances", "Payment Overrides"
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1: CUSTOMER CONTRACTS
# ═══════════════════════════════════════════════════════════════════
with tab_customers:
    with st.expander("Guide"):
        st.markdown("""
- Each customer has a **monthly fee**, **payment plan** (Monthly/Quarterly/Annual), and a **due day** (from contract start or invoice_day)
- Revenue is projected on the due day each billing period — e.g. Quarterly plan pays 3× the monthly fee every 3 months
- In the **Realistic** scenario, a late-payment delay is added to every customer's due date
- **Deactivating** a customer removes their revenue from future projections
""")

    # Check if we're in EDIT mode — show edit form full-width, hide everything else
    if st.session_state.get('editing_customer_id'):
        edit_id = st.session_state['editing_customer_id']
        existing = get_customer_by_id(edit_id)
        if existing:
            # Back button at top
            if st.button("← Back to Customer List", key="back_from_edit_cust"):
                st.session_state.pop('editing_customer_id', None)
                st.rerun()

            st.markdown(f"### Editing: {existing['company_name']}")
            form_data = render_customer_form(existing=existing, key_prefix=f'edit_cust_{edit_id}')
            if form_data:
                try:
                    update_customer_contract(edit_id, form_data)
                    st.success(f"Updated {form_data['company_name']}")
                    st.session_state.pop('editing_customer_id', None)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        else:
            st.error("Customer not found")
            st.session_state.pop('editing_customer_id', None)

    # Check if we're in ADD mode — show add form full-width
    elif st.session_state.get('show_add_customer_form'):
        if st.button("← Back to Customer List", key="back_from_add_cust"):
            st.session_state['show_add_customer_form'] = False
            st.rerun()

        form_data = render_customer_form(key_prefix='add_cust')
        if form_data:
            try:
                form_data['source'] = 'manual'
                result = create_customer_contract(form_data)
                st.success(f"Created contract for {result['company_name']}")
                st.session_state['show_add_customer_form'] = False
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    # LIST mode — show table with inline actions
    else:
        col_search, col_reset, col_add = st.columns([3, 1, 1])
        with col_search:
            search_cust = st.text_input(
                "Search customers",
                placeholder="Type to filter by company name...",
                key="search_customers",
                label_visibility="collapsed"
            )
        with col_reset:
            if st.button("Reset Table", key="reset_cust_table", use_container_width=True):
                if 'cust_table_select' in st.session_state:
                    del st.session_state['cust_table_select']
                st.rerun()
        with col_add:
            if st.button("+ Add Customer", type="primary", use_container_width=True):
                st.session_state['show_add_customer_form'] = True
                st.rerun()

        try:
            customers = get_customers(entity=entity_query, status='Active')

            if search_cust:
                customers = [c for c in customers if search_cust.lower() in c['company_name'].lower()]

            if customers:
                # Build table data
                customer_data = []
                for c in customers:
                    multiplier = PAYMENT_PLAN_FREQUENCIES.get(c['payment_plan'], 1)
                    payment_amount = c['monthly_fee'] * multiplier
                    customer_data.append({
                        'Customer': c['company_name'],
                        'Monthly Fee': format_currency(c['monthly_fee']),
                        'Plan': c['payment_plan'],
                        'Payment': format_currency(payment_amount),
                        'Entity': c['entity'],
                        'Start': c['contract_start'].strftime('%Y-%m-%d') if c['contract_start'] else 'N/A',
                        'End': c['contract_end'].strftime('%Y-%m-%d') if c['contract_end'] else 'Ongoing',
                    })

                df = pd.DataFrame(customer_data)

                # Selectable table — click rows to select (multi-select supported)
                st.caption("Click rows to select them, then use the buttons below.")
                event = st.dataframe(
                    df, width='stretch', hide_index=True,
                    on_select="rerun",
                    selection_mode="multi-row",
                    key="cust_table_select",
                )

                # Determine selected rows
                selected_rows = event.selection.rows if event and event.selection else []
                selected_custs = [customers[i] for i in selected_rows]
                selected_cust = selected_custs[0] if len(selected_custs) == 1 else None
                selection_count = len(selected_custs)

                # Action buttons
                col_edit, col_deact, col_info = st.columns([1, 1, 4])
                with col_edit:
                    edit_label = f"Edit — {selected_cust['company_name']}" if selected_cust else "Edit"
                    if st.button(
                        edit_label,
                        key="edit_cust_btn",
                        use_container_width=True,
                        type="primary",
                        disabled=len(selected_custs) != 1,
                    ):
                        st.session_state['editing_customer_id'] = selected_cust['id']
                        st.rerun()
                with col_deact:
                    deact_label = f"Deactivate ({selection_count})" if selection_count > 1 else "Deactivate"
                    if st.button(
                        deact_label,
                        key="deact_cust_btn",
                        use_container_width=True,
                        type="primary",
                        disabled=selection_count == 0,
                    ):
                        st.session_state['confirm_deact_customers'] = [c['id'] for c in selected_custs]
                with col_info:
                    if selection_count == 0:
                        st.caption("Select one or more rows from the table above")
                    elif selection_count > 1:
                        st.caption(f"{selection_count} selected — Edit requires single selection")

                # Deactivation confirmation (supports multi)
                if st.session_state.get('confirm_deact_customers'):
                    deact_ids = st.session_state['confirm_deact_customers']
                    deact_names = []
                    for did in deact_ids:
                        dc = get_customer_by_id(did)
                        deact_names.append(dc['company_name'] if dc else f"ID {did}")
                    names_str = ", ".join(f"**{n}**" for n in deact_names)
                    st.warning(f"Are you sure you want to deactivate {names_str}?")
                    col_y, col_n, _ = st.columns([1, 1, 4])
                    with col_y:
                        if st.button("Yes, Deactivate", key="confirm_deact_cust_yes", type="primary"):
                            for did in deact_ids:
                                delete_customer_contract(did)
                            st.success(f"Deactivated {len(deact_ids)} contract(s)")
                            st.session_state.pop('confirm_deact_customers', None)
                            st.rerun()
                    with col_n:
                        if st.button("Cancel", key="confirm_deact_cust_no"):
                            st.session_state.pop('confirm_deact_customers', None)
                            st.rerun()

                # Summary metrics
                st.markdown("---")
                total_mrr = sum(c['monthly_fee'] for c in customers)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total MRR", format_currency(total_mrr))
                with col2:
                    st.metric("Annual Run Rate", format_currency(total_mrr * 12))
                with col3:
                    st.metric("Active Contracts", len(customers))

                export_to_csv(customer_data, "customer_contracts", label="Export Customers CSV")

            else:
                empty_state("No customer contracts found", "Click '+ Add Customer' to create one", "👤")

        except Exception as e:
            st.error(f"Error loading customers: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# TAB 2: VENDOR CONTRACTS
# ═══════════════════════════════════════════════════════════════════
with tab_vendors:
    with st.expander("Guide"):
        st.markdown("""
- Each vendor has an **amount**, **frequency** (Monthly/Quarterly/Annual/One-time), **due day**, and **priority** (1-4)
- **Priority 1** (Payroll) is always paid first — never delayed. Priority 4 (Operations) has the most flexibility
- The **Monthly Equiv.** column normalizes all frequencies so you can compare costs (e.g. Annual ÷ 12)
- **Deactivating** a vendor removes their expenses from future projections
""")

    # EDIT mode
    if st.session_state.get('editing_vendor_id'):
        edit_id = st.session_state['editing_vendor_id']
        existing = get_vendor_by_id(edit_id)
        if existing:
            if st.button("← Back to Vendor List", key="back_from_edit_vend"):
                st.session_state.pop('editing_vendor_id', None)
                st.rerun()

            st.markdown(f"### Editing: {existing['vendor_name']}")
            form_data = render_vendor_form(existing=existing, key_prefix=f'edit_vend_{edit_id}')
            if form_data:
                try:
                    update_vendor_contract(edit_id, form_data)
                    st.success(f"Updated {form_data['vendor_name']}")
                    st.session_state.pop('editing_vendor_id', None)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        else:
            st.error("Vendor not found")
            st.session_state.pop('editing_vendor_id', None)

    # ADD mode
    elif st.session_state.get('show_add_vendor_form'):
        if st.button("← Back to Vendor List", key="back_from_add_vend"):
            st.session_state['show_add_vendor_form'] = False
            st.rerun()

        form_data = render_vendor_form(key_prefix='add_vend')
        if form_data:
            try:
                form_data['source'] = 'manual'
                result = create_vendor_contract(form_data)
                st.success(f"Created contract for {result['vendor_name']}")
                st.session_state['show_add_vendor_form'] = False
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    # LIST mode
    else:
        col_search, col_reset, col_add = st.columns([3, 1, 1])
        with col_search:
            search_vend = st.text_input(
                "Search vendors",
                placeholder="Type to filter by vendor name...",
                key="search_vendors",
                label_visibility="collapsed"
            )
        with col_reset:
            if st.button("Reset Table", key="reset_vend_table", use_container_width=True):
                if 'vend_table_select' in st.session_state:
                    del st.session_state['vend_table_select']
                st.rerun()
        with col_add:
            if st.button("+ Add Vendor", type="primary", use_container_width=True):
                st.session_state['show_add_vendor_form'] = True
                st.rerun()

        try:
            vendors = get_vendors(entity=entity_query, status='Active')

            if search_vend:
                vendors = [v for v in vendors if search_vend.lower() in v['vendor_name'].lower()]

            if vendors:
                monthly_multipliers = {
                    'One-time': None,
                    'Daily': Decimal('30'),
                    'Weekly': Decimal('4.33'),
                    'Bi-weekly': Decimal('2.17'),
                    'Monthly': Decimal('1'),
                    'Quarterly': Decimal('1') / Decimal('3'),
                    'Annual': Decimal('1') / Decimal('12'),
                }

                vendor_data = []
                for v in vendors:
                    multiplier = monthly_multipliers.get(v['frequency'])
                    monthly_equiv = format_currency(v['amount'] * multiplier) if multiplier else 'One-time'
                    due_day = v['due_date'].day if v.get('due_date') else '—'
                    vendor_data.append({
                        'Vendor': v['vendor_name'],
                        'Category': v['category'],
                        'Amount': format_currency(v['amount']),
                        'Freq': v['frequency'],
                        'Due Day': f"{due_day}th" if isinstance(due_day, int) else due_day,
                        'Monthly Equiv.': monthly_equiv,
                        'Entity': v['entity'],
                        'Priority': v['priority'],
                        'Notes': v.get('notes', '') or '',
                    })

                df = pd.DataFrame(vendor_data)

                # Selectable table — click rows to select (multi-select supported)
                st.caption("Click rows to select them, then use the buttons below.")
                event = st.dataframe(
                    df, width='stretch', hide_index=True,
                    on_select="rerun",
                    selection_mode="multi-row",
                    key="vend_table_select",
                )

                # Determine selected rows
                selected_rows = event.selection.rows if event and event.selection else []
                selected_vends = [vendors[i] for i in selected_rows]
                selected_vend = selected_vends[0] if len(selected_vends) == 1 else None
                selection_count = len(selected_vends)

                # Action buttons
                col_edit, col_deact, col_info = st.columns([1, 1, 4])
                with col_edit:
                    edit_label = f"Edit — {selected_vend['vendor_name']}" if selected_vend else "Edit"
                    if st.button(
                        edit_label,
                        key="edit_vend_btn",
                        use_container_width=True,
                        type="primary",
                        disabled=len(selected_vends) != 1,
                    ):
                        st.session_state['editing_vendor_id'] = selected_vend['id']
                        st.rerun()
                with col_deact:
                    deact_label = f"Deactivate ({selection_count})" if selection_count > 1 else "Deactivate"
                    if st.button(
                        deact_label,
                        key="deact_vend_btn",
                        use_container_width=True,
                        type="primary",
                        disabled=selection_count == 0,
                    ):
                        st.session_state['confirm_deact_vendors'] = [v['id'] for v in selected_vends]
                with col_info:
                    if selection_count == 0:
                        st.caption("Select one or more rows from the table above")
                    elif selection_count > 1:
                        st.caption(f"{selection_count} selected — Edit requires single selection")

                # Deactivation confirmation (supports multi)
                if st.session_state.get('confirm_deact_vendors'):
                    deact_ids = st.session_state['confirm_deact_vendors']
                    deact_names = []
                    for did in deact_ids:
                        dv = get_vendor_by_id(did)
                        deact_names.append(dv['vendor_name'] if dv else f"ID {did}")
                    names_str = ", ".join(f"**{n}**" for n in deact_names)
                    st.warning(f"Are you sure you want to deactivate {names_str}?")
                    col_y, col_n, _ = st.columns([1, 1, 4])
                    with col_y:
                        if st.button("Yes, Deactivate", key="confirm_deact_vend_yes", type="primary"):
                            for did in deact_ids:
                                delete_vendor_contract(did)
                            st.success(f"Deactivated {len(deact_ids)} contract(s)")
                            st.session_state.pop('confirm_deact_vendors', None)
                            st.rerun()
                    with col_n:
                        if st.button("Cancel", key="confirm_deact_vend_no"):
                            st.session_state.pop('confirm_deact_vendors', None)
                            st.rerun()

                # Category summary (monthly equivalent)
                st.markdown("---")
                st.caption("Monthly equivalent by category")
                category_totals = {}
                for v in vendors:
                    cat = v['category']
                    mult = monthly_multipliers.get(v['frequency'])
                    monthly_amt = v['amount'] * mult if mult else Decimal('0')
                    category_totals[cat] = category_totals.get(cat, Decimal('0')) + monthly_amt

                cols = st.columns(min(len(category_totals), 4))
                for i, (cat, total) in enumerate(sorted(category_totals.items(), key=lambda x: x[1], reverse=True)):
                    if i < len(cols):
                        with cols[i]:
                            st.metric(cat, format_currency(total))

                export_to_csv(vendor_data, "vendor_contracts", label="Export Vendors CSV")

            else:
                empty_state("No vendor contracts found", "Click '+ Add Vendor' to create one", "🏢")

        except Exception as e:
            st.error(f"Error loading vendors: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# TAB 3: BANK BALANCES
# ═══════════════════════════════════════════════════════════════════
with tab_balances:
    with st.expander("Guide"):
        st.markdown("""
- The **latest balance per entity** is the starting point for all cash projections
- Keep balances up to date — stale balances mean inaccurate projections
- Add a new balance whenever you reconcile your actual bank account
""")

    if st.session_state.get('show_add_balance_form'):
        if st.button("← Back to Balances", key="back_from_add_bal"):
            st.session_state['show_add_balance_form'] = False
            st.rerun()

        form_data = render_bank_balance_form(key_prefix='add_bal')
        if form_data:
            try:
                result = create_bank_balance(form_data)
                st.success(f"Added balance for {result['entity']} on {result['balance_date']}")
                st.session_state['show_add_balance_form'] = False
                st.rerun()
            except Exception as e:
                st.error(str(e))
    else:
        col_header, col_add = st.columns([3, 1])
        with col_header:
            st.markdown("Track cash starting positions for each entity.")
        with col_add:
            if st.button("+ Add Balance", type="primary", use_container_width=True):
                st.session_state['show_add_balance_form'] = True
                st.rerun()

        try:
            balances = get_all_bank_balances(entity=entity_query)

            if balances:
                balance_data = []
                for b in balances:
                    balance_data.append({
                        'ID': b['id'],
                        'Date': b['balance_date'].strftime('%Y-%m-%d'),
                        'Entity': b['entity'],
                        'Balance': format_currency(b['balance']),
                        'Source': b.get('source', 'N/A'),
                        'Notes': b.get('notes', '') or '',
                    })

                df = pd.DataFrame(balance_data)
                st.dataframe(df, width='stretch', hide_index=True, column_config={
                    'ID': st.column_config.NumberColumn(width='small'),
                })

                export_to_csv(balance_data, "bank_balances", label="Export Balances CSV")

            else:
                empty_state("No bank balances found", "Click '+ Add Balance' to set a starting cash position", "🏦")

        except Exception as e:
            st.error(f"Error loading balances: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# TAB 4: PAYMENT OVERRIDES
# ═══════════════════════════════════════════════════════════════════
with tab_overrides:
    with st.expander("Guide"):
        st.markdown("""
- **Move** a payment to a different date, or **Skip** it entirely — without changing the recurring schedule
- Useful for: client requested a delay, billing dispute, holiday timing adjustment
- Overrides apply to **both** Optimistic and Realistic projections
- Overrides are one-time — the next billing cycle reverts to the normal schedule
""")

    st.markdown("Adjust individual payment dates without changing the recurring schedule.")

    with st.expander("+ Add New Override", expanded=False):
        override_type = st.radio(
            "Payment Type",
            ["Customer", "Vendor"],
            horizontal=True,
            key="new_override_type"
        )

        override_entity_options = ["YAHSHUA", "ABBA"]
        override_entity = st.selectbox(
            "Entity",
            override_entity_options,
            key="new_override_entity"
        )

        selected_payment_date = None
        contract_id_for_override = None

        if override_type == "Customer":
            cust_list = get_customers(entity=override_entity, status='Active')
            if cust_list:
                cust_map = {c['id']: c['company_name'] for c in cust_list}
                contract_id_for_override = st.selectbox(
                    "Customer",
                    options=list(cust_map.keys()),
                    format_func=lambda x: cust_map[x],
                    key="override_customer"
                )

                if contract_id_for_override:
                    customer = get_customer_by_id(contract_id_for_override)
                    if customer:
                        from projection_engine.revenue_calculator import RevenueCalculator

                        class _MockContract:
                            pass

                        mock = _MockContract()
                        for k, v in customer.items():
                            setattr(mock, k, v)

                        revenue_calc = RevenueCalculator(scenario_type='optimistic')
                        today = date.today()
                        events = revenue_calc.calculate_revenue_events(
                            [mock], today, today + timedelta(days=365)
                        )
                        payment_dates = [e.date for e in events if e.customer_id == contract_id_for_override]
                        if payment_dates:
                            selected_payment_date = st.selectbox(
                                "Payment Date to Override",
                                options=payment_dates,
                                format_func=lambda x: x.strftime('%B %d, %Y'),
                                key="override_cust_date"
                            )
            else:
                st.warning(f"No active customers for {override_entity}")

        else:  # Vendor
            vend_list = get_vendors(entity=override_entity, status='Active')
            if vend_list:
                vend_map = {v['id']: f"{v['vendor_name']} ({v['category']})" for v in vend_list}
                contract_id_for_override = st.selectbox(
                    "Vendor",
                    options=list(vend_map.keys()),
                    format_func=lambda x: vend_map[x],
                    key="override_vendor"
                )

                if contract_id_for_override:
                    vendor = get_vendor_by_id(contract_id_for_override)
                    if vendor:
                        from projection_engine.expense_scheduler import ExpenseScheduler

                        class _MockVendor:
                            pass

                        mock = _MockVendor()
                        for k, v in vendor.items():
                            setattr(mock, k, v)

                        scheduler = ExpenseScheduler()
                        today = date.today()
                        payment_dates = scheduler.get_vendor_payment_dates(
                            mock, today, today + timedelta(days=365)
                        )
                        if payment_dates:
                            selected_payment_date = st.selectbox(
                                "Payment Date to Override",
                                options=payment_dates,
                                format_func=lambda x: x.strftime('%B %d, %Y'),
                                key="override_vend_date"
                            )
            else:
                st.warning(f"No active vendors for {override_entity}")

        if selected_payment_date and contract_id_for_override:
            action = st.radio(
                "Action",
                ["Move to New Date", "Skip Payment"],
                horizontal=True,
                key="override_action"
            )

            new_date = None
            if action == "Move to New Date":
                new_date = st.date_input(
                    "New Payment Date",
                    value=selected_payment_date + timedelta(days=7),
                    min_value=date.today(),
                    key="override_new_date"
                )

            reason = st.text_area(
                "Reason (optional)",
                placeholder="e.g., Client requested delay",
                key="override_reason"
            )

            if st.button("Create Override", type="primary", key="create_override"):
                try:
                    create_payment_override(
                        override_type=override_type.lower(),
                        contract_id=contract_id_for_override,
                        original_date=selected_payment_date,
                        action="move" if action == "Move to New Date" else "skip",
                        entity=override_entity,
                        new_date=new_date,
                        reason=reason if reason else None,
                    )
                    st.success("Override created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Active overrides list
    st.markdown("### Active Overrides")

    overrides = get_payment_overrides(
        entity=entity_query,
        start_date=date.today() - timedelta(days=30),
    )

    if not overrides:
        empty_state("No payment overrides", "Use 'Add New Override' to adjust a payment date", "📅")
    else:
        for override in overrides:
            if override['override_type'] == 'customer':
                contract = get_customer_by_id(override['contract_id'])
                name = contract['company_name'] if contract else f"Customer #{override['contract_id']}"
            else:
                contract = get_vendor_by_id(override['contract_id'])
                name = contract['vendor_name'] if contract else f"Vendor #{override['contract_id']}"

            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                icon = "👤" if override['override_type'] == 'customer' else "🏢"
                st.markdown(f"**{icon} {name}** ({override['entity']})")

            with col2:
                if override['action'] == 'move':
                    st.markdown(
                        f"{override['original_date'].strftime('%b %d, %Y')} → "
                        f"**{override['new_date'].strftime('%b %d, %Y')}**"
                    )
                else:
                    st.markdown(f"~~{override['original_date'].strftime('%b %d, %Y')}~~ **SKIPPED**")

            with col3:
                if st.button("Delete", key=f"del_override_{override['id']}"):
                    delete_payment_override(override['id'])
                    st.rerun()

            if override.get('reason'):
                st.caption(f"  Reason: {override['reason']}")

            st.markdown("---")
