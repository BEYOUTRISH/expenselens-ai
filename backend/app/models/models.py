from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey,
    UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Currency(Base):
    __tablename__ = "currencies"
    currency_code = Column(String(3), primary_key=True)
    currency_name = Column(String(100), nullable=False)
    symbol = Column(String(10))


class Department(Base):
    __tablename__ = "departments"
    dept_id = Column(Integer, primary_key=True)
    dept_name = Column(String(200), nullable=False, unique=True)
    dept_code = Column(String(10), nullable=False, unique=True)
    cost_centers = relationship("CostCenter", back_populates="department")


class CostCenter(Base):
    __tablename__ = "cost_centers"
    cc_id = Column(Integer, primary_key=True)
    dept_id = Column(Integer, ForeignKey("departments.dept_id"), nullable=False)
    cc_code = Column(String(10), nullable=False, unique=True)
    cc_name = Column(String(200), nullable=False)
    annual_budget_inr = Column(Numeric(15, 2), nullable=False)
    department = relationship("Department", back_populates="cost_centers")
    ledger_entries = relationship("LedgerEntry", back_populates="cost_center")


class Employee(Base):
    __tablename__ = "employees"
    employee_id = Column(Integer, primary_key=True)
    full_name = Column(String(200), nullable=False)
    email = Column(String(300), nullable=False, unique=True)
    dept_id = Column(Integer, ForeignKey("departments.dept_id"))
    cost_center_id = Column(Integer, ForeignKey("cost_centers.cc_id"))
    role = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    department_rel = relationship("Department")
    cost_center_rel = relationship("CostCenter")
    submitted_entries = relationship(
        "LedgerEntry", back_populates="submitter",
        foreign_keys="LedgerEntry.submitted_by"
    )


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    rate_id = Column(Integer, primary_key=True)
    from_currency = Column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    to_currency = Column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    rate = Column(Numeric(12, 6), nullable=False)
    effective_date = Column(Date, nullable=False)
    source = Column(String(50), default="RBI_REFERENCE")
    __table_args__ = (
        UniqueConstraint("from_currency", "to_currency", "effective_date"),
        CheckConstraint("from_currency <> to_currency"),
        CheckConstraint("rate > 0"),
    )


class Vendor(Base):
    __tablename__ = "vendors"
    vendor_id = Column(Integer, primary_key=True)
    canonical_name = Column(String(200), nullable=False, unique=True)
    vendor_type = Column(String(50))
    country_code = Column(String(2))
    gstin = Column(String(20))
    preferred_currency = Column(String(3), ForeignKey("currencies.currency_code"))
    is_approved = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    aliases = relationship("VendorAlias", back_populates="vendor", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="vendor_rel")


class VendorAlias(Base):
    __tablename__ = "vendor_aliases"
    alias_id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False)
    alias_name = Column(String(200), nullable=False, unique=True)
    vendor = relationship("Vendor", back_populates="aliases")


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"
    category_id = Column(Integer, primary_key=True)
    category_code = Column(String(20), nullable=False, unique=True)
    category_name = Column(String(100), nullable=False)
    parent_category_id = Column(Integer, ForeignKey("expense_categories.category_id"))
    is_reimbursable = Column(Boolean, default=True)
    receipt_threshold_inr = Column(Numeric(10, 2), default=500.00)
    description = Column(Text)
    children = relationship("ExpenseCategory", backref="parent", remote_side="ExpenseCategory.category_id")
    ledger_entries = relationship("LedgerEntry", back_populates="category_rel")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    entry_id = Column(Integer, primary_key=True)
    txn_ref = Column(String(20), nullable=False, unique=True)
    entry_date = Column(Date, nullable=False)
    submission_date = Column(Date)
    amount_raw_value = Column(Numeric(18, 4), nullable=False)
    original_currency = Column(String(3), ForeignKey("currencies.currency_code"))
    exchange_rate_used = Column(Numeric(12, 6))
    amount_inr = Column(Numeric(15, 2), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"))
    category_id = Column(Integer, ForeignKey("expense_categories.category_id"))
    cost_center_id = Column(Integer, ForeignKey("cost_centers.cc_id"))
    submitted_by = Column(Integer, ForeignKey("employees.employee_id"))
    approved_by = Column(Integer, ForeignKey("employees.employee_id"))
    description = Column(Text)
    receipt_attached = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(Text)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(String(20))
    is_personal = Column(Boolean, default=False)
    approval_status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

    vendor_rel = relationship("Vendor", back_populates="ledger_entries")
    category_rel = relationship("ExpenseCategory", back_populates="ledger_entries")
    cost_center = relationship("CostCenter", back_populates="ledger_entries")
    submitter = relationship("Employee", back_populates="submitted_entries", foreign_keys=[submitted_by])

    __table_args__ = (
        CheckConstraint("amount_raw_value <> 0", name="chk_nonzero_raw"),
        Index("idx_ledger_entry_date", "entry_date"),
        Index("idx_ledger_vendor", "vendor_id"),
        Index("idx_ledger_cost_center", "cost_center_id"),
        Index("idx_ledger_submitted_by", "submitted_by"),
        Index("idx_ledger_approval", "approval_status"),
        Index("idx_ledger_flagged", "is_flagged", postgresql_where=lambda: LedgerEntry.is_flagged.is_(True)),
        Index("idx_ledger_personal", "is_personal", postgresql_where=lambda: LedgerEntry.is_personal.is_(True)),
        Index("idx_ledger_duplicate", "is_duplicate", postgresql_where=lambda: LedgerEntry.is_duplicate.is_(True)),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"
    log_id = Column(Integer, primary_key=True)
    table_name = Column(String(60), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(10), nullable=False)
    changed_by = Column(String(150))
    changed_at = Column(DateTime, server_default=func.now())
    old_values = Column("old_values", Text)
    new_values = Column("new_values", Text)
    __table_args__ = (
        CheckConstraint("action IN ('INSERT', 'UPDATE', 'DELETE')"),
        Index("idx_audit_table_record", "table_name", "record_id"),
    )
