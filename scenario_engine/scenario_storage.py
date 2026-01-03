"""
Scenario storage for JESUS Company Cash Management System.
Handles saving, retrieving, and managing scenarios.
"""
from typing import List, Dict, Optional
from datetime import datetime, date
from decimal import Decimal

from database.db_manager import db_manager
from database.models import Scenario, ScenarioChange


class ScenarioStorage:
    """Manage scenario storage and retrieval."""

    @staticmethod
    def create_scenario(
        scenario_name: str,
        entity: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> int:
        """
        Create a new scenario.

        Args:
            scenario_name: Name of the scenario
            entity: Entity ('YAHSHUA', 'ABBA', or 'Consolidated')
            description: Scenario description (optional)
            created_by: Creator name (optional)

        Returns:
            Scenario ID
        """
        with db_manager.session_scope() as session:
            scenario = Scenario(
                scenario_name=scenario_name,
                entity=entity,
                description=description,
                created_by=created_by
            )
            session.add(scenario)
            session.flush()  # Get ID before commit
            scenario_id = scenario.id

        print(f"✓ Created scenario '{scenario_name}' (ID: {scenario_id})")
        return scenario_id

    @staticmethod
    def add_scenario_change(
        scenario_id: int,
        change_type: str,
        start_date: date,
        **kwargs
    ) -> int:
        """
        Add a change to a scenario.

        Args:
            scenario_id: Scenario ID
            change_type: Type of change ('hiring', 'expense', 'revenue', 'customer_loss', 'investment')
            start_date: Start date of change
            **kwargs: Additional fields based on change type

        Returns:
            Change ID
        """
        with db_manager.session_scope() as session:
            change = ScenarioChange(
                scenario_id=scenario_id,
                change_type=change_type,
                start_date=start_date,
                **kwargs
            )
            session.add(change)
            session.flush()
            change_id = change.id

        print(f"✓ Added {change_type} change to scenario {scenario_id}")
        return change_id

    @staticmethod
    def get_scenario(scenario_id: int) -> Optional[Scenario]:
        """
        Get scenario by ID.

        Args:
            scenario_id: Scenario ID

        Returns:
            Scenario object or None
        """
        with db_manager.session_scope() as session:
            scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
            if scenario:
                session.expunge_all()
            return scenario

    @staticmethod
    def get_all_scenarios(entity: Optional[str] = None) -> List[Scenario]:
        """
        Get all scenarios, optionally filtered by entity.

        Args:
            entity: Filter by entity (optional)

        Returns:
            List of scenarios
        """
        with db_manager.session_scope() as session:
            query = session.query(Scenario)

            if entity:
                query = query.filter(Scenario.entity == entity)

            scenarios = query.order_by(Scenario.created_at.desc()).all()
            session.expunge_all()

            return scenarios

    @staticmethod
    def delete_scenario(scenario_id: int):
        """
        Delete a scenario and all its changes.

        Args:
            scenario_id: Scenario ID
        """
        with db_manager.session_scope() as session:
            scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()
            if scenario:
                session.delete(scenario)
                print(f"✓ Deleted scenario {scenario_id}")
            else:
                print(f"⚠ Scenario {scenario_id} not found")

    @staticmethod
    def update_scenario(
        scenario_id: int,
        scenario_name: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Update scenario details.

        Args:
            scenario_id: Scenario ID
            scenario_name: New name (optional)
            description: New description (optional)
        """
        with db_manager.session_scope() as session:
            scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()

            if not scenario:
                raise ValueError(f"Scenario {scenario_id} not found")

            if scenario_name:
                scenario.scenario_name = scenario_name
            if description is not None:
                scenario.description = description

            scenario.updated_at = datetime.utcnow()

        print(f"✓ Updated scenario {scenario_id}")

    @staticmethod
    def create_hiring_scenario(
        scenario_name: str,
        entity: str,
        employees: int,
        salary_per_employee: Decimal,
        start_date: date,
        end_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> int:
        """
        Create a hiring scenario.

        Args:
            scenario_name: Scenario name
            entity: Entity
            employees: Number of employees to hire
            salary_per_employee: Salary per employee
            start_date: Hire date
            end_date: End date (optional)
            description: Description (optional)

        Returns:
            Scenario ID
        """
        # Create scenario
        scenario_id = ScenarioStorage.create_scenario(
            scenario_name=scenario_name,
            entity=entity,
            description=description or f"Hire {employees} employees at ₱{salary_per_employee:,.2f}/month"
        )

        # Add hiring change
        ScenarioStorage.add_scenario_change(
            scenario_id=scenario_id,
            change_type='hiring',
            start_date=start_date,
            end_date=end_date,
            employees=employees,
            salary_per_employee=salary_per_employee
        )

        return scenario_id

    @staticmethod
    def create_expense_scenario(
        scenario_name: str,
        entity: str,
        expense_name: str,
        expense_amount: Decimal,
        expense_frequency: str,
        start_date: date,
        end_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> int:
        """
        Create a recurring expense scenario.

        Args:
            scenario_name: Scenario name
            entity: Entity
            expense_name: Name of expense
            expense_amount: Amount
            expense_frequency: Frequency
            start_date: Start date
            end_date: End date (optional)
            description: Description (optional)

        Returns:
            Scenario ID
        """
        scenario_id = ScenarioStorage.create_scenario(
            scenario_name=scenario_name,
            entity=entity,
            description=description or f"Add {expense_name}: ₱{expense_amount:,.2f} ({expense_frequency})"
        )

        ScenarioStorage.add_scenario_change(
            scenario_id=scenario_id,
            change_type='expense',
            start_date=start_date,
            end_date=end_date,
            expense_name=expense_name,
            expense_amount=expense_amount,
            expense_frequency=expense_frequency
        )

        return scenario_id

    @staticmethod
    def create_revenue_scenario(
        scenario_name: str,
        entity: str,
        new_clients: int,
        revenue_per_client: Decimal,
        start_date: date,
        end_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> int:
        """
        Create a new revenue scenario.

        Args:
            scenario_name: Scenario name
            entity: Entity
            new_clients: Number of new clients
            revenue_per_client: Revenue per client
            start_date: Start date
            end_date: End date (optional)
            description: Description (optional)

        Returns:
            Scenario ID
        """
        scenario_id = ScenarioStorage.create_scenario(
            scenario_name=scenario_name,
            entity=entity,
            description=description or f"Add {new_clients} clients at ₱{revenue_per_client:,.2f}/month"
        )

        ScenarioStorage.add_scenario_change(
            scenario_id=scenario_id,
            change_type='revenue',
            start_date=start_date,
            end_date=end_date,
            new_clients=new_clients,
            revenue_per_client=revenue_per_client
        )

        return scenario_id

    @staticmethod
    def create_investment_scenario(
        scenario_name: str,
        entity: str,
        investment_amount: Decimal,
        start_date: date,
        description: Optional[str] = None
    ) -> int:
        """
        Create a one-time investment scenario.

        Args:
            scenario_name: Scenario name
            entity: Entity
            investment_amount: Investment amount
            start_date: Investment date
            description: Description (optional)

        Returns:
            Scenario ID
        """
        scenario_id = ScenarioStorage.create_scenario(
            scenario_name=scenario_name,
            entity=entity,
            description=description or f"One-time investment: ₱{investment_amount:,.2f}"
        )

        ScenarioStorage.add_scenario_change(
            scenario_id=scenario_id,
            change_type='investment',
            start_date=start_date,
            investment_amount=investment_amount
        )

        return scenario_id
