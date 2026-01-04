"""
Import real data from Google Sheets and generate validation report.

This script:
1. Clears all existing sample data
2. Imports customer contracts, vendor contracts, and bank balances from Google Sheets
3. Generates a detailed validation report
4. Shows summary statistics

Usage:
    python scripts/import_real_data.py
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import db_manager
from database.models import CustomerContract, VendorContract, BankBalance
from data_processing.google_sheets_import import sync_all_data
from utils.currency_formatter import format_currency


def clear_sample_data() -> None:
    """Clear all existing sample data from database."""
    print("\n" + "=" * 70)
    print("CLEARING EXISTING SAMPLE DATA")
    print("=" * 70 + "\n")

    with db_manager.session_scope() as session:
        customer_count = session.query(CustomerContract).count()
        vendor_count = session.query(VendorContract).count()
        balance_count = session.query(BankBalance).count()

        print(f"Deleting {customer_count} existing customer contracts...")
        session.query(CustomerContract).delete()

        print(f"Deleting {vendor_count} existing vendor contracts...")
        session.query(VendorContract).delete()

        print(f"Deleting {balance_count} existing bank balances...")
        session.query(BankBalance).delete()

    print("\n✓ All sample data cleared successfully")


def generate_validation_report() -> Dict:
    """
    Generate detailed validation report after import.

    Returns:
        Dictionary with validation statistics
    """
    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70 + "\n")

    report = {}

    with db_manager.session_scope() as session:
        # ═══════════════════════════════════════════════════════════════
        # CUSTOMER CONTRACTS
        # ═══════════════════════════════════════════════════════════════
        print("📊 CUSTOMER CONTRACTS")
        print("-" * 70)

        total_customers = session.query(CustomerContract).count()
        yahshua_customers = session.query(CustomerContract).filter_by(entity='YAHSHUA').all()
        abba_customers = session.query(CustomerContract).filter_by(entity='ABBA').all()

        # Calculate MRR (Monthly Recurring Revenue)
        yahshua_mrr = sum(c.monthly_fee for c in yahshua_customers)
        abba_mrr = sum(c.monthly_fee for c in abba_customers)
        total_mrr = yahshua_mrr + abba_mrr

        print(f"Total customers imported: {total_customers}")
        print(f"  - YAHSHUA customers: {len(yahshua_customers)}")
        print(f"  - ABBA customers: {len(abba_customers)}")
        print()
        print(f"Total MRR (Monthly Recurring Revenue): {format_currency(total_mrr)}")
        print(f"  - YAHSHUA MRR: {format_currency(yahshua_mrr)}")
        print(f"  - ABBA MRR: {format_currency(abba_mrr)}")
        print()

        # Show breakdown by payment plan
        payment_plans = session.query(
            CustomerContract.payment_plan,
            CustomerContract.entity
        ).all()

        print("Payment Plan Breakdown:")
        for plan in ['Monthly', 'Quarterly', 'Bi-annually', 'Annual', 'More than 1 year']:
            plan_count = sum(1 for p in payment_plans if p[0] == plan)
            if plan_count > 0:
                print(f"  - {plan}: {plan_count} contracts")
        print()

        report['customers'] = {
            'total': total_customers,
            'yahshua': len(yahshua_customers),
            'abba': len(abba_customers),
            'total_mrr': float(total_mrr),
            'yahshua_mrr': float(yahshua_mrr),
            'abba_mrr': float(abba_mrr)
        }

        # ═══════════════════════════════════════════════════════════════
        # VENDOR CONTRACTS
        # ═══════════════════════════════════════════════════════════════
        print("💰 VENDOR CONTRACTS")
        print("-" * 70)

        total_vendors = session.query(VendorContract).count()
        yahshua_vendors = session.query(VendorContract).filter_by(entity='YAHSHUA').all()
        abba_vendors = session.query(VendorContract).filter_by(entity='ABBA').all()

        print(f"Total vendors imported: {total_vendors}")
        print(f"  - YAHSHUA vendors: {len(yahshua_vendors)}")
        print(f"  - ABBA vendors: {len(abba_vendors)}")
        print()

        # Calculate monthly expenses by category
        print("Monthly Expenses by Category:")
        categories = ['Payroll', 'Loans', 'Software/Tech', 'Operations', 'Rent', 'Utilities']
        total_monthly_expenses = Decimal('0.00')

        for category in categories:
            category_vendors = session.query(VendorContract).filter_by(
                category=category,
                frequency='Monthly'
            ).all()

            if category_vendors:
                category_total = sum(v.amount for v in category_vendors)
                total_monthly_expenses += category_total
                print(f"  - {category}: {format_currency(category_total)}")

        print(f"\nTotal Monthly Expenses: {format_currency(total_monthly_expenses)}")
        print()

        report['vendors'] = {
            'total': total_vendors,
            'yahshua': len(yahshua_vendors),
            'abba': len(abba_vendors),
            'total_monthly_expenses': float(total_monthly_expenses)
        }

        # ═══════════════════════════════════════════════════════════════
        # BANK BALANCES
        # ═══════════════════════════════════════════════════════════════
        print("🏦 BANK BALANCES")
        print("-" * 70)

        # Get most recent balance for each entity
        yahshua_balance = session.query(BankBalance).filter_by(
            entity='YAHSHUA'
        ).order_by(BankBalance.balance_date.desc()).first()

        abba_balance = session.query(BankBalance).filter_by(
            entity='ABBA'
        ).order_by(BankBalance.balance_date.desc()).first()

        if yahshua_balance and abba_balance:
            total_cash = yahshua_balance.balance + abba_balance.balance

            print(f"Current Date: {yahshua_balance.balance_date}")
            print(f"YAHSHUA Balance: {format_currency(yahshua_balance.balance)}")
            print(f"ABBA Balance: {format_currency(abba_balance.balance)}")
            print(f"Total Cash: {format_currency(total_cash)}")

            report['bank_balances'] = {
                'date': str(yahshua_balance.balance_date),
                'yahshua': float(yahshua_balance.balance),
                'abba': float(abba_balance.balance),
                'total': float(total_cash)
            }
        else:
            print("⚠ No bank balances found")
            report['bank_balances'] = None

        print()

    print("=" * 70)
    print("✓ VALIDATION COMPLETE")
    print("=" * 70 + "\n")

    return report


def main() -> None:
    """Main execution function."""
    print("\n" + "=" * 70)
    print("IMPORT REAL DATA FROM GOOGLE SHEETS")
    print("=" * 70 + "\n")

    # Initialize database schema
    print("Initializing database schema...")
    db_manager.init_schema()
    print("✓ Database schema initialized\n")

    # Clear existing sample data
    clear_sample_data()

    # Import all data from Google Sheets
    try:
        sync_result = sync_all_data()
        print(f"\n✓ Import successful!")
        print(f"   Imported {sync_result['customers']} customers")
        print(f"   Imported {sync_result['vendors']} vendors")
        print(f"   Imported {sync_result['balances']} bank balance entries")
        print(f"   Time elapsed: {sync_result['elapsed_seconds']:.2f} seconds")

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        print("\nPossible causes:")
        print("1. Google Sheets credentials not found or invalid")
        print("2. Spreadsheet ID is incorrect")
        print("3. Sheet tab names don't match")
        print("4. Network connection issue")
        print("\nPlease check the error message above and try again.")
        sys.exit(1)

    # Generate validation report
    report = generate_validation_report()

    # Final summary
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("\n1. Review the validation report above")
    print("2. Run tests: pytest tests/ -v")
    print("3. Generate projections: python scripts/verify_projections.py")
    print("4. Start dashboard: streamlit run dashboard/app.py")
    print()


if __name__ == '__main__':
    main()
