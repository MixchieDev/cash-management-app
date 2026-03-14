"""
Database query functions for dashboard.
Provides convenient functions to fetch data for the Streamlit dashboard.
"""
from typing import List, Dict, Optional, Tuple
from datetime import date
from decimal import Decimal
from sqlalchemy import desc

from database.db_manager import db_manager
from database.models import CustomerContract, VendorContract, BankBalance, Scenario, ScenarioChange, PaymentOverride, User, UserPermission
from data_processing.data_validator import DataValidator


def invalidate_projection_cache() -> None:
    """
    Clear the projection cache in Streamlit session state.
    Called after any data modification (create/update/delete).
    """
    try:
        import streamlit as st
        if '_projection_cache' in st.session_state:
            st.session_state['_projection_cache'] = {}
    except (ImportError, RuntimeError):
        # Not running in Streamlit context
        pass


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
                'start_date': v.start_date,
                'end_date': v.end_date,
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


# ═══════════════════════════════════════════════════════════════════
# PAYMENT OVERRIDE QUERIES
# ═══════════════════════════════════════════════════════════════════

def get_payment_overrides(
    override_type: Optional[str] = None,
    entity: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict]:
    """
    Get payment overrides from database.

    Args:
        override_type: Filter by 'customer' or 'vendor'
        entity: Filter by entity
        start_date: Filter overrides affecting dates >= start_date
        end_date: Filter overrides affecting dates <= end_date

    Returns:
        List of payment override dictionaries
    """
    with db_manager.session_scope() as session:
        query = session.query(PaymentOverride)

        if override_type:
            query = query.filter(PaymentOverride.override_type == override_type)

        if entity and entity != 'All' and entity != 'Consolidated':
            query = query.filter(PaymentOverride.entity == entity)

        if start_date:
            query = query.filter(PaymentOverride.original_date >= start_date)

        if end_date:
            query = query.filter(PaymentOverride.original_date <= end_date)

        overrides = query.order_by(PaymentOverride.original_date).all()

        return [
            {
                'id': o.id,
                'override_type': o.override_type,
                'contract_id': o.contract_id,
                'original_date': o.original_date,
                'new_date': o.new_date,
                'action': o.action,
                'entity': o.entity,
                'reason': o.reason,
                'created_by': o.created_by,
                'created_at': o.created_at
            }
            for o in overrides
        ]


def create_payment_override(
    override_type: str,
    contract_id: int,
    original_date: date,
    action: str,
    entity: str,
    new_date: Optional[date] = None,
    reason: Optional[str] = None,
    created_by: Optional[str] = None
) -> Dict:
    """
    Create a new payment override.

    Args:
        override_type: 'customer' or 'vendor'
        contract_id: ID of the customer or vendor contract
        original_date: The scheduled payment date being overridden
        action: 'move' or 'skip'
        entity: 'YAHSHUA' or 'ABBA'
        new_date: New payment date (required if action='move')
        reason: Optional reason for the override
        created_by: Username who created the override

    Returns:
        Dictionary of the created override

    Raises:
        ValueError: If action is 'move' but new_date is not provided
    """
    if action == 'move' and new_date is None:
        raise ValueError("new_date is required when action is 'move'")

    with db_manager.session_scope() as session:
        override = PaymentOverride(
            override_type=override_type,
            contract_id=contract_id,
            original_date=original_date,
            new_date=new_date,
            action=action,
            entity=entity,
            reason=reason,
            created_by=created_by
        )
        session.add(override)
        session.flush()  # Get the ID

        return {
            'id': override.id,
            'override_type': override.override_type,
            'contract_id': override.contract_id,
            'original_date': override.original_date,
            'new_date': override.new_date,
            'action': override.action,
            'entity': override.entity,
            'reason': override.reason,
            'created_by': override.created_by,
            'created_at': override.created_at
        }


def delete_payment_override(override_id: int) -> bool:
    """
    Delete a payment override by ID.

    Args:
        override_id: ID of the override to delete

    Returns:
        True if deleted, False if not found
    """
    with db_manager.session_scope() as session:
        override = session.query(PaymentOverride).filter(
            PaymentOverride.id == override_id
        ).first()

        if not override:
            return False

        session.delete(override)
        return True


