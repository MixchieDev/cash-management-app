"""
Sample data generator for JESUS Company Cash Management System.
Generates realistic test data for development and testing.
"""
from datetime import date, timedelta
from decimal import Decimal
import random
from dateutil.relativedelta import relativedelta

from database.db_manager import db_manager
from database.models import (
    CustomerContract, VendorContract, BankBalance,
    Scenario, ScenarioChange
)


def generate_sample_data(num_customers: int = 50, num_vendors: int = 20):
    """
    Generate comprehensive sample data.

    Args:
        num_customers: Number of customer contracts to generate
        num_vendors: Number of vendor contracts to generate
    """
    print("\n" + "=" * 70)
    print("GENERATING SAMPLE DATA")
    print("=" * 70 + "\n")

    # Initialize database
    print("Initializing database schema...")
    db_manager.init_schema()

    with db_manager.session_scope() as session:
        # Clear existing data
        session.query(CustomerContract).delete()
        session.query(VendorContract).delete()
        session.query(BankBalance).delete()
        session.query(ScenarioChange).delete()
        session.query(Scenario).delete()

    # Generate bank balances
    generate_bank_balances()

    # Generate customer contracts
    generate_customer_contracts(num_customers)

    # Generate vendor contracts
    generate_vendor_contracts(num_vendors)

    # Generate sample scenarios
    generate_sample_scenarios()

    print("\n" + "=" * 70)
    print("SAMPLE DATA GENERATION COMPLETE")
    print("=" * 70 + "\n")


def generate_bank_balances():
    """Generate bank balance records."""
    print("Generating bank balances...")

    balances = [
        {
            'balance_date': date(2026, 1, 1),
            'entity': 'YAHSHUA',
            'balance': Decimal('15000000.00'),  # ₱15M starting cash
            'source': 'Sample Data',
            'notes': 'Initial balance for YAHSHUA Outsourcing'
        },
        {
            'balance_date': date(2026, 1, 1),
            'entity': 'ABBA',
            'balance': Decimal('8000000.00'),  # ₱8M starting cash
            'source': 'Sample Data',
            'notes': 'Initial balance for ABBA Initiative'
        }
    ]

    with db_manager.session_scope() as session:
        for balance_data in balances:
            balance = BankBalance(**balance_data)
            session.add(balance)

    print(f"✓ Generated {len(balances)} bank balance records")


def generate_customer_contracts(num_customers: int):
    """Generate customer contract records."""
    print(f"Generating {num_customers} customer contracts...")

    # Sample company names
    company_templates = [
        "Tech Solutions", "Digital Services", "Cloud Systems", "Data Analytics",
        "Software Development", "IT Consulting", "Web Solutions", "Mobile Apps",
        "AI Solutions", "Cyber Security", "Network Services", "DevOps Pro",
        "Code Masters", "System Integrators", "Business Intelligence", "ERP Solutions"
    ]

    # Acquisition sources with entity mapping
    yahshua_sources = ['RCBC Partner', 'Globe Partner', 'YOWI']
    abba_sources = ['TAI', 'PEI']

    payment_plans = ['Monthly', 'Quarterly', 'Annual', 'Bi-annually']

    customers = []

    for i in range(num_customers):
        # Determine entity (60% YAHSHUA, 40% ABBA)
        if random.random() < 0.6:
            entity = 'YAHSHUA'
            acquisition_source = random.choice(yahshua_sources)
        else:
            entity = 'ABBA'
            acquisition_source = random.choice(abba_sources)

        # Generate contract details
        company_name = f"{random.choice(company_templates)} {random.choice(['Inc', 'Corp', 'Ltd', 'LLC'])} #{i+1}"

        # Monthly fee: ₱20K to ₱500K
        monthly_fee = Decimal(random.randint(20000, 500000))

        # Payment plan
        payment_plan = random.choice(payment_plans)

        # Contract start: Last 12 months
        months_ago = random.randint(0, 12)
        contract_start = date(2026, 1, 1) - relativedelta(months=months_ago)

        # Contract end: 80% no end date, 20% end in future
        if random.random() < 0.8:
            contract_end = None
        else:
            months_forward = random.randint(6, 24)
            contract_end = contract_start + relativedelta(months=months_forward)

        # Status: 90% Active
        status = 'Active' if random.random() < 0.9 else random.choice(['Inactive', 'Pending'])

        customer = CustomerContract(
            company_name=company_name,
            monthly_fee=monthly_fee,
            payment_plan=payment_plan,
            contract_start=contract_start,
            contract_end=contract_end,
            status=status,
            who_acquired=acquisition_source,
            entity=entity,
            invoice_day=15,
            payment_terms_days=30,
            reliability_score=Decimal('0.80')
        )
        customers.append(customer)

    # Count before adding to session
    yahshua_count = sum(1 for c in customers if c.entity == 'YAHSHUA')
    abba_count = sum(1 for c in customers if c.entity == 'ABBA')

    with db_manager.session_scope() as session:
        for customer in customers:
            session.add(customer)

    print(f"✓ Generated {len(customers)} customer contracts")
    print(f"  - YAHSHUA: {yahshua_count} customers")
    print(f"  - ABBA: {abba_count} customers")


