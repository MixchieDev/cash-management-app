"""
Data validation module for JESUS Company Cash Management System.
Validates customer contracts, vendor contracts, and bank balances.
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from config.constants import (
    VALID_PAYMENT_PLANS,
    VALID_EXPENSE_FREQUENCIES,
    VALID_EXPENSE_CATEGORIES,
    VALID_CONTRACT_STATUSES
)
from config.entity_mapping import validate_entity


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class DataValidator:
    """Validate data before saving to database."""

    @staticmethod
    def validate_customer_contract(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate customer contract data.

        Args:
            data: Customer contract dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []

        # Required fields
        required_fields = ['company_name', 'monthly_fee', 'payment_plan', 'contract_start', 'status', 'who_acquired', 'entity']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, "; ".join(errors)

        # Validate monthly fee
        if not isinstance(data['monthly_fee'], Decimal):
            errors.append("monthly_fee must be Decimal type")
        elif data['monthly_fee'] < 0:
            errors.append("monthly_fee cannot be negative")

        # Validate payment plan
        if data['payment_plan'] not in VALID_PAYMENT_PLANS:
            errors.append(f"Invalid payment_plan: {data['payment_plan']}. Valid: {VALID_PAYMENT_PLANS}")

        # Validate status
        if data['status'] not in VALID_CONTRACT_STATUSES:
            errors.append(f"Invalid status: {data['status']}. Valid: {VALID_CONTRACT_STATUSES}")

        # Validate entity
        if not validate_entity(data['entity']):
            errors.append(f"Invalid entity: {data['entity']}")

        # Validate dates
        if not isinstance(data['contract_start'], date):
            errors.append("contract_start must be datetime.date type")

        if data.get('contract_end'):
            if not isinstance(data['contract_end'], date):
                errors.append("contract_end must be datetime.date type")
            elif data['contract_end'] < data['contract_start']:
                errors.append("contract_end cannot be before contract_start")

        # Validate invoice day
        if 'invoice_day' in data:
            if not (1 <= data['invoice_day'] <= 28):
                errors.append("invoice_day must be between 1 and 28")

        # Validate payment terms
        if 'payment_terms_days' in data:
            if data['payment_terms_days'] < 0:
                errors.append("payment_terms_days cannot be negative")

        # Validate reliability score
        if 'reliability_score' in data:
            if not (0 <= data['reliability_score'] <= 1):
                errors.append("reliability_score must be between 0 and 1")

        if errors:
            return False, "; ".join(errors)

        return True, None

    @staticmethod
    def validate_vendor_contract(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate vendor contract data.

        Args:
            data: Vendor contract dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []

        # Required fields
        required_fields = ['vendor_name', 'category', 'amount', 'frequency', 'due_date', 'entity']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, "; ".join(errors)

        # Validate amount
        if not isinstance(data['amount'], Decimal):
            errors.append("amount must be Decimal type")
        elif data['amount'] < 0:
            errors.append("amount cannot be negative")

        # Validate category
        if data['category'] not in VALID_EXPENSE_CATEGORIES:
            errors.append(f"Invalid category: {data['category']}. Valid: {VALID_EXPENSE_CATEGORIES}")

        # Validate frequency
        if data['frequency'] not in VALID_EXPENSE_FREQUENCIES:
            errors.append(f"Invalid frequency: {data['frequency']}. Valid: {VALID_EXPENSE_FREQUENCIES}")

        # Validate entity
        if data['entity'] not in ['YAHSHUA', 'ABBA', 'Both']:
            errors.append(f"Invalid entity: {data['entity']}. Valid: YAHSHUA, ABBA, Both")

        # Validate due date
        if not isinstance(data['due_date'], date):
            errors.append("due_date must be datetime.date type")

        # Validate priority
        if 'priority' in data:
            if not (1 <= data['priority'] <= 4):
                errors.append("priority must be between 1 and 4")

        # Validate flexibility days
        if 'flexibility_days' in data:
            if data['flexibility_days'] < 0:
                errors.append("flexibility_days cannot be negative")

        if errors:
            return False, "; ".join(errors)

        return True, None

    @staticmethod
    def validate_bank_balance(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate bank balance data.

        Args:
            data: Bank balance dictionary

        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []

        # Required fields
        required_fields = ['balance_date', 'entity', 'balance']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, "; ".join(errors)

        # Validate balance date
        if not isinstance(data['balance_date'], date):
            errors.append("balance_date must be datetime.date type")

        # Validate entity
        if not validate_entity(data['entity']):
            errors.append(f"Invalid entity: {data['entity']}")

        # Validate balance (can be negative)
        if not isinstance(data['balance'], Decimal):
            errors.append("balance must be Decimal type")

        if errors:
            return False, "; ".join(errors)

        return True, None

    @staticmethod
    def validate_all_customers(customers: List[Dict]) -> List[str]:
        """
        Validate multiple customer contracts.

        Args:
            customers: List of customer contract dictionaries

        Returns:
            List of error messages (empty if all valid)
        """
        all_errors = []

        for idx, customer in enumerate(customers, start=1):
            is_valid, error = DataValidator.validate_customer_contract(customer)
            if not is_valid:
                all_errors.append(f"Customer #{idx} ({customer.get('company_name', 'Unknown')}): {error}")

        return all_errors

    @staticmethod
    def validate_all_vendors(vendors: List[Dict]) -> List[str]:
        """
        Validate multiple vendor contracts.

        Args:
            vendors: List of vendor contract dictionaries

        Returns:
            List of error messages (empty if all valid)
        """
        all_errors = []

        for idx, vendor in enumerate(vendors, start=1):
            is_valid, error = DataValidator.validate_vendor_contract(vendor)
            if not is_valid:
                all_errors.append(f"Vendor #{idx} ({vendor.get('vendor_name', 'Unknown')}): {error}")

        return all_errors

    @staticmethod
    def validate_all_balances(balances: List[Dict]) -> List[str]:
        """
        Validate multiple bank balances.

        Args:
            balances: List of bank balance dictionaries

        Returns:
            List of error messages (empty if all valid)
        """
        all_errors = []

        for idx, balance in enumerate(balances, start=1):
            is_valid, error = DataValidator.validate_bank_balance(balance)
            if not is_valid:
                all_errors.append(f"Balance #{idx}: {error}")

        return all_errors
