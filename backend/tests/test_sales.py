"""Tests for Sales API."""

from datetime import date
from app.models.inventory import InventoryBatch
from app.models.balance import BalanceAccount
from app.models.debt import CustomerDebt
from app.utils.enums import PaymentType

class TestSales:
    
    def _create_dependencies(self, client, admin_headers):
        # Create product
        p_resp = client.post("/api/products", json={"name": "Test Sale Fuel"}, headers=admin_headers)
        product_id = p_resp.json()["id"]
        
        # Create supplier & customer
        s_resp = client.post("/api/partners", json={"name": "Supplier X", "type": "supplier"}, headers=admin_headers)
        supplier_id = s_resp.json()["id"]
        
        c_resp = client.post("/api/partners", json={"name": "Customer Y", "type": "customer"}, headers=admin_headers)
        customer_id = c_resp.json()["id"]
        
        # Give some initial balance to buy inventory
        client.post("/api/balance/adjust", json={"payment_type": "cash", "amount": 10000000}, headers=admin_headers)
        
        # Create a purchase to have inventory
        pur_resp = client.post("/api/purchases", json={
            "date": str(date.today()),
            "supplier_id": supplier_id,
            "product_id": product_id,
            "quantity_liters": 1000,
            "purchase_price_per_liter": 8000,
            "payments": [{"payment_type": "cash", "amount": 8000000}]
        }, headers=admin_headers)
        
        # Get the batch ID
        inv_resp = client.get("/api/inventory/batches", headers=admin_headers)
        batch_id = [b["id"] for b in inv_resp.json()["items"] if b["product_id"] == product_id][0]
        
        return product_id, customer_id, batch_id

    def test_sale_full_payment_cash(self, client, admin_headers, db_session):
        pid, cid, bid = self._create_dependencies(client, admin_headers)
        
        # Get balance before
        b_resp_before = client.get("/api/balance", headers=admin_headers)
        cash_before = b_resp_before.json()["cash_balance"]
        
        # Make sale: 100 liters * 10,000 UZS = 1,000,000 UZS
        resp = client.post("/api/sales", json={
            "date": str(date.today()),
            "customer_id": cid,
            "product_id": pid,
            "inventory_batch_id": bid,
            "quantity_liters": 100,
            "purchase_price_per_liter": 8000,
            "sale_price_per_liter": 10000,
            "payments": [{"payment_type": "cash", "amount": 1000000}]
        }, headers=admin_headers)
        
        assert resp.status_code == 201
        data = resp.json()
        assert data["profit_per_liter"] == 2000
        assert data["total_profit"] == 200000
        assert data["total_cost"] == 800000
        assert data["total_sale_amount"] == 1000000
        assert data["debt_amount"] == 0
        
        # Check balance increased
        b_resp_after = client.get("/api/balance", headers=admin_headers)
        assert b_resp_after.json()["cash_balance"] == cash_before + 1000000
        
        # Check inventory deducted
        batch = db_session.query(InventoryBatch).filter(InventoryBatch.id == bid).first()
        assert batch.remaining_quantity_liters == 900
        assert batch.status == "active"

    def test_sale_partial_payment_creates_debt(self, client, admin_headers, db_session):
        pid, cid, bid = self._create_dependencies(client, admin_headers)
        
        resp = client.post("/api/sales", json={
            "date": str(date.today()),
            "customer_id": cid,
            "product_id": pid,
            "inventory_batch_id": bid,
            "quantity_liters": 200,
            "purchase_price_per_liter": 8000,
            "sale_price_per_liter": 10000, # total 2M
            "payments": [{"payment_type": "bank_transfer", "amount": 500000}]
        }, headers=admin_headers)
        
        assert resp.status_code == 201
        data = resp.json()
        assert data["debt_amount"] == 1500000
        
        debt = db_session.query(CustomerDebt).filter(CustomerDebt.sale_id == data["id"]).first()
        assert debt is not None
        assert debt.remaining_amount == 1500000

    def test_sale_zero_payment(self, client, admin_headers):
        pid, cid, bid = self._create_dependencies(client, admin_headers)
        
        resp = client.post("/api/sales", json={
            "date": str(date.today()),
            "customer_id": cid,
            "product_id": pid,
            "inventory_batch_id": bid,
            "quantity_liters": 100,
            "purchase_price_per_liter": 8000,
            "sale_price_per_liter": 10000, # total 1M
            "payments": []
        }, headers=admin_headers)
        
        assert resp.status_code == 201
        data = resp.json()
        assert data["paid_amount"] == 0
        assert data["debt_amount"] == 1000000

    def test_sale_quantity_exceeds_stock(self, client, admin_headers):
        pid, cid, bid = self._create_dependencies(client, admin_headers)
        
        resp = client.post("/api/sales", json={
            "date": str(date.today()),
            "customer_id": cid,
            "product_id": pid,
            "inventory_batch_id": bid,
            "quantity_liters": 2000, # Only 1000 in stock
            "purchase_price_per_liter": 8000,
            "sale_price_per_liter": 10000,
            "payments": []
        }, headers=admin_headers)
        
        assert resp.status_code == 400
        assert "yetarli mahsulot yo'q" in resp.json()["detail"]

    def test_batch_finished_status(self, client, admin_headers, db_session):
        pid, cid, bid = self._create_dependencies(client, admin_headers)
        
        # Sell all 1000 liters
        resp = client.post("/api/sales", json={
            "date": str(date.today()),
            "customer_id": cid,
            "product_id": pid,
            "inventory_batch_id": bid,
            "quantity_liters": 1000,
            "purchase_price_per_liter": 8000,
            "sale_price_per_liter": 10000,
            "payments": []
        }, headers=admin_headers)
        
        assert resp.status_code == 201
        
        batch = db_session.query(InventoryBatch).filter(InventoryBatch.id == bid).first()
        assert batch.remaining_quantity_liters == 0
        assert batch.status == "finished"
        
        # Try selling again from finished batch
        resp2 = client.post("/api/sales", json={
            "date": str(date.today()),
            "customer_id": cid,
            "product_id": pid,
            "inventory_batch_id": bid,
            "quantity_liters": 10,
            "purchase_price_per_liter": 8000,
            "sale_price_per_liter": 10000,
            "payments": []
        }, headers=admin_headers)
        assert resp2.status_code == 400
        assert "tugagan" in resp2.json()["detail"]

    def test_cancel_sale(self, client, admin_headers, db_session):
        pid, cid, bid = self._create_dependencies(client, admin_headers)
        
        # Setup: Empty the cash balance so cancellation won't fail due to initial balance,
        # but wait, cancellation removes money. If we received 1M, we can revert 1M.
        
        s_resp = client.post("/api/sales", json={
            "date": str(date.today()),
            "customer_id": cid,
            "product_id": pid,
            "inventory_batch_id": bid,
            "quantity_liters": 100,
            "purchase_price_per_liter": 8000,
            "sale_price_per_liter": 10000,
            "payments": [{"payment_type": "cash", "amount": 1000000}]
        }, headers=admin_headers)
        
        sale_id = s_resp.json()["id"]
        
        # Verify batch is at 900
        batch = db_session.query(InventoryBatch).filter(InventoryBatch.id == bid).first()
        assert batch.remaining_quantity_liters == 900
        
        # Cancel
        c_resp = client.patch(f"/api/sales/{sale_id}/cancel", headers=admin_headers)
        assert c_resp.status_code == 200
        assert c_resp.json()["status"] == "cancelled"
        
        # Batch reverted to 1000
        db_session.refresh(batch)
        assert batch.remaining_quantity_liters == 1000

    def test_cancel_sale_insufficient_balance(self, client, admin_headers, db_session):
        pid, cid, bid = self._create_dependencies(client, admin_headers)
        
        s_resp = client.post("/api/sales", json={
            "date": str(date.today()),
            "customer_id": cid,
            "product_id": pid,
            "inventory_batch_id": bid,
            "quantity_liters": 100,
            "purchase_price_per_liter": 8000,
            "sale_price_per_liter": 10000,
            "payments": [{"payment_type": "cash", "amount": 1000000}]
        }, headers=admin_headers)
        
        sale_id = s_resp.json()["id"]
        
        # Admin artificially removes ALL cash
        cash_acc = db_session.query(BalanceAccount).filter(BalanceAccount.type == PaymentType.CASH.value).first()
        cash_acc.current_balance = 0.0
        db_session.commit()
        
        # Try to cancel -> Should fail because it tries to refund 1M from 0 balance
        c_resp = client.patch(f"/api/sales/{sale_id}/cancel", headers=admin_headers)
        assert c_resp.status_code == 400
        assert "yetarli mablag' yo'q" in c_resp.json()["detail"]
