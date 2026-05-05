"""Purchase and inventory business logic."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.purchase import Purchase, PurchasePayment
from app.models.inventory import InventoryBatch
from app.models.debt import SupplierDebt
from app.models.partner import Partner
from app.schemas.purchase import PurchaseCreate, InitialFuelStockRequest
from app.services.balance_service import update_balance
from app.utils.enums import PaymentType, MovementType, MovementDirection


def create_purchase(
    db: Session, data: PurchaseCreate, user_id: int | None = None
) -> Purchase:
    """Create purchase, manage inventory batch, payments, and supplier debt."""
    # 1. Create Purchase record
    purchase = Purchase(
        date=data.date,
        supplier_id=data.supplier_id,
        product_id=data.product_id,
        quantity_liters=data.quantity_liters,
        purchase_price_per_liter=data.purchase_price_per_liter,
        total_amount=data.total_amount,
        paid_amount=sum(p.amount for p in data.payments),
        debt_amount=data.total_amount - sum(p.amount for p in data.payments),
        note=data.note,
        created_by=user_id,
    )
    db.add(purchase)
    db.flush()  # Get purchase ID

    # 2. Process payments and deduct from balance
    for payment_data in data.payments:
        payment = PurchasePayment(
            purchase_id=purchase.id,
            payment_type=payment_data.payment_type.value,
            amount=payment_data.amount,
            date=data.date,
        )
        db.add(payment)
        
        # Deduct balance
        update_balance(
            db=db,
            payment_type=payment_data.payment_type,
            amount=payment_data.amount,
            direction=MovementDirection.OUTGOING,
            movement_type=MovementType.PURCHASE_PAYMENT,
            related_table="purchases",
            related_id=purchase.id,
            note=f"Prixod to'lovi. Mahsulot: {data.product_id}, Miqdor: {data.quantity_liters}L",
            user_id=user_id,
            auto_commit=False,
        )

    # 3. Create Supplier Debt if there is a remaining amount
    if purchase.debt_amount > 0:
        debt = SupplierDebt(
            supplier_id=purchase.supplier_id,
            purchase_id=purchase.id,
            original_amount=purchase.debt_amount,
            paid_amount=0.0,
            remaining_amount=purchase.debt_amount,
        )
        db.add(debt)

    # 4. Inventory Logic: Batching
    # Check if active batch exists with exactly same product + supplier + price
    existing_batch = (
        db.query(InventoryBatch)
        .filter(
            InventoryBatch.product_id == data.product_id,
            InventoryBatch.supplier_id == data.supplier_id,
            InventoryBatch.purchase_price_per_liter == data.purchase_price_per_liter,
            InventoryBatch.status == "active",
        )
        .first()
    )

    if existing_batch:
        # Merge by adding to existing batch
        existing_batch.initial_quantity_liters += data.quantity_liters
        existing_batch.remaining_quantity_liters += data.quantity_liters
    else:
        # Create new batch
        new_batch = InventoryBatch(
            product_id=data.product_id,
            supplier_id=data.supplier_id,
            purchase_id=purchase.id,
            purchase_price_per_liter=data.purchase_price_per_liter,
            initial_quantity_liters=data.quantity_liters,
            remaining_quantity_liters=data.quantity_liters,
        )
        db.add(new_batch)

    db.commit()
    db.refresh(purchase)
    return purchase


def create_initial_fuel_stock(
    db: Session, data: InitialFuelStockRequest, user_id: int | None = None
) -> Purchase:
    """Creates initial fuel stock.
    Bypasses balance deduction, supplier debt creation, and payments.
    Uses a dummy system supplier to ensure DB integrity without skewing reports.
    """
    # 1. Find or create dummy supplier
    dummy_name = "O'zimiz (Boshlang'ich qoldiq)"
    supplier = db.query(Partner).filter(Partner.name == dummy_name).first()
    if not supplier:
        supplier = Partner(
            name=dummy_name,
            phone="+998000000000",
            type="supplier",
            is_active=True
        )
        db.add(supplier)
        db.flush()

    total_amount = data.quantity_liters * data.purchase_price_per_liter

    # 2. Create dummy Purchase
    # paid_amount=total_amount but 0 payments, debt=0.
    # We add a clear note so it's distinguishable in reports.
    purchase = Purchase(
        date=data.date,
        supplier_id=supplier.id,
        product_id=data.product_id,
        quantity_liters=data.quantity_liters,
        purchase_price_per_liter=data.purchase_price_per_liter,
        total_amount=total_amount,
        paid_amount=total_amount,
        debt_amount=0.0,
        note=data.note or "Boshlang'ich qoldiq",
        created_by=user_id,
    )
    db.add(purchase)
    db.flush()

    # 3. Create Inventory Batch (no merge for initial stock usually, or merge if exact match)
    existing_batch = (
        db.query(InventoryBatch)
        .filter(
            InventoryBatch.product_id == data.product_id,
            InventoryBatch.supplier_id == supplier.id,
            InventoryBatch.purchase_price_per_liter == data.purchase_price_per_liter,
            InventoryBatch.status == "active",
        )
        .first()
    )

    if existing_batch:
        existing_batch.initial_quantity_liters += data.quantity_liters
        existing_batch.remaining_quantity_liters += data.quantity_liters
    else:
        new_batch = InventoryBatch(
            product_id=data.product_id,
            supplier_id=supplier.id,
            purchase_id=purchase.id,
            purchase_price_per_liter=data.purchase_price_per_liter,
            initial_quantity_liters=data.quantity_liters,
            remaining_quantity_liters=data.quantity_liters,
        )
        db.add(new_batch)

    db.commit()
    db.refresh(purchase)
    return purchase


def cancel_purchase(
    db: Session, purchase_id: int, user_id: int | None = None
) -> Purchase:
    """Cancel a purchase, reverse payments/debt, and remove from inventory.
    
    Validates that the batch has not been sold.
    """
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise ValueError("Prixod topilmadi")
    if purchase.status == "cancelled":
        raise ValueError("Prixod allaqachon bekor qilingan")

    # Check Inventory: Find batches created by this purchase
    # Warning: If merged, checking by purchase_id might not cover everything,
    # but initially the batch stores purchase_id of creator.
    # A safer way to check usage: initial_qty != remaining_qty means it was sold.
    # We find any active batch with exactly this product/supplier/price.
    # To precisely reverse: we subtract the purchase quantity from the matching batch.
    
    batch = (
        db.query(InventoryBatch)
        .filter(
            InventoryBatch.product_id == purchase.product_id,
            InventoryBatch.supplier_id == purchase.supplier_id,
            InventoryBatch.purchase_price_per_liter == purchase.purchase_price_per_liter,
            InventoryBatch.status == "active"
        )
        .first()
    )

    if not batch:
        raise ValueError("Omborda tegishli partiya topilmadi")
        
    # Check if ANY of this purchase has been sold
    # If the batch's remaining quantity has decreased by more than what others might have added,
    # it's complex. Simplified check: if remaining < initial, something was sold.
    # Since batches can merge, we specifically check if batch.remaining < purchase.quantity.
    # If remaining is less than what we bought, it means we definitely sold some of THIS purchase.
    if batch.remaining_quantity_liters < purchase.quantity_liters:
        raise ValueError("Bu partiyadan sotuv qilingan. Prixodni o'chirish mumkin emas.")

    # 1. Reverse Inventory
    batch.initial_quantity_liters -= purchase.quantity_liters
    batch.remaining_quantity_liters -= purchase.quantity_liters
    
    if batch.remaining_quantity_liters <= 0 and batch.initial_quantity_liters <= 0:
        batch.status = "finished"

    # 2. Reverse Payments (return money to balance)
    for payment in purchase.payments:
        if payment.status == "active":
            payment.status = "cancelled"
            update_balance(
                db=db,
                payment_type=PaymentType(payment.payment_type),
                amount=payment.amount,
                direction=MovementDirection.INCOME,
                movement_type=MovementType.CANCELLATION,
                related_table="purchases",
                related_id=purchase.id,
                note=f"Prixod bekor qilindi. Qaytarilgan to'lov.",
                user_id=user_id,
                auto_commit=False,
            )

    # 3. Reverse Supplier Debt
    if purchase.debt_amount > 0:
        debt = (
            db.query(SupplierDebt)
            .filter(SupplierDebt.purchase_id == purchase.id)
            .first()
        )
        if debt:
            # If we paid some of this debt later, cancelling is even more complex,
            # but for now we just cancel the debt record.
            if debt.paid_amount > 0:
                 raise ValueError("Bu prixod bo'yicha qarz to'lovi qilingan. Oldin qarz to'lovini bekor qiling.")
            debt.status = "cancelled"

    # 4. Update Purchase status
    purchase.status = "cancelled"
    
    db.commit()
    db.refresh(purchase)
    return purchase
