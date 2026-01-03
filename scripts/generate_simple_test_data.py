#!/usr/bin/env python3
"""
Generate simple test data - 5 customers and 5 vendors with predictable values.
Perfect for manually verifying projections and scenarios.
"""
from datetime import date
from decimal import Decimal
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import db_manager
from database.models import CustomerContract, VendorContract, BankBalance


def clear_existing_data():
    """Clear all existing data from database."""
    print("🗑️  Clearing existing data...")

    with db_manager.session_scope() as session:
        session.query(CustomerContract).delete()
        session.query(VendorContract).delete()
        session.query(BankBalance).delete()
        session.commit()

    print("✅ Database cleared")


def generate_simple_customers():
    """Generate 5 simple customer contracts with predictable values."""

    print("\n📊 Creating 5 Test Customers...")
    print("-" * 70)

    customers = [
        {
            'company_name': 'Client A - Monthly 100K',
            'monthly_fee': Decimal('100000.00'),
            'payment_plan': 'Monthly',
            'contract_start': date(2025, 1, 1),
            'contract_end': None,
            'status': 'Active',
            'who_acquired': 'RCBC Partner',
            'entity': 'YAHSHUA',
            'invoice_day': 15,
            'payment_terms_days': 30,
            'reliability_score': Decimal('0.80'),
            'notes': 'Simple monthly client for testing'
        },
        {
            'company_name': 'Client B - Quarterly 300K',
            'monthly_fee': Decimal('300000.00'),
            'payment_plan': 'Quarterly',
            'contract_start': date(2025, 1, 1),
            'contract_end': None,
            'status': 'Active',
            'who_acquired': 'Globe Partner',
            'entity': 'YAHSHUA',
            'invoice_day': 15,
            'payment_terms_days': 30,
            'reliability_score': Decimal('0.80'),
            'notes': 'Quarterly billing - ₱300K × 3 months = ₱900K per quarter'
        },
        {
            'company_name': 'Client C - Monthly 150K',
            'monthly_fee': Decimal('150000.00'),
            'payment_plan': 'Monthly',
            'contract_start': date(2025, 1, 1),
            'contract_end': None,
            'status': 'Active',
            'who_acquired': 'TAI',
            'entity': 'ABBA',
            'invoice_day': 15,
            'payment_terms_days': 30,
            'reliability_score': Decimal('0.80'),
            'notes': 'ABBA client - monthly billing'
        },
        {
            'company_name': 'Client D - Annual 600K',
            'monthly_fee': Decimal('600000.00'),
            'payment_plan': 'Annual',
            'contract_start': date(2025, 1, 1),
            'contract_end': None,
            'status': 'Active',
            'who_acquired': 'PEI',
            'entity': 'ABBA',
            'invoice_day': 15,
            'payment_terms_days': 30,
            'reliability_score': Decimal('0.80'),
            'notes': 'Annual billing - ₱600K × 12 months = ₱7.2M per year'
        },
        {
            'company_name': 'Client E - Monthly 200K',
            'monthly_fee': Decimal('200000.00'),
            'payment_plan': 'Monthly',
            'contract_start': date(2025, 1, 1),
            'contract_end': None,
            'status': 'Active',
            'who_acquired': 'YOWI',
            'entity': 'YAHSHUA',
            'invoice_day': 15,
            'payment_terms_days': 30,
            'reliability_score': Decimal('0.80'),
            'notes': 'Another monthly client'
        }
    ]

    with db_manager.session_scope() as session:
        for customer_data in customers:
            customer = CustomerContract(**customer_data)
            session.add(customer)
            print(f"✅ {customer_data['company_name']} | {customer_data['entity']} | ₱{customer_data['monthly_fee']:,.2f}/mo ({customer_data['payment_plan']})")
        session.commit()

    print("\n💰 Expected Monthly Revenue:")
    print(f"   YAHSHUA: ₱100K + ₱200K = ₱300,000/mo (+ quarterly)")
    print(f"   ABBA: ₱150K = ₱150,000/mo (+ annual)")