def generate_vendor_contracts(num_vendors: int):
    """Generate vendor contract records."""
    print(f"Generating {num_vendors} vendor contracts...")

    vendors = []

    # PAYROLL (CRITICAL - One for each entity)
    vendors.extend([
        VendorContract(
            vendor_name='Payroll - 15th',
            category='Payroll',
            amount=Decimal('1000000.00'),
            frequency='Monthly',
            due_date=date(2026, 1, 15),
            entity='YAHSHUA',
            priority=1,
            flexibility_days=0,
            status='Active'
        ),
        VendorContract(
            vendor_name='Payroll - 30th',
            category='Payroll',
            amount=Decimal('1000000.00'),
            frequency='Monthly',
            due_date=date(2026, 1, 30),
            entity='YAHSHUA',
            priority=1,
            flexibility_days=0,
            status='Active'
        ),
        VendorContract(
            vendor_name='Payroll - 15th',
            category='Payroll',
            amount=Decimal('1000000.00'),
            frequency='Monthly',
            due_date=date(2026, 1, 15),
            entity='ABBA',
            priority=1,
            flexibility_days=0,
            status='Active'
        ),
        VendorContract(
            vendor_name='Payroll - 30th',
            category='Payroll',
            amount=Decimal('1000000.00'),
            frequency='Monthly',
            due_date=date(2026, 1, 30),
            entity='ABBA',
            priority=1,
            flexibility_days=0,
            status='Active'
        )
    ])

    # Software/Tech expenses
    tech_vendors = [
        ('AWS Cloud Services', Decimal('150000.00'), 'Monthly', 'YAHSHUA', 3, 7),
        ('Google Workspace', Decimal('50000.00'), 'Monthly', 'Both', 3, 5),
        ('Microsoft 365', Decimal('30000.00'), 'Monthly', 'Both', 3, 5),
        ('Slack Premium', Decimal('25000.00'), 'Monthly', 'YAHSHUA', 3, 7),
        ('GitHub Enterprise', Decimal('40000.00'), 'Monthly', 'YAHSHUA', 3, 7),
        ('Zoom Business', Decimal('20000.00'), 'Monthly', 'Both', 3, 5),
    ]

    for vendor_name, amount, frequency, entity, priority, flexibility in tech_vendors:
        vendors.append(VendorContract(
            vendor_name=vendor_name,
            category='Software/Tech',
            amount=amount,
            frequency=frequency,
            due_date=date(2026, 1, 21),
            entity=entity,
            priority=priority,
            flexibility_days=flexibility,
            status='Active'
        ))

    # Operations expenses
    ops_vendors = [
        ('Office Rent - Manila', Decimal('300000.00'), 'Monthly', 'YAHSHUA', 4, 5),
        ('Office Rent - Cebu', Decimal('150000.00'), 'Monthly', 'ABBA', 4, 5),
        ('Electricity - Manila', Decimal('80000.00'), 'Monthly', 'YAHSHUA', 4, 10),
        ('Electricity - Cebu', Decimal('40000.00'), 'Monthly', 'ABBA', 4, 10),
        ('Internet - Manila', Decimal('25000.00'), 'Monthly', 'YAHSHUA', 4, 5),
        ('Internet - Cebu', Decimal('15000.00'), 'Monthly', 'ABBA', 4, 5),
        ('Office Supplies', Decimal('30000.00'), 'Monthly', 'Both', 4, 14),
        ('Fuel & Transportation', Decimal('50000.00'), 'Monthly', 'Both', 4, 10),
    ]

    for vendor_name, amount, frequency, entity, priority, flexibility in ops_vendors:
        vendors.append(VendorContract(
            vendor_name=vendor_name,
            category='Operations',
            amount=amount,
            frequency=frequency,
            due_date=date(2026, 1, 25),
            entity=entity,
            priority=priority,
            flexibility_days=flexibility,
            status='Active'
        ))

    # Loans
    loans = [
        ('Bank Loan - Equipment', Decimal('200000.00'), 'Monthly', 'YAHSHUA', 2, 2),
        ('Business Loan', Decimal('150000.00'), 'Monthly', 'ABBA', 2, 2),
    ]

    for vendor_name, amount, frequency, entity, priority, flexibility in loans:
        vendors.append(VendorContract(
            vendor_name=vendor_name,
            category='Loans',
            amount=amount,
            frequency=frequency,
            due_date=date(2026, 1, 10),
            entity=entity,
            priority=priority,
            flexibility_days=flexibility,
            status='Active'
        ))

    with db_manager.session_scope() as session:
        for vendor in vendors:
            session.add(vendor)

    print(f"✓ Generated {len(vendors)} vendor contracts")


