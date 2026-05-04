"""Sale business logic."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.sale import Sale, SalePayment
from app.models.inventory import InventoryBatch
from app.models.debt import CustomerDebt
from app.models.product import Product
from app.schemas.sale import SaleCreate
from app.services.balance_service import update_balance
from app.utils.enums import PaymentType, MovementType, MovementDirection


def create_sale(
    db: Session, data: SaleCreate, user_id: int | None = None
) -> Sale:
    """Create a sale, deduct inventory, and manage balances and customer debts."""
    
    # 1. Fetch related product and inventory batch
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise ValueError("Mahsulot topilmadi")
    if not product.is_active:
        raise ValueError("Nofaol mahsulotni sotish mumkin emas")
        
    batch = db.query(InventoryBatch).filter(InventoryBatch.id == data.inventory_batch_id).first()
    if not batch:
        raise ValueError("Ombor partiyasi topilmadi")
        
    if batch.product_id != data.product_id:
        raise ValueError("Ombor partiyasi mahsulotga mos kelmaydi")
        
    if batch.status == "finished":
        raise ValueError("Ushbu partiyada mahsulot tugagan (finished)")
        
    if data.quantity_liters > batch.remaining_quantity_liters:
        raise ValueError("Tanlangan partiyada yetarli mahsulot yo'q.")
        
    # Backend recalculation
    total_sale_amount = data.quantity_liters * data.sale_price_per_liter
    total_cost = data.quantity_liters * batch.purchase_price_per_liter
    profit_per_liter = data.sale_price_per_liter - batch.purchase_price_per_liter
    total_profit = profit_per_liter * data.quantity_liters
    
    paid_amount = sum(p.amount for p in data.payments)
    if paid_amount > total_sale_amount + 0.01:
        raise ValueError("To'langan summa umumiy sotuv summasidan katta bo'lishi mumkin emas.")
        
    debt_amount = total_sale_amount - paid_amount

    # 2. Update Inventory Batch
    batch.remaining_quantity_liters -= data.quantity_liters
    if batch.remaining_quantity_liters <= 0:
        batch.remaining_quantity_liters = 0.0
        batch.status = "finished"

    # 3. Create Sale record
    sale = Sale(
        date=data.date,
        customer_id=data.customer_id,
        product_id=data.product_id,
        inventory_batch_id=data.inventory_batch_id,
        quantity_liters=data.quantity_liters,
        purchase_price_per_liter=batch.purchase_price_per_liter,
        sale_price_per_liter=data.sale_price_per_liter,
        profit_per_liter=profit_per_liter,
        total_cost=total_cost,
        total_sale_amount=total_sale_amount,
        total_profit=total_profit,
        paid_amount=paid_amount,
        debt_amount=debt_amount,
        note=data.note,
        created_by=user_id,
    )
    db.add(sale)
    db.flush()  # Get sale ID

    # 4. Process payments and add to balance
    for payment_data in data.payments:
        payment = SalePayment(
            sale_id=sale.id,
            payment_type=payment_data.payment_type.value,
            amount=payment_data.amount,
            date=data.date,
        )
        db.add(payment)
        
        # Increase balance (Income)
        update_balance(
            db=db,
            payment_type=payment_data.payment_type,
            amount=payment_data.amount,
            direction=MovementDirection.INCOME,
            movement_type=MovementType.SALE_PAYMENT,
            related_table="sales",
            related_id=sale.id,
            note=f"Sotuv tushumi. Mahsulot: {data.product_id}, Miqdor: {data.quantity_liters}L",
            user_id=user_id,
            auto_commit=False,
        )

    # 5. Create Customer Debt if there is a remaining amount
    if debt_amount > 0:
        debt = CustomerDebt(
            customer_id=sale.customer_id,
            sale_id=sale.id,
            original_amount=debt_amount,
            paid_amount=0.0,
            remaining_amount=debt_amount,
        )
        db.add(debt)

    db.commit()
    db.refresh(sale)
    return sale


def cancel_sale(
    db: Session, sale_id: int, user_id: int | None = None
) -> Sale:
    """Cancel a sale, return inventory, reverse payments/debt."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise ValueError("Sotuv topilmadi")
    if sale.status == "cancelled":
        raise ValueError("Sotuv allaqachon bekor qilingan")

    # 1. Reverse Inventory
    batch = db.query(InventoryBatch).filter(InventoryBatch.id == sale.inventory_batch_id).first()
    if not batch:
        raise ValueError("Bog'langan ombor partiyasi topilmadi")
        
    batch.remaining_quantity_liters += sale.quantity_liters
    if batch.status == "finished" and batch.remaining_quantity_liters > 0:
        batch.status = "active"

    # 2. Reverse Payments (deduct money from balance)
    for payment in sale.payments:
        if payment.status == "active":
            payment.status = "cancelled"
            try:
                update_balance(
                    db=db,
                    payment_type=PaymentType(payment.payment_type),
                    amount=payment.amount,
                    direction=MovementDirection.OUTGOING,
                    movement_type=MovementType.CANCELLATION,
                    related_table="sales",
                    related_id=sale.id,
                    note=f"Sotuv bekor qilindi. Tushum qaytarildi.",
                    user_id=user_id,
                    auto_commit=False,
                )
            except ValueError:
                # Catch insufficient funds error from update_balance
                raise ValueError("Balansda ushbu sotuvni bekor qilish uchun yetarli mablag' yo'q.")

    # 3. Reverse Customer Debt
    if sale.debt_amount > 0:
        debt = (
            db.query(CustomerDebt)
            .filter(CustomerDebt.sale_id == sale.id)
            .first()
        )
        if debt:
            if debt.paid_amount > 0:
                 raise ValueError("Bu sotuv bo'yicha mijoz qarz to'lagan. Oldin qarz to'lovini bekor qiling.")
            debt.status = "cancelled"

    # 4. Update Sale status
    sale.status = "cancelled"
    
    db.commit()
    db.refresh(sale)
    return sale