def generate_simple_vendors():
    """Generate 5 simple vendor contracts."""

    print("\n💳 Creating 5 Test Vendors...")
    print("-" * 70)

    vendors = [
        # YAHSHUA Payroll - 15th
        {
            'vendor_name': 'Payroll YAHSHUA - 15th',
            'category': 'Payroll',
            'amount': Decimal('1000000.00'),
            'frequency': 'Monthly',
            'due_date': date(2025, 1, 15),
            'entity': 'YAHSHUA',
            'priority': 1,
            'flexibility_days': 0,
            'status': 'Active',
            'notes': 'Critical - First half of monthly payroll'
        },
        # YAHSHUA Payroll - 30th
        {
            'vendor_name': 'Payroll YAHSHUA - 30th',
            'category': 'Payroll',
            'amount': Decimal('1000000.00'),
            'frequency': 'Monthly',
            'due_date': date(2025, 1, 30),
            'entity': 'YAHSHUA',
            'priority': 1,
            'flexibility_days': 0,
            'status': 'Active',
            'notes': 'Critical - Second half of monthly payroll'
        },
        # ABBA Payroll - 15th
        {
            'vendor_name': 'Payroll ABBA - 15th',
            'category': 'Payroll',
            'amount': Decimal('500000.00'),
            'frequency': 'Monthly',
            'due_date': date(2025, 1, 15),
            'entity': 'ABBA',
            'priority': 1,
            'flexibility_days': 0,
            'status': 'Active',
            'notes': 'Critical - First half of monthly payroll'
        },
        # ABBA Payroll - 30th
        {
            'vendor_name': 'Payroll ABBA - 30th',
            'category': 'Payroll',
            'amount': Decimal('500000.00'),
            'frequency': 'Monthly',
            'due_date': date(2025, 1, 30),
            'entity': 'ABBA',
            'priority': 1,
            'flexibility_days': 0,
            'status': 'Active',
            'notes': 'Critical - Second half of monthly payroll'
        },
        {
            'vendor_name': 'AWS Cloud - YAHSHUA',
            'category': 'Software/Tech',
            'amount': Decimal('50000.00'),
            'frequency': 'Monthly',
            'due_date': date(2025, 1, 21),
            'entity': 'YAHSHUA',
            'priority': 3,
            'flexibility_days': 7,
            'status': 'Active',
            'notes': 'YAHSHUA share of AWS Cloud costs'
        },
        {
            'vendor_name': 'AWS Cloud - ABBA',
            'category': 'Software/Tech',
            'amount': Decimal('50000.00'),
            'frequency': 'Monthly',
            'due_date': date(2025, 1, 21),
            'entity': 'ABBA',
            'priority': 3,
            'flexibility_days': 7,
            'status': 'Active',
            'notes': 'ABBA share of AWS Cloud costs'
        },
        {
            'vendor_name': 'Office Rent',
            'category': 'Rent',
            'amount': Decimal('200000.00'),
            'frequency': 'Monthly',
            'due_date': date(2025, 1, 1),
            'entity': 'YAHSHUA',
            'priority': 4,
            'flexibility_days': 10,
            'status': 'Active',
            'notes': 'Can delay if cash tight'
        },
        {
            'vendor_name': 'BDO Loan',
            'category': 'Loans',
            'amount': Decimal('300000.00'),
            'frequency': 'Monthly',
            'due_date': date(2025, 1, 10),
            'entity': 'YAHSHUA',
            'priority': 2,
            'flexibility_days': 0,
            'status': 'Active',
            'notes': 'Contractual obligation'
        }
    ]

    with db_manager.session_scope() as session:
        for vendor_data in vendors:
            vendor = VendorContract(**vendor_data)
            session.add(vendor)
            print(f"✅ {vendor_data['vendor_name']:20} | {vendor_data['entity']:8} | ₱{vendor_data['amount']:,.2f}/mo | Priority {vendor_data['priority']}")
        session.commit()

    print("\n💸 Expected Monthly Expenses:")
    print(f"   YAHSHUA: ₱2M (payroll: ₱1M×2) + ₱50K (AWS half) + ₱200K (rent) + ₱300K (loan) = ₱2,550,000/mo")
    print(f"   ABBA: ₱1M (payroll: ₱500K×2) + ₱50K (AWS half) = ₱1,050,000/mo")


