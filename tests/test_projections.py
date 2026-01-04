"""
Test suite for cash projections.
CRITICAL: Tests must verify 100% accuracy of financial calculations.
"""
import pytest
from datetime import date
from decimal import Decimal
from database.db_manager import db_manager
from database.models import CustomerContract, VendorContract, BankBalance
from projection_engine.cash_projector import CashProjector, ProjectionDataPoint
from projection_engine.revenue_calculator import RevenueCalculator
from projection_engine.expense_scheduler import ExpenseScheduler
from config.constants import PAYROLL_CONFIG


@pytest.fixture
def clean_database():
    """Clean database before each test."""
    db_manager.reset_database()
    yield
    # Cleanup after test if needed


@pytest.fixture
def sample_bank_balance():
    """Create sample bank balance."""
    with db_manager.session_scope() as session:
        balance_yahshua = BankBalance(
            balance_date=date(2026, 1, 1),
            entity='YAHSHUA',
            balance=Decimal('10000000.00')  # ₱10M starting cash
        )
        balance_abba = BankBalance(
            balance_date=date(2026, 1, 1),
            entity='ABBA',
            balance=Decimal('5000000.00')  # ₱5M starting cash
        )
        session.add(balance_yahshua)
        session.add(balance_abba)
    yield


@pytest.fixture
def sample_customer_contract():
    """Create sample customer contract."""
    with db_manager.session_scope() as session:
        customer = CustomerContract(
            company_name='Test Company',
            monthly_fee=Decimal('100000.00'),
            payment_plan='Monthly',
            contract_start=date(2026, 1, 1),
            contract_end=None,
            status='Active',
            who_acquired='RCBC Partner',
            entity='YAHSHUA',
            invoice_day=15,
            payment_terms_days=30,
            reliability_score=Decimal('0.80')
        )
        session.add(customer)
    yield


class TestPayrollCalculations:
    """Test payroll calculation logic (CRITICAL - NEVER FAIL)."""

    def test_payroll_always_2m_per_month(self, clean_database, sample_bank_balance):
        """Payroll must match configured amount per month for YAHSHUA."""
        projector = CashProjector()
        expense_scheduler = ExpenseScheduler()

        # Generate payroll events for 1 year
        start_date = date(2026, 1, 1)
        end_date = date(2026, 12, 31)

        payroll_events = expense_scheduler.calculate_payroll_events(
            start_date, end_date, 'YAHSHUA'
        )

        # Group by month
        monthly_totals = {}
        for event in payroll_events:
            month_key = (event.date.year, event.date.month)
            if month_key not in monthly_totals:
                monthly_totals[month_key] = Decimal('0.00')
            monthly_totals[month_key] += event.amount

        # Get expected total from config
        expected_monthly = PAYROLL_CONFIG['YAHSHUA']['15th'] + PAYROLL_CONFIG['YAHSHUA']['30th']

        # Verify each month has exactly the configured amount
        for month_key, total in monthly_totals.items():
            assert total == expected_monthly, \
                f"Payroll for {month_key} must be ₱{expected_monthly:,.2f}, got ₱{total:,.2f}"

    def test_payroll_payments_on_15th_and_30th(self, clean_database):
        """Payroll must be paid on 15th and 30th (or last day of month)."""
        expense_scheduler = ExpenseScheduler()

        start_date = date(2026, 1, 1)
        end_date = date(2026, 12, 31)

        payroll_events = expense_scheduler.calculate_payroll_events(
            start_date, end_date, 'YAHSHUA'
        )

        for event in payroll_events:
            assert event.date.day in [15, 28, 29, 30, 31], \
                f"Payroll must be on 15th or last day of month, got {event.date.day}"

    def test_payroll_amount_1m_each_payment(self, clean_database):
        """Each payroll payment must match configured amount for YAHSHUA."""
        expense_scheduler = ExpenseScheduler()

        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)

        payroll_events = expense_scheduler.calculate_payroll_events(
            start_date, end_date, 'YAHSHUA'
        )

        # Get expected amounts from config
        expected_15th = PAYROLL_CONFIG['YAHSHUA']['15th']
        expected_30th = PAYROLL_CONFIG['YAHSHUA']['30th']

        for event in payroll_events:
            if event.date.day == 15:
                assert event.amount == expected_15th, \
                    f"Payroll on 15th must be ₱{expected_15th:,.2f}, got ₱{event.amount:,.2f}"
            else:
                assert event.amount == expected_30th, \
                    f"Payroll on 30th must be ₱{expected_30th:,.2f}, got ₱{event.amount:,.2f}"

    def test_payroll_priority_is_highest(self, clean_database):
        """Payroll must have priority 1 (highest)."""
        expense_scheduler = ExpenseScheduler()

        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)

        payroll_events = expense_scheduler.calculate_payroll_events(
            start_date, end_date, 'YAHSHUA'
        )

        for event in payroll_events:
            assert event.priority == 1, \
                f"Payroll priority must be 1, got {event.priority}"
            assert event.is_payroll is True


