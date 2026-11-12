"""Sale business logic."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.sale import Sale, SalePayment
from app.models.inventory import InventoryBatch
from app.models.debt import CustomerDebt
from app.models.product import Product
from app.models.partner import Partner
from app.schemas.sale import SaleCreate
from app.services.balance_service import update_balance
from app.utils.enums import PaymentType, MovementType, MovementDirection


def create_sale(
    db: Session, data: SaleCreate, user_id: int | None = None,
    auto_commit: bool = True,
) -> Sale:
    """Create a sale, deduct inventory, and manage balances and customer debts."""
    
    # 1. Fetch related product and inventory batch
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise ValueError("Маҳсулот топилмади")
    if not product.is_active:
        raise ValueError("Нофаол маҳсулотни сотиш мумкин эмас")
        
    customer = db.get(Partner, data.customer_id)
    if customer is None:
        raise ValueError("Мижоз топилмади")
    if customer.type not in ("customer", "both"):
        raise ValueError("Танланган ҳамкор мижоз эмас")

    batch = db.query(InventoryBatch).filter(InventoryBatch.id == data.inventory_batch_id).first()
    if not batch:
        raise ValueError("Омбор партияси топилмади")
        
    if batch.product_id != data.product_id:
        raise ValueError("Омбор партияси маҳсулотга мос келмайди")
        
    if batch.status == "finished":
        raise ValueError("Ушбу партияда маҳсулот тугаган")
        
    if data.quantity_liters > batch.remaining_quantity_liters:
        raise ValueError("Танланган партияда етарли маҳсулот йўқ.")
        
    # Backend recalculation
    total_sale_amount = round(data.quantity_liters * data.sale_price_per_liter, 2)
    total_cost = round(data.quantity_liters * batch.purchase_price_per_liter, 2)
    profit_per_liter = round(data.sale_price_per_liter - batch.purchase_price_per_liter, 4)
    total_profit = round(total_sale_amount - total_cost, 2)

    paid_amount = round(sum(p.amount for p in data.payments), 2)
    if paid_amount > total_sale_amount + 0.01:
        raise ValueError("Тўланган сумма умумий сотув суммасидан катта бўлиши мумкин эмас.")
        
    debt_amount = round(total_sale_amount - paid_amount, 2)
    if debt_amount < 0.01:
        debt_amount = 0.0

    # 2. Update Inventory Batch
    batch.remaining_quantity_liters -= data.quantity_liters
    batch.remaining_quantity_liters = round(batch.remaining_quantity_liters, 3)
    if batch.remaining_quantity_liters <= 0.0005:
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
            note=f"Сотув тушуми. Маҳсулот: {data.product_id}, Миқдор: {data.quantity_liters}Л",
            user_id=user_id,
            auto_commit=False,
            on_date=data.date,
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

    if auto_commit:
        db.commit()
        db.refresh(sale)
    return sale


def cancel_sale(
    db: Session, sale_id: int, user_id: int | None = None,
    auto_commit: bool = True,
) -> Sale:
    """Cancel a sale, return inventory, reverse payments/debt."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise ValueError("Сотув топилмади")
    if sale.status == "cancelled":
        raise ValueError("Сотув аллақачон бекор қилинган")

    # 0. Hammasini TEKSHIRIB olamiz va faqat keyin o'zgartiramiz. Aks holda
    # omborga qaytarib bo'lgach xatolik chiqsa, yarim o'zgarish osilib qoladi.
    batch = db.query(InventoryBatch).filter(InventoryBatch.id == sale.inventory_batch_id).first()
    if not batch:
        raise ValueError("Боғланган омбор партияси топилмади")

    debt = None
    if sale.debt_amount > 0:
        debt = db.query(CustomerDebt).filter(CustomerDebt.sale_id == sale.id).first()
        if debt and debt.paid_amount > 0:
            raise ValueError("Бу сотув бўйича мижоз қарз тўлаган. Олдин қарз тўловини бекор қилинг.")

    # 1. Reverse Inventory
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
                    note=f"Сотув бекор қилинди. Тушум қайтарилди.",
                    user_id=user_id,
                    auto_commit=False,
                )
            except ValueError:
                # Catch insufficient funds error from update_balance
                raise ValueError("Балансда ушбу сотувни бекор қилиш учун етарли маблағ йўқ.")

    # 3. Reverse Customer Debt (yuqorida tekshirilgan)
    if debt:
        debt.status = "cancelled"
        debt.remaining_amount = 0.0

    # 4. Update Sale status
    sale.status = "cancelled"

    if auto_commit:
        db.commit()
        db.refresh(sale)
    return sale


def edit_sale(
    db: Session, sale_id: int, data: SaleCreate, user_id: int | None = None
) -> Sale:
    """Sotuvni to'g'rilash: eskisini bekor qilib, yangi ma'lumot bilan qayta yozadi.

    Ikkalasi bitta tranzaksiyada bajariladi — yangisi o'tmasa (masalan omborda
    yetarli yoqilg'i yo'q), eskisi ham joyida qoladi. Eski yozuv o'chmaydi,
    "bekor qilingan" bo'lib tarixda turadi.
    """
    try:
        cancel_sale(db, sale_id, user_id=user_id, auto_commit=False)
        new_sale = create_sale(db, data, user_id=user_id, auto_commit=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(new_sale)
    return new_sale