def generate_initial_balances():
    """Generate starting bank balances."""

    print("\n🏦 Creating Initial Bank Balances...")
    print("-" * 70)

    balances = [
        {
            'balance_date': date.today(),
            'entity': 'YAHSHUA',
            'balance': Decimal('10000000.00'),  # ₱10M starting
            'source': 'Test Data',
            'notes': 'Initial test balance for projection verification'
        },
        {
            'balance_date': date.today(),
            'entity': 'ABBA',
            'balance': Decimal('5000000.00'),  # ₱5M starting
            'source': 'Test Data',
            'notes': 'Initial test balance for projection verification'
        }
    ]

    with db_manager.session_scope() as session:
        for balance_data in balances:
            balance = BankBalance(**balance_data)
            session.add(balance)
            print(f"✅ {balance_data['entity']:8} | ₱{balance_data['balance']:,.2f} starting balance")
        session.commit()


def main():
    """Generate simple test data."""
    print("\n" + "=" * 70)
    print("SIMPLE TEST DATA GENERATOR")
    print("=" * 70)

    # Initialize database
    db_manager.init_schema()

    # Clear existing data
    clear_existing_data()

    # Generate new data
    generate_simple_customers()
    generate_simple_vendors()
    generate_initial_balances()

    print("\n" + "=" * 70)
    print("✅ TEST DATA GENERATION COMPLETE!")
    print("=" * 70)

    print("\n📋 Summary:")
    print("   • 5 Customers (3 YAHSHUA, 2 ABBA)")
    print("   • 8 Vendors (4 payroll + 2 AWS + 2 other)")
    print("   • 2 Bank Balances")

    print("\n💰 Monthly Cash Flow (Approximate):")
    print("   YAHSHUA:")
    print("     Revenue:  ₱300,000/mo (monthly) + quarterly + ...")
    print("     Expenses: ₱2,550,000/mo")
    print("     Net:      -₱2,250,000/mo (NEGATIVE - needs more revenue!)")
    print()
    print("   ABBA:")
    print("     Revenue:  ₱150,000/mo (monthly) + annual + ...")
    print("     Expenses: ₱1,050,000/mo")
    print("     Net:      -₱900,000/mo (NEGATIVE - needs more revenue!)")

    print("\n🎯 Expected Behavior:")
    print("   • Both entities should show declining cash over time")
    print("   • YAHSHUA burns ₱2.25M/mo → will run out of ₱10M in ~4-5 months")
    print("   • ABBA burns ₱900K/mo → will run out of ₱5M in ~5-6 months")
    print("   • Projections should show negative cash warnings")

    print("\n✨ Test Scenarios to Create:")
    print("   1. 'Add 10 Clients': Add 10 × ₱100K = ₱1M/mo revenue")
    print("      → Should improve cash runway significantly")
    print()
    print("   2. 'Hire 5 Employees': Add 5 × ₱50K = ₱250K/mo expense")
    print("      → Should worsen cash runway")
    print()
    print("   3. 'New Office Investment': ₱5M one-time expense")
    print("      → Should show immediate cash drop")

    print("\n📊 Next Steps:")
    print("   1. Navigate to Dashboard: http://localhost:8501")
    print("   2. Go to Scenario Comparison page")
    print("   3. Create test scenarios listed above")
    print("   4. Verify 'Monthly Expenses' and 'Monthly Revenue' columns")
    print("   5. Compare scenarios to see combined impact")
    print()


if __name__ == '__main__':
    main()