class TestRevenueCalculations:
    """Test revenue calculation logic."""

    def test_realistic_payment_delay(self, clean_database, sample_bank_balance, sample_customer_contract):
        """Realistic scenario should apply 10-day payment delay."""
        optimistic_calc = RevenueCalculator(scenario_type='optimistic')
        realistic_calc = RevenueCalculator(scenario_type='realistic')

        invoice_date = date(2026, 2, 15)  # Invoice sent Feb 15

        # Optimistic: Net 30 = March 17
        optimistic_payment = optimistic_calc.calculate_payment_date(invoice_date, 30)
        expected_optimistic = date(2026, 3, 17)
        assert optimistic_payment == expected_optimistic, \
            f"Optimistic payment should be {expected_optimistic}, got {optimistic_payment}"

        # Realistic: Net 30 + 10 days = March 27
        realistic_payment = realistic_calc.calculate_payment_date(invoice_date, 30)
        expected_realistic = date(2026, 3, 27)
        assert realistic_payment == expected_realistic, \
            f"Realistic payment should be {expected_realistic}, got {realistic_payment}"

    def test_invoice_15_days_before_month(self, clean_database):
        """Invoice must be sent 15 days before the 1st of billing month."""
        revenue_calc = RevenueCalculator()

        # March billing → Invoice Feb 15
        billing_month = date(2026, 3, 1)
        invoice_date = revenue_calc.calculate_invoice_date(billing_month)

        assert invoice_date == date(2026, 2, 15), \
            f"Invoice for March billing must be Feb 15, got {invoice_date}"

    def test_monthly_contract_generates_12_payments(self, clean_database, sample_bank_balance, sample_customer_contract):
        """Monthly contract should generate 12 payments in a year."""
        revenue_calc = RevenueCalculator(scenario_type='optimistic')

        with db_manager.session_scope() as session:
            contracts = session.query(CustomerContract).all()
            session.expunge_all()

        start_date = date(2026, 1, 1)
        end_date = date(2026, 12, 31)

        events = revenue_calc.calculate_revenue_events(contracts, start_date, end_date)

        # Should have ~12 payment events (depending on payment timing)
        assert len(events) >= 11, \
            f"Monthly contract should generate ~12 payments per year, got {len(events)}"

    def test_payment_plan_multiplier_logic(self, clean_database, sample_bank_balance):
        """Payment amount should be Monthly Fee × number of months in payment period."""
        # Create contracts with different payment plans
        with db_manager.session_scope() as session:
            # Monthly: ₱100K × 1 = ₱100K per payment
            monthly_contract = CustomerContract(
                company_name='Monthly Client',
                monthly_fee=Decimal('100000.00'),
                payment_plan='Monthly',
                contract_start=date(2026, 1, 1),
                status='Active',
                who_acquired='RCBC Partner',
                entity='YAHSHUA'
            )
            # Quarterly: ₱100K × 3 = ₱300K per payment
            quarterly_contract = CustomerContract(
                company_name='Quarterly Client',
                monthly_fee=Decimal('100000.00'),
                payment_plan='Quarterly',
                contract_start=date(2026, 1, 1),
                status='Active',
                who_acquired='RCBC Partner',
                entity='YAHSHUA'
            )
            # Bi-annually: ₱100K × 6 = ₱600K per payment
            biannual_contract = CustomerContract(
                company_name='Bi-annual Client',
                monthly_fee=Decimal('100000.00'),
                payment_plan='Bi-annually',
                contract_start=date(2026, 1, 1),
                status='Active',
                who_acquired='RCBC Partner',
                entity='YAHSHUA'
            )
            # Annual: ₱100K × 12 = ₱1.2M per payment
            annual_contract = CustomerContract(
                company_name='Annual Client',
                monthly_fee=Decimal('100000.00'),
                payment_plan='Annual',
                contract_start=date(2026, 1, 1),
                status='Active',
                who_acquired='RCBC Partner',
                entity='YAHSHUA'
            )
            session.add(monthly_contract)
            session.add(quarterly_contract)
            session.add(biannual_contract)
            session.add(annual_contract)

        revenue_calc = RevenueCalculator(scenario_type='optimistic')

        with db_manager.session_scope() as session:
            contracts = session.query(CustomerContract).all()
            session.expunge_all()

        start_date = date(2026, 1, 1)
        end_date = date(2026, 12, 31)

        events = revenue_calc.calculate_revenue_events(contracts, start_date, end_date)

        # Verify payment amounts for each contract type
        monthly_events = [e for e in events if e.company_name == 'Monthly Client']
        quarterly_events = [e for e in events if e.company_name == 'Quarterly Client']
        biannual_events = [e for e in events if e.company_name == 'Bi-annual Client']
        annual_events = [e for e in events if e.company_name == 'Annual Client']

        # Monthly: ₱100K per payment
        assert len(monthly_events) > 0, "Monthly contract should generate events"
        for event in monthly_events:
            assert event.amount == Decimal('100000.00'), \
                f"Monthly payment should be ₱100,000.00, got ₱{event.amount:,.2f}"

        # Quarterly: ₱300K per payment (₱100K × 3 months)
        assert len(quarterly_events) > 0, "Quarterly contract should generate events"
        for event in quarterly_events:
            assert event.amount == Decimal('300000.00'), \
                f"Quarterly payment should be ₱300,000.00 (₱100K × 3), got ₱{event.amount:,.2f}"

        # Bi-annually: ₱600K per payment (₱100K × 6 months)
        assert len(biannual_events) > 0, "Bi-annual contract should generate events"
        for event in biannual_events:
            assert event.amount == Decimal('600000.00'), \
                f"Bi-annual payment should be ₱600,000.00 (₱100K × 6), got ₱{event.amount:,.2f}"

        # Annual: ₱1.2M per payment (₱100K × 12 months)
        assert len(annual_events) > 0, "Annual contract should generate events"
        for event in annual_events:
            assert event.amount == Decimal('1200000.00'), \
                f"Annual payment should be ₱1,200,000.00 (₱100K × 12), got ₱{event.amount:,.2f}"

        # Verify annual revenue is the same for all contracts (₱1.2M)
        monthly_total = sum(e.amount for e in monthly_events)
        quarterly_total = sum(e.amount for e in quarterly_events)
        biannual_total = sum(e.amount for e in biannual_events)
        annual_total = sum(e.amount for e in annual_events)

        expected_annual = Decimal('1200000.00')  # ₱100K × 12 months

        assert monthly_total == expected_annual, \
            f"Monthly contract annual revenue should be ₱1,200,000.00, got ₱{monthly_total:,.2f}"
        assert quarterly_total == expected_annual, \
            f"Quarterly contract annual revenue should be ₱1,200,000.00, got ₱{quarterly_total:,.2f}"
        assert biannual_total == expected_annual, \
            f"Bi-annual contract annual revenue should be ₱1,200,000.00, got ₱{biannual_total:,.2f}"
        assert annual_total == expected_annual, \
            f"Annual contract annual revenue should be ₱1,200,000.00, got ₱{annual_total:,.2f}"


