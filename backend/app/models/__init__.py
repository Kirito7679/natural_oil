"""Import all models so SQLAlchemy registers them with Base.metadata."""

from app.models.user import User  # noqa: F401
from app.models.partner import Partner  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.balance import BalanceAccount  # noqa: F401
from app.models.inventory import InventoryBatch  # noqa: F401
from app.models.purchase import Purchase, PurchasePayment  # noqa: F401
from app.models.sale import Sale, SalePayment  # noqa: F401
from app.models.debt import CustomerDebt, SupplierDebt, DebtPayment  # noqa: F401
from app.models.expense import ExpenseCategory, Expense  # noqa: F401
from app.models.money_movement import MoneyMovement  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