def generate_sample_scenarios():
    """Generate sample scenarios for testing."""
    print("Generating sample scenarios...")

    scenarios_created = 0

    with db_manager.session_scope() as session:
        # Scenario 1: Hire 10 employees
        scenario1 = Scenario(
            scenario_name='Hire 10 Employees',
            entity='YAHSHUA',
            description='What if we hire 10 new employees at ₱50K/month?',
            created_by='CFO Mich'
        )
        session.add(scenario1)
        session.flush()

        change1 = ScenarioChange(
            scenario_id=scenario1.id,
            change_type='hiring',
            start_date=date(2026, 3, 1),
            employees=10,
            salary_per_employee=Decimal('50000.00')
        )
        session.add(change1)
        scenarios_created += 1

        # Scenario 2: Add 5 new clients
        scenario2 = Scenario(
            scenario_name='Add 5 New Clients',
            entity='YAHSHUA',
            description='What if we acquire 5 new clients at ₱100K/month?',
            created_by='CFO Mich'
        )
        session.add(scenario2)
        session.flush()

        change2 = ScenarioChange(
            scenario_id=scenario2.id,
            change_type='revenue',
            start_date=date(2026, 2, 1),
            new_clients=5,
            revenue_per_client=Decimal('100000.00')
        )
        session.add(change2)
        scenarios_created += 1

        # Scenario 3: New office investment
        scenario3 = Scenario(
            scenario_name='New Office Investment',
            entity='YAHSHUA',
            description='₱10M investment in new office space',
            created_by='CFO Mich'
        )
        session.add(scenario3)
        session.flush()

        change3 = ScenarioChange(
            scenario_id=scenario3.id,
            change_type='investment',
            start_date=date(2026, 6, 1),
            investment_amount=Decimal('10000000.00')
        )
        session.add(change3)
        scenarios_created += 1

        # Scenario 4: Combined growth scenario
        scenario4 = Scenario(
            scenario_name='Aggressive Growth Plan',
            entity='YAHSHUA',
            description='Hire 20 employees + acquire 10 new clients',
            created_by='CFO Mich'
        )
        session.add(scenario4)
        session.flush()

        change4a = ScenarioChange(
            scenario_id=scenario4.id,
            change_type='hiring',
            start_date=date(2026, 4, 1),
            employees=20,
            salary_per_employee=Decimal('50000.00')
        )
        change4b = ScenarioChange(
            scenario_id=scenario4.id,
            change_type='revenue',
            start_date=date(2026, 4, 1),
            new_clients=10,
            revenue_per_client=Decimal('120000.00')
        )
        session.add(change4a)
        session.add(change4b)
        scenarios_created += 1

    print(f"✓ Generated {scenarios_created} sample scenarios")


if __name__ == '__main__':
    generate_sample_data(num_customers=50, num_vendors=20)

    print("\nSample data ready! You can now:")
    print("1. Run tests: pytest tests/ -v")
    print("2. Generate projections: python scripts/generate_projection_demo.py")
    print("3. Start dashboard: streamlit run dashboard/app.py")
