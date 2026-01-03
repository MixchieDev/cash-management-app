"""
Test suite for scenario modeling.
Tests what-if analysis and break-even calculations.
"""
import pytest
from datetime import date
from decimal import Decimal
from database.db_manager import db_manager
from database.models import BankBalance
from projection_engine.cash_projector import CashProjector, ProjectionDataPoint
from scenario_engine.scenario_storage import ScenarioStorage
from scenario_engine.scenario_calculator import ScenarioCalculator


@pytest.fixture
def clean_database():
    """Clean database before each test."""
    db_manager.reset_database()
    yield


@pytest.fixture
def sample_bank_balance():
    """Create sample bank balance."""
    with db_manager.session_scope() as session:
        balance = BankBalance(
            balance_date=date(2026, 1, 1),
            entity='YAHSHUA',
            balance=Decimal('10000000.00')
        )
        session.add(balance)
    yield


@pytest.fixture
def baseline_projection(clean_database, sample_bank_balance):
    """Generate baseline projection."""
    projector = CashProjector()
    projection = projector.calculate_cash_projection(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        entity='YAHSHUA',
        timeframe='monthly'
    )
    return projection


class TestScenarioCreation:
    """Test scenario creation and storage."""

    def test_create_hiring_scenario(self, clean_database):
        """Test creating a hiring scenario."""
        scenario_id = ScenarioStorage.create_hiring_scenario(
            scenario_name='Hire 10 Employees',
            entity='YAHSHUA',
            employees=10,
            salary_per_employee=Decimal('50000.00'),
            start_date=date(2026, 3, 1),
            description='Test hiring scenario'
        )

        assert scenario_id > 0, "Scenario ID should be positive"

        # Retrieve scenario
        scenario = ScenarioStorage.get_scenario(scenario_id)
        assert scenario is not None
        assert scenario.scenario_name == 'Hire 10 Employees'
        assert scenario.entity == 'YAHSHUA'
        assert len(scenario.changes) == 1
        assert scenario.changes[0].change_type == 'hiring'
        assert scenario.changes[0].employees == 10

    def test_create_expense_scenario(self, clean_database):
        """Test creating an expense scenario."""
        scenario_id = ScenarioStorage.create_expense_scenario(
            scenario_name='Add Office Rent',
            entity='YAHSHUA',
            expense_name='Office Rent',
            expense_amount=Decimal('200000.00'),
            expense_frequency='Monthly',
            start_date=date(2026, 2, 1)
        )

        scenario = ScenarioStorage.get_scenario(scenario_id)
        assert scenario.changes[0].change_type == 'expense'
        assert scenario.changes[0].expense_amount == Decimal('200000.00')

    def test_create_revenue_scenario(self, clean_database):
        """Test creating a revenue scenario."""
        scenario_id = ScenarioStorage.create_revenue_scenario(
            scenario_name='Add 5 Clients',
            entity='YAHSHUA',
            new_clients=5,
            revenue_per_client=Decimal('100000.00'),
            start_date=date(2026, 4, 1)
        )

        scenario = ScenarioStorage.get_scenario(scenario_id)
        assert scenario.changes[0].change_type == 'revenue'
        assert scenario.changes[0].new_clients == 5

    def test_create_investment_scenario(self, clean_database):
        """Test creating an investment scenario."""
        scenario_id = ScenarioStorage.create_investment_scenario(
            scenario_name='New Office Investment',
            entity='YAHSHUA',
            investment_amount=Decimal('5000000.00'),
            start_date=date(2026, 6, 1)
        )

        scenario = ScenarioStorage.get_scenario(scenario_id)
        assert scenario.changes[0].change_type == 'investment'
        assert scenario.changes[0].investment_amount == Decimal('5000000.00')


