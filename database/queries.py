"""
Database query functions for dashboard.
Provides convenient functions to fetch data for the Streamlit dashboard.
"""
from typing import List, Dict, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy import desc

from database.db_manager import db_manager
from database.models import CustomerContract, VendorContract, BankBalance, Scenario


def get_customers(entity: Optional[str] = None, status: str = 'Active') -> List[Dict]:
    """
    Get customer contracts from database.

    Args:
        entity: Filter by entity ('YAHSHUA', 'ABBA', or None for all)
        status: Filter by status (default 'Active')

    Returns:
        List of customer contract dictionaries
    """
    with db_manager.session_scope() as session:
        query = session.query(CustomerContract)

        if entity and entity != 'All' and entity != 'Consolidated':
            query = query.filter(CustomerContract.entity == entity)

        if status:
            query = query.filter(CustomerContract.status == status)

        customers = query.all()

        return [
            {
                'id': c.id,
                'company_name': c.company_name,
                'monthly_fee': Decimal(str(c.monthly_fee)),
                'payment_plan': c.payment_plan,
                'contract_start': c.contract_start,
                'contract_end': c.contract_end,
                'status': c.status,
                'who_acquired': c.who_acquired,
                'entity': c.entity,
                'invoice_day': c.invoice_day,
                'payment_terms_days': c.payment_terms_days,
                'reliability_score': float(c.reliability_score) if c.reliability_score else 0.80,
                'notes': c.notes
            }
            for c in customers
        ]


def get_vendors(entity: Optional[str] = None, status: str = 'Active') -> List[Dict]:
    """
    Get vendor contracts from database.

    Args:
        entity: Filter by entity ('YAHSHUA', 'ABBA', or None for all)
        status: Filter by status (default 'Active')

    Returns:
        List of vendor contract dictionaries
    """
    with db_manager.session_scope() as session:
        query = session.query(VendorContract)

        # Filter by entity
        if entity and entity != 'All' and entity != 'Consolidated':
            query = query.filter(VendorContract.entity == entity)

        if status:
            query = query.filter(VendorContract.status == status)

        vendors = query.all()

        return [
            {
                'id': v.id,
                'vendor_name': v.vendor_name,
                'category': v.category,
                'amount': Decimal(str(v.amount)),
                'frequency': v.frequency,
                'due_date': v.due_date,
                'entity': v.entity,
                'priority': v.priority,
                'flexibility_days': v.flexibility_days,
                'status': v.status,
                'notes': v.notes
            }
            for v in vendors
        ]


def get_latest_bank_balance(entity: str) -> Dict:
    """
    Get the most recent bank balance for an entity.

    Args:
        entity: Entity code ('YAHSHUA' or 'ABBA')

    Returns:
        Dictionary with 'date' and 'amount' keys

    Raises:
        ValueError: If no bank balance found for entity
    """
    with db_manager.session_scope() as session:
        balance = session.query(BankBalance)\
            .filter(BankBalance.entity == entity)\
            .order_by(desc(BankBalance.balance_date))\
            .first()

        if not balance:
            raise ValueError(f"No bank balance found for entity: {entity}")

        return {
            'date': balance.balance_date,
            'amount': Decimal(str(balance.balance)),
            'source': balance.source
        }


