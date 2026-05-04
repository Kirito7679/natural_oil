"""Tests for Products CRUD API.

Covers:
- List products (seed data)
- Create product
- Duplicate product name rejected
- Empty product name rejected
- Update product
- Toggle product active/inactive
- Get single product
- Product not found
"""


class TestListProducts:
    """Test product listing."""

    def test_list_all_products(self, client, admin_headers):
        resp = client.get("/api/products", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 6  # seed products
        names = {p["name"] for p in data["items"]}
        assert "AI-80" in names
        assert "AI-91" in names
        assert "AI-92" in names
        assert "AI-95" in names
        assert "Dizel" in names

    def test_list_active_only(self, client, admin_headers, db_session):
        from app.models.product import Product
        # Deactivate one product
        p = db_session.query(Product).filter(Product.name == "AI-80").first()
        p.is_active = False
        db_session.commit()

        resp = client.get("/api/products?active_only=true", headers=admin_headers)
        assert resp.status_code == 200
        names = {p["name"] for p in resp.json()["items"]}
        assert "AI-80" not in names

    def test_all_products_have_liter_unit(self, client, admin_headers):
        resp = client.get("/api/products", headers=admin_headers)
        for p in resp.json()["items"]:
            assert p["unit"] == "liter"


class TestCreateProduct:
    """Test product creation."""

    def test_create_product(self, client, admin_headers):
        resp = client.post("/api/products", json={
            "name": "Metan gaz",
            "note": "Test mahsulot",
        }, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Metan gaz"
        assert data["unit"] == "liter"
        assert data["is_active"] is True
        assert data["note"] == "Test mahsulot"

    def test_duplicate_name_rejected(self, client, admin_headers):
        resp = client.post("/api/products", json={
            "name": "AI-92",
        }, headers=admin_headers)
        assert resp.status_code == 400
        assert "allaqachon mavjud" in resp.json()["detail"]

    def test_empty_name_rejected(self, client, admin_headers):
        resp = client.post("/api/products", json={
            "name": "  ",
        }, headers=admin_headers)
        assert resp.status_code == 422


class TestUpdateProduct:
    """Test product editing."""

    def test_update_product_name(self, client, admin_headers, db_session):
        from app.models.product import Product
        p = db_session.query(Product).filter(Product.name == "Boshqa").first()

        resp = client.put(f"/api/products/{p.id}", json={
            "name": "Boshqa yoqilg'i",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Boshqa yoqilg'i"

    def test_update_with_duplicate_name_rejected(self, client, admin_headers, db_session):
        from app.models.product import Product
        p = db_session.query(Product).filter(Product.name == "AI-80").first()

        resp = client.put(f"/api/products/{p.id}", json={
            "name": "AI-92",
        }, headers=admin_headers)
        assert resp.status_code == 400

    def test_update_nonexistent_product(self, client, admin_headers):
        resp = client.put("/api/products/9999", json={
            "name": "Test",
        }, headers=admin_headers)
        assert resp.status_code == 404


class TestToggleProduct:
    """Test activate/deactivate product."""

    def test_toggle_deactivate(self, client, admin_headers, db_session):
        from app.models.product import Product
        p = db_session.query(Product).filter(Product.name == "AI-80").first()
        assert p.is_active is True

        resp = client.patch(f"/api/products/{p.id}/toggle", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_toggle_reactivate(self, client, admin_headers, db_session):
        from app.models.product import Product
        p = db_session.query(Product).filter(Product.name == "AI-80").first()
        p.is_active = False
        db_session.commit()

        resp = client.patch(f"/api/products/{p.id}/toggle", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True


class TestGetProduct:
    """Test getting single product."""

    def test_get_product(self, client, admin_headers, db_session):
        from app.models.product import Product
        p = db_session.query(Product).filter(Product.name == "AI-92").first()

        resp = client.get(f"/api/products/{p.id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "AI-92"

    def test_get_nonexistent(self, client, admin_headers):
        resp = client.get("/api/products/9999", headers=admin_headers)
        assert resp.status_code == 404
