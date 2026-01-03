"""
Projection demo script for JESUS Company Cash Management System.
Demonstrates the projection engine with sample data.
"""
from datetime import date
from decimal import Decimal
from projection_engine.cash_projector import CashProjector
from utils.currency_formatter import format_currency


def run_projection_demo():
    """Run projection demo and display results."""
    print("\n" + "=" * 70)
    print("JESUS COMPANY CASH PROJECTION DEMO")
    print("=" * 70 + "\n")

    projector = CashProjector()

    # Run 12-month projection for YAHSHUA
    print("Generating 12-month projection for YAHSHUA Outsourcing...")
    yahshua_projection = projector.calculate_cash_projection(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        entity='YAHSHUA',
        timeframe='monthly',
        scenario_type='realistic'
    )

    print("\n" + "-" * 70)
    print("YAHSHUA OUTSOURCING - 12-MONTH CASH PROJECTION (Realistic)")
    print("-" * 70)
    print(f"{'Month':<15} {'Starting Cash':<20} {'Inflows':<20} {'Outflows':<20} {'Ending Cash':<20} {'Status'}")
    print("-" * 70)

    for point in yahshua_projection:
        status = "⚠ NEGATIVE" if point.is_negative else "✓ Positive"
        print(f"{point.date.strftime('%Y-%m-%d'):<15} "
              f"{format_currency(point.starting_cash):<20} "
              f"{format_currency(point.inflows):<20} "
              f"{format_currency(point.outflows):<20} "
              f"{format_currency(point.ending_cash):<20} "
              f"{status}")

    # Summary statistics
    total_inflows = sum(p.inflows for p in yahshua_projection)
    total_outflows = sum(p.outflows for p in yahshua_projection)
    starting_cash = yahshua_projection[0].starting_cash
    ending_cash = yahshua_projection[-1].ending_cash
    cash_change = ending_cash - starting_cash

    print("-" * 70)
    print("\nSUMMARY:")
    print(f"  Starting Cash (Jan 1):  {format_currency(starting_cash)}")
    print(f"  Total Inflows (12 mo):  {format_currency(total_inflows)}")
    print(f"  Total Outflows (12 mo): {format_currency(total_outflows)}")
    print(f"  Ending Cash (Dec 31):   {format_currency(ending_cash)}")
    print(f"  Net Change:             {format_currency(cash_change)}")

    if cash_change > 0:
        print(f"\n✓ Positive cash growth of {format_currency(cash_change)} over 12 months")
    else:
        print(f"\n⚠ Cash decreased by {format_currency(abs(cash_change))} over 12 months")

    # Check for negative cash months
    negative_months = [p for p in yahshua_projection if p.is_negative]
    if negative_months:
        print(f"\n⚠ WARNING: {len(negative_months)} month(s) with negative cash:")
        for p in negative_months:
            print(f"  - {p.date.strftime('%B %Y')}: {format_currency(p.ending_cash)}")
    else:
        print("\n✓ Cash flow remains positive throughout the year")

    # Run ABBA projection
    print("\n" + "-" * 70)
    print("ABBA INITIATIVE - 12-MONTH CASH PROJECTION (Realistic)")
    print("-" * 70)

    abba_projection = projector.calculate_cash_projection(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        entity='ABBA',
        timeframe='monthly',
        scenario_type='realistic'
    )

    for point in abba_projection:
        status = "⚠ NEGATIVE" if point.is_negative else "✓ Positive"
        print(f"{point.date.strftime('%Y-%m-%d'):<15} "
              f"{format_currency(point.starting_cash):<20} "
              f"{format_currency(point.inflows):<20} "
              f"{format_currency(point.outflows):<20} "
              f"{format_currency(point.ending_cash):<20} "
              f"{status}")

    # Consolidated view
    print("\n" + "=" * 70)
    print("CONSOLIDATED (YAHSHUA + ABBA) - SUMMARY")
    print("=" * 70)

    consolidated_projection = projector.calculate_cash_projection(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        entity='Consolidated',
        timeframe='monthly',
        scenario_type='realistic'
    )

    consolidated_starting = consolidated_projection[0].starting_cash
    consolidated_ending = consolidated_projection[-1].ending_cash
    consolidated_inflows = sum(p.inflows for p in consolidated_projection)
    consolidated_outflows = sum(p.outflows for p in consolidated_projection)

    print(f"\n  Starting Cash:  {format_currency(consolidated_starting)}")
    print(f"  Total Inflows:  {format_currency(consolidated_inflows)}")
    print(f"  Total Outflows: {format_currency(consolidated_outflows)}")
    print(f"  Ending Cash:    {format_currency(consolidated_ending)}")
    print(f"  Net Change:     {format_currency(consolidated_ending - consolidated_starting)}")

    print("\n" + "=" * 70)
    print("PROJECTION DEMO COMPLETE")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    run_projection_demo()