def get_consolidated_bank_balance() -> Dict:
    """
    Get consolidated bank balance (ALL active entities combined).

    Dynamically fetches balances for all active entities from the database
    and returns total with per-entity breakdown.

    Returns:
        Dictionary with:
            - 'date': Most recent balance date across all entities
            - 'amount': Total combined balance
            - 'entity_amounts': Dict mapping entity code to balance amount
            - Legacy keys for backward compatibility:
                - 'yahshua_amount': YAHSHUA balance (if exists)
                - 'abba_amount': ABBA balance (if exists)
    """
    from database.settings_manager import get_valid_entity_codes

    entity_codes = get_valid_entity_codes()

    if not entity_codes:
        raise ValueError("No active entities found in database")

    entity_balances = {}
    most_recent_date = None

    for entity_code in entity_codes:
        try:
            balance = get_latest_bank_balance(entity_code)
            entity_balances[entity_code] = balance

            # Track the most recent date across all entities
            if most_recent_date is None or balance['date'] > most_recent_date:
                most_recent_date = balance['date']

        except ValueError:
            # Entity has no bank balance yet - skip but continue
            continue

    if not entity_balances:
        raise ValueError("No bank balances found for any active entity")

    # Calculate total
    total_amount = sum(b['amount'] for b in entity_balances.values())

    # Build result with per-entity breakdown
    result = {
        'date': most_recent_date,
        'amount': total_amount,
        'entity_amounts': {
            code: balance['amount']
            for code, balance in entity_balances.items()
        }
    }

    # Add legacy keys for backward compatibility
    if 'YAHSHUA' in entity_balances:
        result['yahshua_amount'] = entity_balances['YAHSHUA']['amount']
    if 'ABBA' in entity_balances:
        result['abba_amount'] = entity_balances['ABBA']['amount']

    return result


def get_all_scenarios(entity: Optional[str] = None) -> List[Dict]:
    """
    Get all saved scenarios.

    Args:
        entity: Filter by entity (optional)

    Returns:
        List of scenario dictionaries
    """
    with db_manager.session_scope() as session:
        query = session.query(Scenario)

        if entity and entity != 'All':
            query = query.filter(Scenario.entity == entity)

        scenarios = query.order_by(desc(Scenario.created_at)).all()

        return [
            {
                'id': s.id,
                'scenario_name': s.scenario_name,
                'entity': s.entity,
                'description': s.description,
                'created_by': s.created_by,
                'created_at': s.created_at,
                'num_changes': len(s.changes)
            }
            for s in scenarios
        ]


def get_scenario_by_id(scenario_id: int) -> Optional[Dict]:
    """
    Get a specific scenario by ID.

    Args:
        scenario_id: Scenario ID

    Returns:
        Scenario dictionary or None if not found
    """
    with db_manager.session_scope() as session:
        scenario = session.query(Scenario).filter(Scenario.id == scenario_id).first()

        if not scenario:
            return None

        return {
            'id': scenario.id,
            'scenario_name': scenario.scenario_name,
            'entity': scenario.entity,
            'description': scenario.description,
            'created_by': scenario.created_by,
            'created_at': scenario.created_at,
            'changes': [
                {
                    'change_type': change.change_type,
                    'start_date': change.start_date,
                    'end_date': change.end_date,
                    'employees': change.employees,
                    'salary_per_employee': Decimal(str(change.salary_per_employee)) if change.salary_per_employee else None,
                    'expense_name': change.expense_name,
                    'expense_amount': Decimal(str(change.expense_amount)) if change.expense_amount else None,
                    'new_clients': change.new_clients,
                    'revenue_per_client': Decimal(str(change.revenue_per_client)) if change.revenue_per_client else None,
                    'lost_revenue': Decimal(str(change.lost_revenue)) if change.lost_revenue else None,
                    'investment_amount': Decimal(str(change.investment_amount)) if change.investment_amount else None,
                    'notes': change.notes,
                }
                for change in scenario.changes
            ]
        }


def get_total_mrr(entity: Optional[str] = None) -> Decimal:
    """
    Get total Monthly Recurring Revenue.

    Args:
        entity: Filter by entity (optional)

    Returns:
        Total MRR as Decimal
    """
    customers = get_customers(entity=entity, status='Active')
    return sum(c['monthly_fee'] for c in customers)


def get_total_monthly_expenses(entity: Optional[str] = None) -> Decimal:
    """
    Get total monthly expenses from vendors.

    Args:
        entity: Filter by entity (optional)

    Returns:
        Total monthly expenses as Decimal
    """
    vendors = get_vendors(entity=entity, status='Active')
    total = Decimal('0')

    for v in vendors:
        amount = v['amount']

        # Only count monthly vendors for this metric
        if v['frequency'] != 'Monthly':
            continue

        total += amount

    return total
