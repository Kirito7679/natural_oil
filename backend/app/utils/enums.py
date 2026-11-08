"""Enumerations used across the application.

IMPORTANT: PaymentType has exactly 2 values — cash and bank_transfer.
There is NO card payment method anywhere in this system.
"""

import enum


class PaymentType(str, enum.Enum):
    """Only two payment methods exist: cash and bank_transfer."""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"


class PartnerType(str, enum.Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    BOTH = "both"


class MovementType(str, enum.Enum):
    INITIAL_BALANCE = "initial_balance"
    PURCHASE_PAYMENT = "purchase_payment"
    SALE_PAYMENT = "sale_payment"
    CUSTOMER_DEBT_PAYMENT = "customer_debt_payment"
    SUPPLIER_DEBT_PAYMENT = "supplier_debt_payment"
    EXPENSE = "expense"
    BALANCE_ADJUSTMENT = "balance_adjustment"
    CANCELLATION = "cancellation"


class MovementDirection(str, enum.Enum):
    INCOME = "income"
    OUTGOING = "outgoing"


class RecordStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    DELETED = "deleted"
    CLOSED = "closed"


class BatchStatus(str, enum.Enum):
    ACTIVE = "active"
    FINISHED = "finished"


class DebtType(str, enum.Enum):
    CUSTOMER_DEBT = "customer_debt"
    SUPPLIER_DEBT = "supplier_debt"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DEV = "dev"  # texnik ma'mur: direktor bilan bir xil to'liq huquq
    OPERATOR = "operator"
    INVESTOR = "investor"  # faqat ko'rish huquqi


# To'liq huquqli rollar. Direktor — biznes egasi, dev — tizimga javob beradigan
# texnik ma'mur. Huquqlari bir xil, faqat nomi boshqa.
FULL_ACCESS_ROLES = (UserRole.ADMIN.value, UserRole.DEV.value)
