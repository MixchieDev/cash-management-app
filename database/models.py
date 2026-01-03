"""
SQLAlchemy ORM models for JESUS Company Cash Management System.
Defines database schema as Python classes.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Numeric,
    Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class CustomerContract(Base):
    """Customer contract with recurring revenue."""
    __tablename__ = 'customer_contracts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String, nullable=False)
    monthly_fee = Column(Numeric(15, 2), nullable=False)
    payment_plan = Column(String, nullable=False)
    contract_start = Column(Date, nullable=False)
    contract_end = Column(Date, nullable=True)
    status = Column(String, nullable=False)
    who_acquired = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    invoice_day = Column(Integer, default=15)
    payment_terms_days = Column(Integer, default=30)
    reliability_score = Column(Numeric(3, 2), default=0.80)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("payment_plan IN ('Monthly', 'Quarterly', 'Annual', 'Bi-annually', 'More than 1 year')",
                       name='ck_payment_plan'),
        CheckConstraint("status IN ('Active', 'Inactive', 'Pending', 'Cancelled')",
                       name='ck_customer_status'),
        CheckConstraint("entity IN ('YAHSHUA', 'ABBA')",
                       name='ck_customer_entity'),
        CheckConstraint("invoice_day BETWEEN 1 AND 28",
                       name='ck_invoice_day'),
        CheckConstraint("reliability_score BETWEEN 0 AND 1",
                       name='ck_reliability_score'),
    )

    def __repr__(self):
        return f"<CustomerContract(id={self.id}, company={self.company_name}, entity={self.entity})>"


class VendorContract(Base):
    """Vendor contract with recurring expenses."""
    __tablename__ = 'vendor_contracts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    frequency = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    start_date = Column(Date, nullable=True)  # Date when vendor expense becomes active
    end_date = Column(Date, nullable=True)  # Date when vendor expense ends (null = continues indefinitely)
    entity = Column(String, nullable=False)
    priority = Column(Integer, default=3)
    flexibility_days = Column(Integer, default=0)
    status = Column(String, nullable=False, default='Active')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("category IN ('Payroll', 'Loans', 'Software/Tech', 'Operations', 'Rent', 'Utilities')",
                       name='ck_vendor_category'),
        CheckConstraint("frequency IN ('One-time', 'Daily', 'Weekly', 'Bi-weekly', 'Monthly', 'Quarterly', 'Annual')",
                       name='ck_vendor_frequency'),
        CheckConstraint("entity IN ('YAHSHUA', 'ABBA')",
                       name='ck_vendor_entity'),
        CheckConstraint("priority BETWEEN 1 AND 4",
                       name='ck_vendor_priority'),
        CheckConstraint("status IN ('Active', 'Inactive', 'Paid', 'Pending')",
                       name='ck_vendor_status'),
    )

    def __repr__(self):
        return f"<VendorContract(id={self.id}, vendor={self.vendor_name}, category={self.category})>"


class BankBalance(Base):
    """Bank balance snapshot (source of truth for starting cash)."""
    __tablename__ = 'bank_balances'

    id = Column(Integer, primary_key=True, autoincrement=True)
    balance_date = Column(Date, nullable=False)
    entity = Column(String, nullable=False)
    balance = Column(Numeric(15, 2), nullable=False)
    source = Column(String, default='Manual Entry')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('balance_date', 'entity', name='uq_balance_date_entity'),
        CheckConstraint("entity IN ('YAHSHUA', 'ABBA')",
                       name='ck_bank_entity'),
    )

    def __repr__(self):
        return f"<BankBalance(date={self.balance_date}, entity={self.entity}, balance={self.balance})>"


class Scenario(Base):
    """Scenario for what-if analysis."""
    __tablename__ = 'scenarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_name = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    changes = relationship("ScenarioChange", back_populates="scenario", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("entity IN ('YAHSHUA', 'ABBA', 'Consolidated')",
                       name='ck_scenario_entity'),
    )

    def __repr__(self):
        return f"<Scenario(id={self.id}, name={self.scenario_name}, entity={self.entity})>"


class ScenarioChange(Base):
    """Changes to apply in a scenario."""
    __tablename__ = 'scenario_changes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id', ondelete='CASCADE'), nullable=False)
    change_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Hiring fields
    employees = Column(Integer, nullable=True)
    salary_per_employee = Column(Numeric(15, 2), nullable=True)

    # Expense fields
    expense_name = Column(String, nullable=True)
    expense_amount = Column(Numeric(15, 2), nullable=True)
    expense_frequency = Column(String, nullable=True)

    # Revenue fields
    new_clients = Column(Integer, nullable=True)
    revenue_per_client = Column(Numeric(15, 2), nullable=True)

    # Investment fields
    investment_amount = Column(Numeric(15, 2), nullable=True)

    # Customer loss fields
    lost_revenue = Column(Numeric(15, 2), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    scenario = relationship("Scenario", back_populates="changes")

    __table_args__ = (
        CheckConstraint("change_type IN ('hiring', 'expense', 'revenue', 'customer_loss', 'investment')",
                       name='ck_change_type'),
    )

    def __repr__(self):
        return f"<ScenarioChange(id={self.id}, type={self.change_type}, scenario_id={self.scenario_id})>"


class Projection(Base):
    """Cached projection result."""
    __tablename__ = 'projections'

    id = Column(Integer, primary_key=True, autoincrement=True)
    projection_date = Column(Date, nullable=False)
    entity = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    scenario_type = Column(String, nullable=False)
    scenario_id = Column(Integer, ForeignKey('scenarios.id', ondelete='SET NULL'), nullable=True)
    starting_cash = Column(Numeric(15, 2), nullable=False)
    inflows = Column(Numeric(15, 2), nullable=False, default=0)
    outflows = Column(Numeric(15, 2), nullable=False, default=0)
    ending_cash = Column(Numeric(15, 2), nullable=False)
    is_negative = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("entity IN ('YAHSHUA', 'ABBA', 'Consolidated')",
                       name='ck_projection_entity'),
        CheckConstraint("timeframe IN ('daily', 'weekly', 'monthly', 'quarterly')",
                       name='ck_projection_timeframe'),
        CheckConstraint("scenario_type IN ('optimistic', 'realistic')",
                       name='ck_projection_scenario_type'),
    )

    def __repr__(self):
        return f"<Projection(date={self.projection_date}, entity={self.entity}, ending_cash={self.ending_cash})>"


class SystemMetadata(Base):
    """System metadata and configuration."""
    __tablename__ = 'system_metadata'

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SystemMetadata(key={self.key}, value={self.value})>"


class PaymentOverride(Base):
    """One-off payment date override for customer or vendor payment."""
    __tablename__ = 'payment_overrides'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Type: 'customer' or 'vendor'
    override_type = Column(String, nullable=False)

    # Reference to the contract (can be customer_contract_id or vendor_contract_id)
    contract_id = Column(Integer, nullable=False)

    # The original scheduled date being overridden
    original_date = Column(Date, nullable=False)

    # The new payment date (null = skip payment entirely)
    new_date = Column(Date, nullable=True)

    # Action: 'move' or 'skip'
    action = Column(String, nullable=False, default='move')

    # Entity for filtering
    entity = Column(String, nullable=False)

    # Optional reason/notes
    reason = Column(Text, nullable=True)

    # Audit fields
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("override_type IN ('customer', 'vendor')",
                       name='ck_override_type'),
        CheckConstraint("action IN ('move', 'skip')",
                       name='ck_override_action'),
        CheckConstraint("entity IN ('YAHSHUA', 'ABBA')",
                       name='ck_override_entity'),
        # Unique constraint: only one override per contract + original date + type
        UniqueConstraint('override_type', 'contract_id', 'original_date',
                        name='uq_override_contract_date'),
    )

    def __repr__(self):
        return f"<PaymentOverride(id={self.id}, type={self.override_type}, action={self.action}, original={self.original_date})>"
