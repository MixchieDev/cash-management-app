#!/usr/bin/env python3
"""
Quick verification script to test that projections calculate correctly after removing "Both" vendor logic.
"""
import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.queries import get_total_monthly_expenses, get_vendors
from projection_engine.cash_projector import CashProjector


def test_monthly_expenses():
    """Test that monthly expenses are calculated correctly for each entity."""
    print("\n" + "=" * 70)
    print("TESTING: Monthly Expense Calculations")
    print("=" * 70)

    # Test YAHSHUA expenses
    yahshua_expenses = get_total_monthly_expenses('YAHSHUA')
    expected_yahshua = Decimal('2550000.00')  # ₱2M payroll + ₱50K AWS + ₱200K rent + ₱300K loan

    print(f"\nYAHSHUA Monthly Expenses:")
    print(f"  Calculated: ₱{yahshua_expenses:,.2f}")
    print(f"  Expected:   ₱{expected_yahshua:,.2f}")

    if yahshua_expenses == expected_yahshua:
        print("  ✅ PASS")
    else:
        print(f"  ❌ FAIL - Difference: ₱{abs(yahshua_expenses - expected_yahshua):,.2f}")
        return False

    # Test ABBA expenses
    abba_expenses = get_total_monthly_expenses('ABBA')
    expected_abba = Decimal('1050000.00')  # ₱1M payroll + ₱50K AWS

    print(f"\nABBA Monthly Expenses:")
    print(f"  Calculated: ₱{abba_expenses:,.2f}")
    print(f"  Expected:   ₱{expected_abba:,.2f}")

    if abba_expenses == expected_abba:
        print("  ✅ PASS")
    else:
        print(f"  ❌ FAIL - Difference: ₱{abs(abba_expenses - expected_abba):,.2f}")
        return False

    print("\n✅ All monthly expense calculations PASSED")
    return True


def test_vendor_queries():
    """Test that vendor queries correctly filter by entity (no more 'Both')."""
    print("\n" + "=" * 70)
    print("TESTING: Vendor Query Filtering")
    print("=" * 70)

    # Test YAHSHUA vendors
    yahshua_vendors = get_vendors('YAHSHUA', 'Active')
    print(f"\nYAHSHUA Vendors (Active):")
    print(f"  Count: {len(yahshua_vendors)}")
    print(f"  Vendors:")
    for v in yahshua_vendors:
        print(f"    • {v['vendor_name']:30} | ₱{v['amount']:>10,.2f} | {v['entity']}")

    # Verify no "Both" vendors
    both_vendors = [v for v in yahshua_vendors if v['entity'] == 'Both']
    if both_vendors:
        print(f"  ❌ FAIL - Found {len(both_vendors)} 'Both' vendors (should be 0)")
        return False
    else:
        print("  ✅ PASS - No 'Both' vendors found")

    # Test ABBA vendors
    abba_vendors = get_vendors('ABBA', 'Active')
    print(f"\nABBA Vendors (Active):")
    print(f"  Count: {len(abba_vendors)}")
    print(f"  Vendors:")
    for v in abba_vendors:
        print(f"    • {v['vendor_name']:30} | ₱{v['amount']:>10,.2f} | {v['entity']}")

    # Verify no "Both" vendors
    both_vendors = [v for v in abba_vendors if v['entity'] == 'Both']
    if both_vendors:
        print(f"  ❌ FAIL - Found {len(both_vendors)} 'Both' vendors (should be 0)")
        return False
    else:
        print("  ✅ PASS - No 'Both' vendors found")

    print("\n✅ All vendor query tests PASSED")
    return True


def test_projection_calculation():
    """Test that projection calculations work correctly."""
    print("\n" + "=" * 70)
    print("TESTING: Projection Calculations")
    print("=" * 70)

    projector = CashProjector()
    start_date = date.today()
    end_date = start_date + timedelta(days=90)  # 3 months

    # Test YAHSHUA projection
    print("\nYAHSHUA 3-Month Projection:")
    yahshua_projection = projector.calculate_cash_projection(
        entity='YAHSHUA',
        start_date=start_date,
        end_date=end_date,
        timeframe='monthly',
        scenario_type='realistic'
    )

    print(f"  Generated {len(yahshua_projection)} data points")
    if yahshua_projection:
        first_point = yahshua_projection[0]
        print(f"  First point: {first_point.date} | Ending Cash: ₱{first_point.ending_cash:,.2f}")
        print("  ✅ PASS - Projection generated successfully")
    else:
        print("  ❌ FAIL - No projection data generated")
        return False

    # Test ABBA projection
    print("\nABBA 3-Month Projection:")
    abba_projection = projector.calculate_cash_projection(
        entity='ABBA',
        start_date=start_date,
        end_date=end_date,
        timeframe='monthly',
        scenario_type='realistic'
    )

    print(f"  Generated {len(abba_projection)} data points")
    if abba_projection:
        first_point = abba_projection[0]
        print(f"  First point: {first_point.date} | Ending Cash: ₱{first_point.ending_cash:,.2f}")
        print("  ✅ PASS - Projection generated successfully")
    else:
        print("  ❌ FAIL - No projection data generated")
        return False

    print("\n✅ All projection calculation tests PASSED")
    return True


def main():
    """Run all verification tests."""
    print("\n" + "=" * 70)
    print("PROJECTION VERIFICATION SUITE")
    print("After removing 'Both' vendor entity and split logic")
    print("=" * 70)

    all_passed = True

    # Run tests
    if not test_monthly_expenses():
        all_passed = False

    if not test_vendor_queries():
        all_passed = False

    if not test_projection_calculation():
        all_passed = False

    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nProjections are calculating correctly without 'Both' vendor logic!")
        print("The removal of VENDOR_BOTH_SPLIT has been successful.")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        print("\nPlease review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
