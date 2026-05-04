"""Tests for Partners CRUD API.

Covers:
- Create partner (customer, supplier, both)
- List all partners
- Filter by type
- Search
- Update partner
- Toggle active
- Get single partner
- Validation
"""


class TestCreatePartner:
    """Test partner creation."""

    def test_create_customer(self, client, admin_headers):
        resp = client.post("/api/partners", json={
            "name": "Alisher Savdo",
            "phone": "+998901111111",
            "company_name": "Alisher LLC",
            "type": "customer",
        }, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Alisher Savdo"
        assert data["type"] == "customer"
        assert data["is_active"] is True

    def test_create_supplier(self, client, admin_headers):
        resp = client.post("/api/partners", json={
            "name": "Neft Zavod",
            "phone": "+998902222222",
            "type": "supplier",
        }, headers=admin_headers)
        assert resp.status_code == 201
        assert resp.json()["type"] == "supplier"

    def test_create_both_type(self, client, admin_headers):
        resp = client.post("/api/partners", json={
            "name": "Universal Trade",
            "type": "both",
        }, headers=admin_headers)
        assert resp.status_code == 201
        assert resp.json()["type"] == "both"

    def test_empty_name_rejected(self, client, admin_headers):
        resp = client.post("/api/partners", json={
            "name": "  ",
            "type": "customer",
        }, headers=admin_headers)
        assert resp.status_code == 422

    def test_default_type_is_customer(self, client, admin_headers):
        resp = client.post("/api/partners", json={
            "name": "Default Type Test",
        }, headers=admin_headers)
        assert resp.status_code == 201
        assert resp.json()["type"] == "customer"


class TestListPartners:
    """Test partner listing and filtering."""

    def _create_test_partners(self, client, admin_headers):
        """Helper to create a set of test partners."""
        client.post("/api/partners", json={
            "name": "Mijoz A",
            "type": "customer",
        }, headers=admin_headers)
        client.post("/api/partners", json={
            "name": "Yetkazuvchi B",
            "type": "supplier",
        }, headers=admin_headers)
        client.post("/api/partners", json={
            "name": "Ikkalasi C",
            "type": "both",
            "company_name": "Universal Corp",
        }, headers=admin_headers)

    def test_list_all(self, client, admin_headers):
        self._create_test_partners(client, admin_headers)
        resp = client.get("/api/partners", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 3

    def test_filter_customers(self, client, admin_headers):
        """Filtering by 'customer' should return customers + both."""
        self._create_test_partners(client, admin_headers)
        resp = client.get("/api/partners?partner_type=customer", headers=admin_headers)
        assert resp.status_code == 200
        types = {p["type"] for p in resp.json()["items"]}
        assert "supplier" not in types  # only customer and both

    def test_filter_suppliers(self, client, admin_headers):
        """Filtering by 'supplier' should return suppliers + both."""
        self._create_test_partners(client, admin_headers)
        resp = client.get("/api/partners?partner_type=supplier", headers=admin_headers)
        assert resp.status_code == 200
        types = {p["type"] for p in resp.json()["items"]}
        assert "customer" not in types  # only supplier and both

    def test_search_by_name(self, client, admin_headers):
        self._create_test_partners(client, admin_headers)
        resp = client.get("/api/partners?search=Mijoz", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
        assert any("Mijoz" in p["name"] for p in resp.json()["items"])

    def test_search_by_company_name(self, client, admin_headers):
        self._create_test_partners(client, admin_headers)
        resp = client.get("/api/partners?search=Universal", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_active_only_filter(self, client, admin_headers, db_session):
        from app.models.partner import Partner
        self._create_test_partners(client, admin_headers)
        # Deactivate one
        p = db_session.query(Partner).filter(Partner.name == "Mijoz A").first()
        if p:
            p.is_active = False
            db_session.commit()

        resp = client.get("/api/partners?active_only=true", headers=admin_headers)
        names = {p["name"] for p in resp.json()["items"]}
        assert "Mijoz A" not in names


class TestUpdatePartner:
    """Test partner editing."""

    def test_update_partner(self, client, admin_headers):
        # Create first
        create_resp = client.post("/api/partners", json={
            "name": "Edit Test",
            "type": "customer",
        }, headers=admin_headers)
        pid = create_resp.json()["id"]

        resp = client.put(f"/api/partners/{pid}", json={
            "name": "Updated Name",
            "phone": "+998903333333",
            "type": "supplier",
        }, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"
        assert data["phone"] == "+998903333333"
        assert data["type"] == "supplier"

    def test_update_nonexistent(self, client, admin_headers):
        resp = client.put("/api/partners/9999", json={
            "name": "Ghost",
        }, headers=admin_headers)
        assert resp.status_code == 404


class TestTogglePartner:
    """Test activate/deactivate partner."""

    def test_toggle(self, client, admin_headers):
        create_resp = client.post("/api/partners", json={
            "name": "Toggle Test",
        }, headers=admin_headers)
        pid = create_resp.json()["id"]
        assert create_resp.json()["is_active"] is True

        resp = client.patch(f"/api/partners/{pid}/toggle", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        # Toggle back
        resp = client.patch(f"/api/partners/{pid}/toggle", headers=admin_headers)
        assert resp.json()["is_active"] is True


class TestGetPartner:
    """Test getting single partner."""

    def test_get_partner(self, client, admin_headers):
        create_resp = client.post("/api/partners", json={
            "name": "Get Test",
            "type": "both",
        }, headers=admin_headers)
        pid = create_resp.json()["id"]

        resp = client.get(f"/api/partners/{pid}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Test"
        assert resp.json()["type"] == "both"

    def test_get_nonexistent(self, client, admin_headers):
        resp = client.get("/api/partners/9999", headers=admin_headers)
        assert resp.status_code == 404