class TestEntityIsolation:
    """Test entity isolation (CRITICAL - YAHSHUA ≠ ABBA)."""

    def test_entity_isolation_in_projections(self, clean_database, sample_bank_balance):
        """YAHSHUA and ABBA projections should be completely separate."""
        # Create customer for YAHSHUA
        with db_manager.session_scope() as session:
            yahshua_customer = CustomerContract(
                company_name='YAHSHUA Customer',
                monthly_fee=Decimal('100000.00'),
                payment_plan='Monthly',
                contract_start=date(2026, 1, 1),
                status='Active',
                who_acquired='RCBC Partner',
                entity='YAHSHUA'
            )
            abba_customer = CustomerContract(
                company_name='ABBA Customer',
                monthly_fee=Decimal('50000.00'),
                payment_plan='Monthly',
                contract_start=date(2026, 1, 1),
                status='Active',
                who_acquired='TAI',
                entity='ABBA'
            )
            session.add(yahshua_customer)
            session.add(abba_customer)

        projector = CashProjector()

        # Get contracts for each entity
        yahshua_contracts = projector.get_active_customer_contracts('YAHSHUA')
        abba_contracts = projector.get_active_customer_contracts('ABBA')

        # Verify no overlap
        yahshua_ids = set(c.id for c in yahshua_contracts)
        abba_ids = set(c.id for c in abba_contracts)

        assert yahshua_ids.isdisjoint(abba_ids), \
            "Entity isolation violated: customers appearing in both entities"

        # Verify correct assignment
        assert len(yahshua_contracts) == 1
        assert len(abba_contracts) == 1
        assert yahshua_contracts[0].company_name == 'YAHSHUA Customer'
        assert abba_contracts[0].company_name == 'ABBA Customer'

    def test_bank_balance_entity_separation(self, clean_database, sample_bank_balance):
        """Bank balances should be separate for each entity."""
        projector = CashProjector()

        yahshua_cash, _ = projector.get_starting_cash('YAHSHUA')
        abba_cash, _ = projector.get_starting_cash('ABBA')

        assert yahshua_cash == Decimal('10000000.00')
        assert abba_cash == Decimal('5000000.00')