class TestScenarioCalculations:
    """Test scenario application to projections."""

    def test_hiring_scenario_increases_payroll(self, baseline_projection, clean_database):
        """Hiring scenario should increase payroll expenses correctly."""
        # Create hiring scenario
        scenario_id = ScenarioStorage.create_hiring_scenario(
            scenario_name='Hire 10 Employees',
            entity='YAHSHUA',
            employees=10,
            salary_per_employee=Decimal('50000.00'),
            start_date=date(2026, 3, 1)
        )

        # Apply scenario
        calculator = ScenarioCalculator()
        scenario_projection = calculator.apply_scenario_to_projection(
            baseline_projection, scenario_id
        )

        # Find March data point (index 2 for 0-indexed list)
        march_baseline = baseline_projection[2]
        march_scenario = scenario_projection[2]

        # Expected increase: 10 employees × ₱50K = ₱500K
        expected_increase = Decimal('500000.00')
        actual_increase = march_scenario.outflows - march_baseline.outflows

        assert abs(actual_increase - expected_increase) < Decimal('0.01'), \
            f"Hiring 10 employees should increase payroll by ₱500,000, got ₱{actual_increase:,.2f}"

    def test_revenue_scenario_increases_inflows(self, baseline_projection, clean_database):
        """Revenue scenario should increase inflows correctly."""
        scenario_id = ScenarioStorage.create_revenue_scenario(
            scenario_name='Add 5 Clients',
            entity='YAHSHUA',
            new_clients=5,
            revenue_per_client=Decimal('100000.00'),
            start_date=date(2026, 4, 1)
        )

        calculator = ScenarioCalculator()
        scenario_projection = calculator.apply_scenario_to_projection(
            baseline_projection, scenario_id
        )

        # Find April data point (index 3)
        april_baseline = baseline_projection[3]
        april_scenario = scenario_projection[3]

        # Expected increase: 5 clients × ₱100K = ₱500K
        expected_increase = Decimal('500000.00')
        actual_increase = april_scenario.inflows - april_baseline.inflows

        assert abs(actual_increase - expected_increase) < Decimal('0.01'), \
            f"Adding 5 clients should increase revenue by ₱500,000, got ₱{actual_increase:,.2f}"

    def test_investment_scenario_decreases_cash(self, baseline_projection, clean_database):
        """Investment scenario should create one-time outflow."""
        scenario_id = ScenarioStorage.create_investment_scenario(
            scenario_name='Equipment Purchase',
            entity='YAHSHUA',
            investment_amount=Decimal('2000000.00'),
            start_date=date(2026, 6, 1)  # June
        )

        calculator = ScenarioCalculator()
        scenario_projection = calculator.apply_scenario_to_projection(
            baseline_projection, scenario_id
        )

        # Find June data point (index 5)
        june_baseline = baseline_projection[5]
        june_scenario = scenario_projection[5]

        # Expected increase in outflows: ₱2M
        expected_increase = Decimal('2000000.00')
        actual_increase = june_scenario.outflows - june_baseline.outflows

        assert actual_increase == expected_increase, \
            f"Investment should add ₱2,000,000 to outflows, got ₱{actual_increase:,.2f}"

    def test_scenario_ending_cash_recalculated(self, baseline_projection, clean_database):
        """After applying scenario, ending cash should be recalculated correctly."""
        scenario_id = ScenarioStorage.create_expense_scenario(
            scenario_name='Add Expense',
            entity='YAHSHUA',
            expense_name='New Expense',
            expense_amount=Decimal('100000.00'),
            expense_frequency='Monthly',
            start_date=date(2026, 1, 1)
        )

        calculator = ScenarioCalculator()
        scenario_projection = calculator.apply_scenario_to_projection(
            baseline_projection, scenario_id
        )

        # Verify ending cash calculation for each period
        for point in scenario_projection:
            expected_ending = point.starting_cash + point.inflows - point.outflows
            assert point.ending_cash == expected_ending, \
                f"Ending cash mismatch: {point.ending_cash} != {expected_ending}"


