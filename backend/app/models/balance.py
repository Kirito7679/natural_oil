"""Balance account model — exactly 2 rows: cash and bank_transfer.

There is NO card balance account. Only cash and bank_transfer.
"""

from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BalanceAccount(Base):
    __tablename__ = "balance_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )  # cash | bank_transfer  — NO card
    current_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