class TestVendorExpenses:
    """Test vendor expense calculations."""

    def test_vendor_single_entity_not_split(self, clean_database, sample_bank_balance):
        """Vendors with single entity should not be split."""
        # Create a vendor for YAHSHUA only
        with db_manager.session_scope() as session:
            yahshua_vendor = VendorContract(
                vendor_name='YAHSHUA Office Rent',
                amount=Decimal('100000.00'),  # ₱100K/month
                frequency='Monthly',
                due_date=date(2026, 1, 5),
                category='Rent',
                priority=4,
                entity='YAHSHUA',  # YAHSHUA only
                status='Active'
            )
            session.add(yahshua_vendor)

        expense_scheduler = ExpenseScheduler()

        with db_manager.session_scope() as session:
            vendors = session.query(VendorContract).all()
            session.expunge_all()

        start_date = date(2026, 1, 1)
        end_date = date(2026, 1, 31)

        # Get vendor events for YAHSHUA
        yahshua_events = expense_scheduler.calculate_vendor_events(
            vendors, start_date, end_date, entity='YAHSHUA'
        )

        # Get vendor events for ABBA
        abba_events = expense_scheduler.calculate_vendor_events(
            vendors, start_date, end_date, entity='ABBA'
        )

        # Verify YAHSHUA gets the full amount
        yahshua_vendor_events = [e for e in yahshua_events if e.vendor_name == 'YAHSHUA Office Rent']
        assert len(yahshua_vendor_events) > 0, "YAHSHUA should have vendor events"

        for event in yahshua_vendor_events:
            assert event.amount == Decimal('100000.00'), \
                f"YAHSHUA should pay full amount ₱100,000.00, got ₱{event.amount:,.2f}"
            assert event.entity == 'YAHSHUA'

        # Verify ABBA has no events for this vendor
        abba_vendor_events = [e for e in abba_events if e.vendor_name == 'YAHSHUA Office Rent']
        assert len(abba_vendor_events) == 0, \
            "ABBA should not have events for YAHSHUA-only vendor"


class TestProjectionAccuracy:
    """Test overall projection accuracy."""

    def test_projection_generates_correct_number_of_periods(self, clean_database, sample_bank_balance):
        """Projection should generate correct number of periods."""
        projector = CashProjector()

        # Monthly projection for 12 months
        projection = projector.calculate_cash_projection(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            entity='YAHSHUA',
            timeframe='monthly'
        )

        assert len(projection) == 12, \
            f"12-month projection should have 12 data points, got {len(projection)}"

    def test_ending_cash_equals_starting_plus_inflows_minus_outflows(
        self, clean_database, sample_bank_balance
    ):
        """Ending cash must equal starting + inflows - outflows."""
        projector = CashProjector()

        projection = projector.calculate_cash_projection(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            entity='YAHSHUA',
            timeframe='monthly'
        )

        for point in projection:
            calculated_ending = point.starting_cash + point.inflows - point.outflows
            assert point.ending_cash == calculated_ending, \
                f"Ending cash calculation error: {point.ending_cash} != {calculated_ending}"

    def test_consolidated_projection_sums_entities(self, clean_database, sample_bank_balance):
        """Consolidated projection should sum YAHSHUA + ABBA."""
        projector = CashProjector()

        consolidated = projector.calculate_cash_projection(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            entity='Consolidated',
            timeframe='monthly'
        )

        yahshua = projector.calculate_cash_projection(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            entity='YAHSHUA',
            timeframe='monthly'
        )

        abba = projector.calculate_cash_projection(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            entity='ABBA',
            timeframe='monthly'
        )

        # Check first period
        assert consolidated[0].ending_cash == yahshua[0].ending_cash + abba[0].ending_cash, \
            "Consolidated ending cash should equal YAHSHUA + ABBA"


class TestPerformance:
    """Test performance requirements."""

    def test_projection_generation_under_5_seconds(self, clean_database, sample_bank_balance):
        """Projection generation must complete in < 5 seconds."""
        import time

        projector = CashProjector()

        start_time = time.time()

        # Generate 3-year daily projection (1095 data points)
        projection = projector.calculate_cash_projection(
            start_date=date(2026, 1, 1),
            end_date=date(2028, 12, 31),
            entity='YAHSHUA',
            timeframe='daily'
        )

        elapsed = time.time() - start_time

        assert elapsed < 5.0, \
            f"Projection generation took {elapsed:.2f}s, must be < 5.0s"