class TestBreakEvenAnalysis:
    """Test break-even calculations."""

    def test_affordable_scenario(self, baseline_projection, clean_database):
        """Scenario that stays positive should be marked as affordable."""
        # Small expense scenario (should be affordable)
        scenario_id = ScenarioStorage.create_expense_scenario(
            scenario_name='Small Expense',
            entity='YAHSHUA',
            expense_name='Small Expense',
            expense_amount=Decimal('10000.00'),
            expense_frequency='Monthly',
            start_date=date(2026, 1, 1)
        )

        calculator = ScenarioCalculator()
        break_even = calculator.calculate_break_even(baseline_projection, scenario_id)

        assert break_even['affordable'] is True, \
            "Small expense should be affordable"
        assert break_even['first_negative_date'] is None

    def test_unaffordable_scenario(self, baseline_projection, clean_database):
        """Scenario that goes negative should be marked as unaffordable."""
        # Large expense scenario (should be unaffordable)
        scenario_id = ScenarioStorage.create_expense_scenario(
            scenario_name='Huge Expense',
            entity='YAHSHUA',
            expense_name='Huge Expense',
            expense_amount=Decimal('50000000.00'),  # ₱50M per month
            expense_frequency='Monthly',
            start_date=date(2026, 1, 1)
        )

        calculator = ScenarioCalculator()
        break_even = calculator.calculate_break_even(baseline_projection, scenario_id)

        assert break_even['affordable'] is False, \
            "Huge expense should be unaffordable"
        assert break_even['first_negative_date'] is not None
        assert break_even['additional_revenue_needed'] > 0

    def test_scenario_impact_summary(self, baseline_projection, clean_database):
        """Test scenario impact summary calculation."""
        scenario_id = ScenarioStorage.create_hiring_scenario(
            scenario_name='Hire 5 Employees',
            entity='YAHSHUA',
            employees=5,
            salary_per_employee=Decimal('50000.00'),
            start_date=date(2026, 1, 1)
        )

        calculator = ScenarioCalculator()
        scenario_projection = calculator.apply_scenario_to_projection(
            baseline_projection, scenario_id
        )

        summary = calculator.calculate_scenario_impact_summary(
            baseline_projection, scenario_projection
        )

        # Verify structure
        assert 'baseline' in summary
        assert 'scenario' in summary
        assert 'difference' in summary
        assert 'percentage_change' in summary

        # Verify outflows increased
        assert summary['difference']['outflows'] > 0, \
            "Hiring scenario should increase outflows"


class TestScenarioStorage:
    """Test scenario storage operations."""

    def test_get_all_scenarios(self, clean_database):
        """Test retrieving all scenarios."""
        # Create multiple scenarios
        ScenarioStorage.create_hiring_scenario(
            'Scenario 1', 'YAHSHUA', 10, Decimal('50000'), date(2026, 1, 1)
        )
        ScenarioStorage.create_expense_scenario(
            'Scenario 2', 'ABBA', 'Rent', Decimal('200000'), 'Monthly', date(2026, 1, 1)
        )

        all_scenarios = ScenarioStorage.get_all_scenarios()
        assert len(all_scenarios) == 2

        yahshua_scenarios = ScenarioStorage.get_all_scenarios(entity='YAHSHUA')
        assert len(yahshua_scenarios) == 1

    def test_delete_scenario(self, clean_database):
        """Test deleting a scenario."""
        scenario_id = ScenarioStorage.create_hiring_scenario(
            'Test Delete', 'YAHSHUA', 5, Decimal('50000'), date(2026, 1, 1)
        )

        # Verify created
        scenario = ScenarioStorage.get_scenario(scenario_id)
        assert scenario is not None

        # Delete
        ScenarioStorage.delete_scenario(scenario_id)

        # Verify deleted
        scenario = ScenarioStorage.get_scenario(scenario_id)
        assert scenario is None

    def test_update_scenario(self, clean_database):
        """Test updating scenario details."""
        scenario_id = ScenarioStorage.create_hiring_scenario(
            'Original Name', 'YAHSHUA', 5, Decimal('50000'), date(2026, 1, 1)
        )

        # Update
        ScenarioStorage.update_scenario(
            scenario_id,
            scenario_name='Updated Name',
            description='Updated description'
        )

        # Verify
        scenario = ScenarioStorage.get_scenario(scenario_id)
        assert scenario.scenario_name == 'Updated Name'
        assert scenario.description == 'Updated description'