def get_overrides_for_contract(
    override_type: str,
    contract_id: int
) -> List[Dict]:
    """
    Get all overrides for a specific contract.

    Args:
        override_type: 'customer' or 'vendor'
        contract_id: ID of the contract

    Returns:
        List of override dictionaries
    """
    with db_manager.session_scope() as session:
        overrides = session.query(PaymentOverride).filter(
            PaymentOverride.override_type == override_type,
            PaymentOverride.contract_id == contract_id
        ).order_by(PaymentOverride.original_date).all()

        return [
            {
                'id': o.id,
                'override_type': o.override_type,
                'contract_id': o.contract_id,
                'original_date': o.original_date,
                'new_date': o.new_date,
                'action': o.action,
                'entity': o.entity,
                'reason': o.reason,
                'created_by': o.created_by,
                'created_at': o.created_at
            }
            for o in overrides
        ]


def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    """
    Get a customer contract by ID.

    Args:
        customer_id: Customer contract ID

    Returns:
        Customer dictionary or None if not found
    """
    with db_manager.session_scope() as session:
        c = session.query(CustomerContract).filter(
            CustomerContract.id == customer_id
        ).first()

        if not c:
            return None

        return {
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


def get_vendor_by_id(vendor_id: int) -> Optional[Dict]:
    """
    Get a vendor contract by ID.

    Args:
        vendor_id: Vendor contract ID

    Returns:
        Vendor dictionary or None if not found
    """
    with db_manager.session_scope() as session:
        v = session.query(VendorContract).filter(
            VendorContract.id == vendor_id
        ).first()

        if not v:
            return None

        return {
            'id': v.id,
            'vendor_name': v.vendor_name,
            'category': v.category,
            'amount': Decimal(str(v.amount)),
            'frequency': v.frequency,
            'due_date': v.due_date,
            'start_date': v.start_date,
            'end_date': v.end_date,
            'entity': v.entity,
            'priority': v.priority,
            'flexibility_days': v.flexibility_days,
            'status': v.status,
            'notes': v.notes
        }


# ═══════════════════════════════════════════════════════════════════
# CUSTOMER CONTRACT CRUD
# ═══════════════════════════════════════════════════════════════════

def create_customer_contract(data: Dict) -> Dict:
    """
    Create a new customer contract.

    Args:
        data: Customer contract data dictionary with keys:
            company_name, monthly_fee (Decimal), payment_plan, contract_start (date),
            status, who_acquired, entity, and optional: contract_end, invoice_day,
            payment_terms_days, reliability_score, notes, source, created_by

    Returns:
        Dictionary of the created customer contract

    Raises:
        ValueError: If validation fails
    """
    is_valid, error = DataValidator.validate_customer_contract(data)
    if not is_valid:
        raise ValueError(f"Validation failed: {error}")

    with db_manager.session_scope() as session:
        contract = CustomerContract(
            company_name=data['company_name'],
            monthly_fee=data['monthly_fee'],
            payment_plan=data['payment_plan'],
            contract_start=data['contract_start'],
            contract_end=data.get('contract_end'),
            status=data['status'],
            who_acquired=data['who_acquired'],
            entity=data['entity'],
            invoice_day=data.get('invoice_day'),
            payment_terms_days=data.get('payment_terms_days'),
            reliability_score=data.get('reliability_score', Decimal('0.80')),
            notes=data.get('notes'),
            source=data.get('source', 'manual'),
            created_by=data.get('created_by'),
        )
        session.add(contract)
        session.flush()

        result = {
            'id': contract.id,
            'company_name': contract.company_name,
            'monthly_fee': Decimal(str(contract.monthly_fee)),
            'payment_plan': contract.payment_plan,
            'contract_start': contract.contract_start,
            'contract_end': contract.contract_end,
            'status': contract.status,
            'who_acquired': contract.who_acquired,
            'entity': contract.entity,
            'invoice_day': contract.invoice_day,
            'payment_terms_days': contract.payment_terms_days,
            'reliability_score': float(contract.reliability_score) if contract.reliability_score else 0.80,
            'notes': contract.notes,
            'source': contract.source,
        }

    invalidate_projection_cache()
    return result


def update_customer_contract(customer_id: int, data: Dict) -> Dict:
    """
    Update an existing customer contract.

    Args:
        customer_id: ID of the customer contract to update
        data: Dictionary of fields to update

    Returns:
        Updated customer contract dictionary

    Raises:
        ValueError: If customer not found or validation fails
    """
    with db_manager.session_scope() as session:
        contract = session.query(CustomerContract).filter(
            CustomerContract.id == customer_id
        ).first()

        if not contract:
            raise ValueError(f"Customer contract not found: {customer_id}")

        # Build full data dict for validation (merge existing + updates)
        full_data = {
            'company_name': data.get('company_name', contract.company_name),
            'monthly_fee': data.get('monthly_fee', Decimal(str(contract.monthly_fee))),
            'payment_plan': data.get('payment_plan', contract.payment_plan),
            'contract_start': data.get('contract_start', contract.contract_start),
            'contract_end': data.get('contract_end', contract.contract_end),
            'status': data.get('status', contract.status),
            'who_acquired': data.get('who_acquired', contract.who_acquired),
            'entity': data.get('entity', contract.entity),
        }
        if 'invoice_day' in data:
            full_data['invoice_day'] = data['invoice_day']
        if 'payment_terms_days' in data:
            full_data['payment_terms_days'] = data['payment_terms_days']
        if 'reliability_score' in data:
            full_data['reliability_score'] = data['reliability_score']

        is_valid, error = DataValidator.validate_customer_contract(full_data)
        if not is_valid:
            raise ValueError(f"Validation failed: {error}")

        # Apply updates
        for key, value in data.items():
            if hasattr(contract, key) and key != 'id':
                setattr(contract, key, value)

        session.flush()

        result = {
            'id': contract.id,
            'company_name': contract.company_name,
            'monthly_fee': Decimal(str(contract.monthly_fee)),
            'payment_plan': contract.payment_plan,
            'contract_start': contract.contract_start,
            'contract_end': contract.contract_end,
            'status': contract.status,
            'who_acquired': contract.who_acquired,
            'entity': contract.entity,
            'invoice_day': contract.invoice_day,
            'payment_terms_days': contract.payment_terms_days,
            'reliability_score': float(contract.reliability_score) if contract.reliability_score else 0.80,
            'notes': contract.notes,
            'source': contract.source,
        }

    invalidate_projection_cache()
    return result


def delete_customer_contract(customer_id: int) -> bool:
    """
    Soft-delete a customer contract by setting status to 'Cancelled'.

    Args:
        customer_id: ID of the customer contract

    Returns:
        True if deactivated, False if not found
    """
    with db_manager.session_scope() as session:
        contract = session.query(CustomerContract).filter(
            CustomerContract.id == customer_id
        ).first()

        if not contract:
            return False

        contract.status = 'Cancelled'

    invalidate_projection_cache()
    return True


# ═══════════════════════════════════════════════════════════════════
# VENDOR CONTRACT CRUD
# ═══════════════════════════════════════════════════════════════════

def create_vendor_contract(data: Dict) -> Dict:
    """
    Create a new vendor contract.

    Args:
        data: Vendor contract data dictionary with keys:
            vendor_name, category, amount (Decimal), frequency, due_date (date),
            entity, and optional: start_date, end_date, priority, flexibility_days,
            status, notes, source, created_by

    Returns:
        Dictionary of the created vendor contract

    Raises:
        ValueError: If validation fails
    """
    is_valid, error = DataValidator.validate_vendor_contract(data)
    if not is_valid:
        raise ValueError(f"Validation failed: {error}")

    with db_manager.session_scope() as session:
        contract = VendorContract(
            vendor_name=data['vendor_name'],
            category=data['category'],
            amount=data['amount'],
            frequency=data['frequency'],
            due_date=data['due_date'],
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            entity=data['entity'],
            priority=data.get('priority', 3),
            flexibility_days=data.get('flexibility_days', 0),
            status=data.get('status', 'Active'),
            notes=data.get('notes'),
            source=data.get('source', 'manual'),
            created_by=data.get('created_by'),
        )
        session.add(contract)
        session.flush()

        result = {
            'id': contract.id,
            'vendor_name': contract.vendor_name,
            'category': contract.category,
            'amount': Decimal(str(contract.amount)),
            'frequency': contract.frequency,
            'due_date': contract.due_date,
            'start_date': contract.start_date,
            'end_date': contract.end_date,
            'entity': contract.entity,
            'priority': contract.priority,
            'flexibility_days': contract.flexibility_days,
            'status': contract.status,
            'notes': contract.notes,
            'source': contract.source,
        }

    invalidate_projection_cache()
    return result


def update_vendor_contract(vendor_id: int, data: Dict) -> Dict:
    """
    Update an existing vendor contract.

    Args:
        vendor_id: ID of the vendor contract to update
        data: Dictionary of fields to update

    Returns:
        Updated vendor contract dictionary

    Raises:
        ValueError: If vendor not found or validation fails
    """
    with db_manager.session_scope() as session:
        contract = session.query(VendorContract).filter(
            VendorContract.id == vendor_id
        ).first()

        if not contract:
            raise ValueError(f"Vendor contract not found: {vendor_id}")

        # Build full data dict for validation
        full_data = {
            'vendor_name': data.get('vendor_name', contract.vendor_name),
            'category': data.get('category', contract.category),
            'amount': data.get('amount', Decimal(str(contract.amount))),
            'frequency': data.get('frequency', contract.frequency),
            'due_date': data.get('due_date', contract.due_date),
            'entity': data.get('entity', contract.entity),
        }
        if 'priority' in data:
            full_data['priority'] = data['priority']
        if 'flexibility_days' in data:
            full_data['flexibility_days'] = data['flexibility_days']

        is_valid, error = DataValidator.validate_vendor_contract(full_data)
        if not is_valid:
            raise ValueError(f"Validation failed: {error}")

        # Apply updates
        for key, value in data.items():
            if hasattr(contract, key) and key != 'id':
                setattr(contract, key, value)

        session.flush()

        result = {
            'id': contract.id,
            'vendor_name': contract.vendor_name,
            'category': contract.category,
            'amount': Decimal(str(contract.amount)),
            'frequency': contract.frequency,
            'due_date': contract.due_date,
            'start_date': contract.start_date,
            'end_date': contract.end_date,
            'entity': contract.entity,
            'priority': contract.priority,
            'flexibility_days': contract.flexibility_days,
            'status': contract.status,
            'notes': contract.notes,
            'source': contract.source,
        }

    invalidate_projection_cache()
    return result


def delete_vendor_contract(vendor_id: int) -> bool:
    """
    Soft-delete a vendor contract by setting status to 'Inactive'.

    Args:
        vendor_id: ID of the vendor contract

    Returns:
        True if deactivated, False if not found
    """
    with db_manager.session_scope() as session:
        contract = session.query(VendorContract).filter(
            VendorContract.id == vendor_id
        ).first()

        if not contract:
            return False

        contract.status = 'Inactive'

    invalidate_projection_cache()
    return True


# ═══════════════════════════════════════════════════════════════════
# BANK BALANCE CRUD
# ═══════════════════════════════════════════════════════════════════

def get_all_bank_balances(entity: Optional[str] = None) -> List[Dict]:
    """
    Get all bank balance entries, ordered by date descending.

    Args:
        entity: Filter by entity (optional)

    Returns:
        List of bank balance dictionaries
    """
    with db_manager.session_scope() as session:
        query = session.query(BankBalance)

        if entity and entity != 'All' and entity != 'Consolidated':
            query = query.filter(BankBalance.entity == entity)

        balances = query.order_by(desc(BankBalance.balance_date)).all()

        return [
            {
                'id': b.id,
                'balance_date': b.balance_date,
                'entity': b.entity,
                'balance': Decimal(str(b.balance)),
                'source': b.source,
                'notes': b.notes,
                'created_at': b.created_at,
            }
            for b in balances
        ]


def create_bank_balance(data: Dict) -> Dict:
    """
    Create a new bank balance entry.

    Args:
        data: Bank balance data with keys:
            balance_date (date), entity, balance (Decimal),
            and optional: source, notes

    Returns:
        Dictionary of the created bank balance

    Raises:
        ValueError: If validation fails
    """
    is_valid, error = DataValidator.validate_bank_balance(data)
    if not is_valid:
        raise ValueError(f"Validation failed: {error}")

    with db_manager.session_scope() as session:
        balance = BankBalance(
            balance_date=data['balance_date'],
            entity=data['entity'],
            balance=data['balance'],
            source=data.get('source', 'Manual Entry'),
            notes=data.get('notes'),
        )
        session.add(balance)
        session.flush()

        result = {
            'id': balance.id,
            'balance_date': balance.balance_date,
            'entity': balance.entity,
            'balance': Decimal(str(balance.balance)),
            'source': balance.source,
            'notes': balance.notes,
        }

    invalidate_projection_cache()
    return result


def update_bank_balance(balance_id: int, data: Dict) -> Dict:
    """
    Update an existing bank balance.

    Args:
        balance_id: ID of the bank balance to update
        data: Dictionary of fields to update

    Returns:
        Updated bank balance dictionary

    Raises:
        ValueError: If balance not found or validation fails
    """
    with db_manager.session_scope() as session:
        balance = session.query(BankBalance).filter(
            BankBalance.id == balance_id
        ).first()

        if not balance:
            raise ValueError(f"Bank balance not found: {balance_id}")

        # Build full data for validation
        full_data = {
            'balance_date': data.get('balance_date', balance.balance_date),
            'entity': data.get('entity', balance.entity),
            'balance': data.get('balance', Decimal(str(balance.balance))),
        }

        is_valid, error = DataValidator.validate_bank_balance(full_data)
        if not is_valid:
            raise ValueError(f"Validation failed: {error}")

        for key, value in data.items():
            if hasattr(balance, key) and key != 'id':
                setattr(balance, key, value)

        session.flush()

        result = {
            'id': balance.id,
            'balance_date': balance.balance_date,
            'entity': balance.entity,
            'balance': Decimal(str(balance.balance)),
            'source': balance.source,
            'notes': balance.notes,
        }

    invalidate_projection_cache()
    return result


def delete_bank_balance(balance_id: int) -> bool:
    """
    Delete a bank balance entry.

    Args:
        balance_id: ID of the bank balance to delete

    Returns:
        True if deleted, False if not found
    """
    with db_manager.session_scope() as session:
        balance = session.query(BankBalance).filter(
            BankBalance.id == balance_id
        ).first()

        if not balance:
            return False

        session.delete(balance)

    invalidate_projection_cache()
    return True


def delete_all_customer_contracts() -> int:
    """
    Permanently delete ALL customer contracts.

    Returns:
        Number of records deleted
    """
    with db_manager.session_scope() as session:
        count = session.query(CustomerContract).delete()
    invalidate_projection_cache()
    return count


def delete_all_vendor_contracts() -> int:
    """
    Permanently delete ALL vendor contracts.

    Returns:
        Number of records deleted
    """
    with db_manager.session_scope() as session:
        count = session.query(VendorContract).delete()
    invalidate_projection_cache()
    return count


def delete_all_bank_balances() -> int:
    """
    Permanently delete ALL bank balance entries.

    Returns:
        Number of records deleted
    """
    with db_manager.session_scope() as session:
        count = session.query(BankBalance).delete()
    invalidate_projection_cache()
    return count


def delete_all_payment_overrides() -> int:
    """
    Permanently delete ALL payment overrides.

    Returns:
        Number of records deleted
    """
    with db_manager.session_scope() as session:
        count = session.query(PaymentOverride).delete()
    invalidate_projection_cache()
    return count


def delete_all_scenarios() -> int:
    """
    Permanently delete ALL scenarios and their changes.

    Returns:
        Number of scenario records deleted
    """
    with db_manager.session_scope() as session:
        session.query(ScenarioChange).delete()
        count = session.query(Scenario).delete()
    return count


def delete_all_data() -> Dict[str, int]:
    """
    Permanently delete ALL application data (contracts, balances, overrides, scenarios).

    Returns:
        Dictionary with counts per table
    """
    results = {
        'customers': delete_all_customer_contracts(),
        'vendors': delete_all_vendor_contracts(),
        'bank_balances': delete_all_bank_balances(),
        'payment_overrides': delete_all_payment_overrides(),
        'scenarios': delete_all_scenarios(),
    }
    return results


# ═══════════════════════════════════════════════════════════════════
# USER MANAGEMENT QUERIES
# ═══════════════════════════════════════════════════════════════════

def get_user_by_username(username: str) -> Optional[Dict]:
    """
    Get a user by username, including their permissions.

    Args:
        username: Username to look up

    Returns:
        User dictionary with permissions, or None if not found
    """
    with db_manager.session_scope() as session:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return None

        granted_permissions = [
            p.permission for p in user.permissions if p.granted
        ]

        return {
            'id': user.id,
            'username': user.username,
            'password_hash': user.password_hash,
            'name': user.name,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at,
            'permissions': granted_permissions,
        }


def get_all_users() -> List[Dict]:
    """
    Get all users with their permissions.

    Returns:
        List of user dictionaries
    """
    with db_manager.session_scope() as session:
        users = session.query(User).order_by(User.created_at).all()

        return [
            {
                'id': u.id,
                'username': u.username,
                'name': u.name,
                'role': u.role,
                'is_active': u.is_active,
                'created_at': u.created_at,
                'permissions': [p.permission for p in u.permissions if p.granted],
            }
            for u in users
        ]


def create_user(username: str, password: str, name: str, role: str = 'viewer') -> Dict:
    """
    Create a new user with default permissions based on role.

    Args:
        username: Unique username
        password: Plain text password (will be hashed)
        name: Display name
        role: Role template ('admin', 'editor', 'viewer')

    Returns:
        Created user dictionary

    Raises:
        ValueError: If username already exists
    """
    import bcrypt
    from auth.permissions import get_default_permissions, PERMISSION_KEYS

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    default_perms = get_default_permissions(role)

    with db_manager.session_scope() as session:
        existing = session.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError(f"Username already exists: {username}")

        user = User(
            username=username,
            password_hash=password_hash,
            name=name,
            role=role,
            is_active=True,
        )
        session.add(user)
        session.flush()

        # Create permission entries for ALL permissions
        for perm_key in PERMISSION_KEYS:
            perm = UserPermission(
                user_id=user.id,
                permission=perm_key,
                granted=(perm_key in default_perms),
            )
            session.add(perm)

        return {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'role': user.role,
            'is_active': user.is_active,
            'permissions': default_perms,
        }


def update_user(user_id: int, **kwargs) -> Dict:
    """
    Update user fields (name, role, is_active).

    Args:
        user_id: User ID
        **kwargs: Fields to update (name, role, is_active)

    Returns:
        Updated user dictionary

    Raises:
        ValueError: If user not found
    """
    with db_manager.session_scope() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        for key, value in kwargs.items():
            if hasattr(user, key) and key not in ('id', 'username', 'password_hash', 'created_at'):
                setattr(user, key, value)

        session.flush()

        return {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'role': user.role,
            'is_active': user.is_active,
            'permissions': [p.permission for p in user.permissions if p.granted],
        }


def update_user_permissions(user_id: int, permissions_dict: Dict[str, bool]) -> None:
    """
    Bulk update permissions for a user.

    Args:
        user_id: User ID
        permissions_dict: Dict mapping permission key to granted (True/False)
    """
    with db_manager.session_scope() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        for perm in user.permissions:
            if perm.permission in permissions_dict:
                perm.granted = permissions_dict[perm.permission]


def reset_user_password(user_id: int, new_password: str) -> None:
    """
    Reset a user's password.

    Args:
        user_id: User ID
        new_password: New plain text password
    """
    import bcrypt

    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    with db_manager.session_scope() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        user.password_hash = password_hash


def deactivate_user(user_id: int) -> None:
    """Soft-delete a user by setting is_active=False."""
    update_user(user_id, is_active=False)


def reactivate_user(user_id: int) -> None:
    """Reactivate a deactivated user."""
    update_user(user_id, is_active=True)


def has_permission(username: str, permission: str) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        username: Username
        permission: Permission key

    Returns:
        True if user has the permission granted
    """
    user = get_user_by_username(username)
    if not user:
        return False
    return permission in user.get('permissions', [])


def auto_seed_admin() -> None:
    """
    Create default admin user if no users exist in the database.
    Called during app initialization.
    """
    with db_manager.session_scope() as session:
        user_count = session.query(User).count()
        if user_count > 0:
            return

    # No users exist — create default admin
    try:
        create_user(
            username='admin',
            password='admin123',
            name='CFO Mich',
            role='admin',
        )
        # Also create default viewer
        create_user(
            username='viewer',
            password='viewer123',
            name='Team Viewer',
            role='viewer',
        )
        print("[DB] Default users created (admin/admin123, viewer/viewer123)")
    except ValueError:
        pass  # Users already exist
