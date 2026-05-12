"""Tests for Purchases and Inventory API."""

from datetime import date

class TestPurchasesAndInventory:
    
    def _create_dependencies(self, client, admin_headers):
        # Create a product
        p_resp = client.post("/api/products", json={"name": "Test Fuel"}, headers=admin_headers)
        product_id = p_resp.json()["id"]
        
        # Create a supplier
        s_resp = client.post("/api/partners", json={"name": "Test Supplier", "type": "supplier"}, headers=admin_headers)
        supplier_id = s_resp.json()["id"]
        
        # Give ourselves some balance
        client.post("/api/balance/adjust", json={"payment_type": "cash", "amount": 100000000}, headers=admin_headers)
        client.post("/api/balance/adjust", json={"payment_type": "bank_transfer", "amount": 100000000}, headers=admin_headers)
        
        return product_id, supplier_id

    def test_purchase_with_full_payment(self, client, admin_headers, db_session):
        pid, sid = self._create_dependencies(client, admin_headers)
        
        resp = client.post("/api/purchases", json={
            "date": str(date.today()),
            "supplier_id": sid,
            "product_id": pid,
            "quantity_liters": 1000,
            "purchase_price_per_liter": 8000,
            # No total_amount provided, system should calculate: 1000 * 8000 = 8,000,000
            "payments": [
                {"payment_type": "cash", "amount": 8000000}
            ]
        }, headers=admin_headers)
        
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_amount"] == 8000000
        assert data["paid_amount"] == 8000000
        assert data["debt_amount"] == 0
        
        # Check balance deduction
        b_resp = client.get("/api/balance", headers=admin_headers)
        # Assumes start was 100M
        assert b_resp.json()["cash_balance"] == 92000000
        
        # Check inventory batch creation
        inv_resp = client.get("/api/inventory/batches", headers=admin_headers)
        assert inv_resp.status_code == 200
        assert len(inv_resp.json()["items"]) >= 1
        batch = [b for b in inv_resp.json()["items"] if b["product_id"] == pid and b["supplier_id"] == sid][0]
        assert batch["initial_quantity_liters"] == 1000
        assert batch["remaining_quantity_liters"] == 1000
        assert batch["purchase_price_per_liter"] == 8000

    def test_purchase_with_zero_payment(self, client, admin_headers):
        pid, sid = self._create_dependencies(client, admin_headers)
        
        resp = client.post("/api/purchases", json={
            "date": str(date.today()),
            "supplier_id": sid,
            "product_id": pid,
            "quantity_liters": 500,
            "total_amount": 4000000,
            # No price_per_liter, system calculates: 4000000 / 500 = 8000
            "payments": []
        }, headers=admin_headers)
        
        assert resp.status_code == 201
        data = resp.json()
        assert data["purchase_price_per_liter"] == 8000
        assert data["paid_amount"] == 0
        assert data["debt_amount"] == 4000000
        
        # This exact product + supplier + price matches previous test if run sequentially?
        # No, because this is a new product/supplier created in _create_dependencies per test.
        # Check inventory to see it created a batch of 500
        inv_resp = client.get("/api/inventory/batches", headers=admin_headers)
        batches = [b for b in inv_resp.json()["items"] if b["product_id"] == pid]
        assert sum(b["remaining_quantity_liters"] for b in batches) == 500

    def test_purchase_negative_balance_allowed(self, client, admin_headers):
        pid, sid = self._create_dependencies(client, admin_headers)
        
        # We gave 100M in setup. Try to buy 200M worth
        resp = client.post("/api/purchases", json={
            "date": str(date.today()),
            "supplier_id": sid,
            "product_id": pid,
            "quantity_liters": 10000,
            "purchase_price_per_liter": 20000, # 200M total
            "payments": [
                {"payment_type": "cash", "amount": 200000000}
            ]
        }, headers=admin_headers)
        
        assert resp.status_code == 201
        data = resp.json()
        assert data["paid_amount"] == 200000000

    def test_inventory_batch_merging(self, client, admin_headers):
        pid, sid = self._create_dependencies(client, admin_headers)
        
        # Buy 100 liters
        client.post("/api/purchases", json={
            "date": str(date.today()),
            "supplier_id": sid,
            "product_id": pid,
            "quantity_liters": 100,
            "purchase_price_per_liter": 5000,
        }, headers=admin_headers)
        
        # Buy 200 liters exact same product, supplier, price
        client.post("/api/purchases", json={
            "date": str(date.today()),
            "supplier_id": sid,
            "product_id": pid,
            "quantity_liters": 200,
            "purchase_price_per_liter": 5000,
        }, headers=admin_headers)
        
        inv_resp = client.get("/api/inventory/batches", headers=admin_headers)
        batches = [b for b in inv_resp.json()["items"] if b["product_id"] == pid]
        
        # Should be merged into 1 batch with 300 initial and remaining
        assert len(batches) == 1
        assert batches[0]["initial_quantity_liters"] == 300
        assert batches[0]["remaining_quantity_liters"] == 300

    def test_cancel_purchase(self, client, admin_headers):
        pid, sid = self._create_dependencies(client, admin_headers)
        
        # Create purchase
        p_resp = client.post("/api/purchases", json={
            "date": str(date.today()),
            "supplier_id": sid,
            "product_id": pid,
            "quantity_liters": 100,
            "purchase_price_per_liter": 5000,
            "payments": [{"payment_type": "cash", "amount": 500000}]
        }, headers=admin_headers)
        
        purchase_id = p_resp.json()["id"]
        
        # Cancel purchase
        c_resp = client.patch(f"/api/purchases/{purchase_id}/cancel", headers=admin_headers)
        assert c_resp.status_code == 200
        assert c_resp.json()["status"] == "cancelled"
        
        # Verify inventory was reverted
        inv_resp = client.get("/api/inventory/batches?status=finished", headers=admin_headers)
        batches = [b for b in inv_resp.json()["items"] if b["product_id"] == pid]
        assert len(batches) == 1
        assert batches[0]["status"] == "finished"
        assert batches[0]["remaining_quantity_liters"] == 0

    def test_cancel_purchase_blocked_if_sold(self, client, admin_headers, db_session):
        from app.models.inventory import InventoryBatch
        pid, sid = self._create_dependencies(client, admin_headers)
        
        p_resp = client.post("/api/purchases", json={
            "date": str(date.today()),
            "supplier_id": sid,
            "product_id": pid,
            "quantity_liters": 100,
            "purchase_price_per_liter": 5000,
        }, headers=admin_headers)
        
        purchase_id = p_resp.json()["id"]
        
        # Simulate sale by manually reducing remaining qty
        batch = db_session.query(InventoryBatch).filter(InventoryBatch.product_id == pid).first()
        batch.remaining_quantity_liters = 50
        db_session.commit()
        
        # Try to cancel
        c_resp = client.patch(f"/api/purchases/{purchase_id}/cancel", headers=admin_headers)
        assert c_resp.status_code == 400
        assert "sotuv qilingan" in c_resp.json()["detail"]
