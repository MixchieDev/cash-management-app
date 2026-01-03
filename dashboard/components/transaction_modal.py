"""
Transaction breakdown modal component.
Displays detailed revenue and expense events for a selected period.
"""
import streamlit as st
from datetime import date
from decimal import Decimal
from typing import List
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from projection_engine.revenue_calculator import RevenueEvent
from projection_engine.expense_scheduler import ExpenseEvent
from utils.currency_formatter import format_currency


def show_transaction_breakdown_modal(
    period_label: str,
    period_start: date,
    period_end: date,
    revenue_events: List[RevenueEvent],
    expense_events: List[ExpenseEvent],
    entity: str
):
    """
    Display modal with transaction-level breakdown.

    Args:
        period_label: Human-readable period label (e.g., "Jan 14, 2026" or "Week of Jan 12-18")
        period_start: Period start date
        period_end: Period end date
        revenue_events: Revenue events for this period
        expense_events: Expense events for this period
        entity: Entity filter
    """
    # Modal content
    with st.container():
        # Header
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"## Transaction Breakdown: {period_label}")
            st.caption(f"{period_start.strftime('%b %d, %Y')} - {period_end.strftime('%b %d, %Y')} | Entity: {entity}")
        with col2:
            if st.button("✕ Close", key="close_modal", type="secondary"):
                st.session_state.show_transaction_modal = False
                st.rerun()

        st.markdown("---")

        # Revenue Section
        st.markdown("### 💰 Revenue Inflows")

        if revenue_events:
            # Build revenue table
            revenue_data = []
            for event in revenue_events:
                revenue_data.append({
                    'Date': event.date.strftime('%Y-%m-%d'),
                    'Customer': event.company_name,
                    'Amount': format_currency(event.amount),
                    'Payment Plan': event.payment_plan,
                    'Entity': event.entity,
                    'Invoice Date': event.invoice_date.strftime('%Y-%m-%d') if event.invoice_date else 'N/A'
                })

            df_revenue = pd.DataFrame(revenue_data)

            st.dataframe(
                df_revenue,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Date': st.column_config.DateColumn('Date', format='YYYY-MM-DD'),
                    'Amount': st.column_config.TextColumn('Amount')
                }
            )

            total_revenue = sum(event.amount for event in revenue_events)
            st.metric("Total Revenue Inflows", format_currency(total_revenue))
        else:
            st.info("No revenue inflows for this period")
            total_revenue = Decimal('0.00')

        st.markdown("---")

        # Expense Section
        st.markdown("### 💸 Expense Outflows")

        if expense_events:
            # Build expense table
            expense_data = []
            for event in expense_events:
                expense_data.append({
                    'Date': event.date.strftime('%Y-%m-%d'),
                    'Vendor': event.vendor_name,
                    'Amount': format_currency(event.amount),
                    'Category': event.category,
                    'Priority': f"P{event.priority}",
                    'Entity': event.entity
                })

            df_expense = pd.DataFrame(expense_data)

            st.dataframe(
                df_expense,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Date': st.column_config.DateColumn('Date', format='YYYY-MM-DD'),
                    'Amount': st.column_config.TextColumn('Amount')
                }
            )

            total_expenses = sum(event.amount for event in expense_events)
            st.metric("Total Expense Outflows", format_currency(total_expenses))
        else:
            st.info("No expense outflows for this period")
            total_expenses = Decimal('0.00')

        st.markdown("---")

        # Summary Footer
        st.markdown("### 📊 Period Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Inflows",
                format_currency(total_revenue),
                help=f"{len(revenue_events)} revenue event(s)"
            )

        with col2:
            st.metric(
                "Total Outflows",
                format_currency(total_expenses),
                help=f"{len(expense_events)} expense event(s)"
            )

        with col3:
            net_cash_flow = total_revenue - total_expenses
            st.metric(
                "Net Cash Flow",
                format_currency(net_cash_flow),
                delta=format_currency(net_cash_flow),
                delta_color="normal" if net_cash_flow >= 0 else "inverse"
            )
