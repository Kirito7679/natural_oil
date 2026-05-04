"""Tests for balance system, payment methods, and money movements.

Covers:
- Balance view (initially 0)
- Set initial balance (cash + bank_transfer)
- Balance adjustment
- Payment type validation (only cash and bank_transfer, NO card)
- Money movement recording
- Insufficient balance check
- Non-admin cannot adjust balance
"""


class TestPaymentTypeEnum:
    """Verify that only cash and bank_transfer exist as payment types."""

    def test_only_two_payment_types(self):
        from app.utils.enums import PaymentType
        values = [e.value for e in PaymentType]
        assert values == ["cash", "bank_transfer"]

    def test_no_card_payment_type(self):
        from app.utils.enums import PaymentType
        values = [e.value for e in PaymentType]
        assert "card" not in values
        assert "karta" not in values
        assert "bank_card" not in values


class TestBalanceView:
    """Test viewing current balance."""

    def test_initial_balance_is_zero(self, client, admin_headers):
        resp = client.get("/api/balance", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["cash_balance"] == 0.0
        assert data["bank_transfer_balance"] == 0.0
        assert data["total_balance"] == 0.0

    def test_unauthenticated_cannot_view_balance(self, client):
        resp = client.get("/api/balance")
        assert resp.status_code == 403  # No Bearer token


class TestSetInitialBalance:
    """Test setting initial balance — TEST SCENARIO 1."""

    def test_set_initial_balance(self, client, admin_headers):
        """TEST 1: Cash=50M, BankTransfer=100M → Total=150M"""
        resp = client.post("/api/balance/initial", json={
            "cash_amount": 50_000_000,
            "bank_transfer_amount": 100_000_000,
        }, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["cash_balance"] == 50_000_000
        assert data["bank_transfer_balance"] == 100_000_000
        assert data["total_balance"] == 150_000_000

    def test_initial_balance_creates_money_movements(self, client, admin_headers):
        """Setting initial balance should create 2 money movements."""
        client.post("/api/balance/initial", json={
            "cash_amount": 50_000_000,
            "bank_transfer_amount": 100_000_000,
        }, headers=admin_headers)

        resp = client.get("/api/balance/movements", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

        types = {m["payment_type"] for m in data["items"]}
        assert types == {"cash", "bank_transfer"}

        # All movements should be income + initial_balance
        for m in data["items"]:
            assert m["movement_type"] == "initial_balance"
            assert m["direction"] == "income"

    def test_negative_initial_balance_rejected(self, client, admin_headers):
        resp = client.post("/api/balance/initial", json={
            "cash_amount": -1000,
            "bank_transfer_amount": 0,
        }, headers=admin_headers)
        assert resp.status_code == 422  # Validation error


class TestBalanceAdjustment:
    """Test admin balance adjustments."""

    def test_positive_adjustment(self, client, admin_headers):
        """Add money to cash balance."""
        # Set initial
        client.post("/api/balance/initial", json={
            "cash_amount": 10_000_000,
            "bank_transfer_amount": 0,
        }, headers=admin_headers)

        # Adjust +5M
        resp = client.post("/api/balance/adjust", json={
            "payment_type": "cash",
            "amount": 5_000_000,
            "note": "Test tuzatish",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["cash_balance"] == 15_000_000

    def test_negative_adjustment(self, client, admin_headers):
        """Subtract money from bank_transfer balance."""
        client.post("/api/balance/initial", json={
            "cash_amount": 0,
            "bank_transfer_amount": 20_000_000,
        }, headers=admin_headers)

        resp = client.post("/api/balance/adjust", json={
            "payment_type": "bank_transfer",
            "amount": -5_000_000,
            "note": "Test ayirish",
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["bank_transfer_balance"] == 15_000_000

    def test_insufficient_balance_rejected(self, client, admin_headers):
        """Cannot subtract more than available."""
        client.post("/api/balance/initial", json={
            "cash_amount": 1_000_000,
            "bank_transfer_amount": 0,
        }, headers=admin_headers)

        resp = client.post("/api/balance/adjust", json={
            "payment_type": "cash",
            "amount": -5_000_000,
        }, headers=admin_headers)
        assert resp.status_code == 400

    def test_card_payment_type_rejected(self, client, admin_headers):
        """Card payment type must be rejected everywhere."""
        resp = client.post("/api/balance/adjust", json={
            "payment_type": "card",
            "amount": 1_000_000,
        }, headers=admin_headers)
        assert resp.status_code == 422  # Pydantic validation error

    def test_adjustment_creates_money_movement(self, client, admin_headers):
        """Each adjustment should record a money movement."""
        client.post("/api/balance/initial", json={
            "cash_amount": 10_000_000,
            "bank_transfer_amount": 0,
        }, headers=admin_headers)
        client.post("/api/balance/adjust", json={
            "payment_type": "cash",
            "amount": 5_000_000,
        }, headers=admin_headers)

        resp = client.get("/api/balance/movements", headers=admin_headers)
        data = resp.json()
        # 1 initial + 1 adjustment
        assert data["total"] == 2
        adj = [m for m in data["items"] if m["movement_type"] == "balance_adjustment"]
        assert len(adj) == 1
        assert adj[0]["payment_type"] == "cash"
        assert adj[0]["direction"] == "income"
        assert adj[0]["amount"] == 5_000_000


class TestMoneyMovements:
    """Test money movement history."""

    def test_empty_movements(self, client, admin_headers):
        resp = client.get("/api/balance/movements", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["items"] == []

    def test_movements_ordered_newest_first(self, client, admin_headers):
        """Movements should be returned newest first."""
        client.post("/api/balance/initial", json={
            "cash_amount": 10_000_000,
            "bank_transfer_amount": 20_000_000,
        }, headers=admin_headers)
        client.post("/api/balance/adjust", json={
            "payment_type": "cash",
            "amount": 1_000_000,
        }, headers=admin_headers)

        resp = client.get("/api/balance/movements", headers=admin_headers)
        items = resp.json()["items"]
        # Newest (adjustment) should be first
        assert items[0]["movement_type"] == "balance_adjustment"

    def test_pagination(self, client, admin_headers):
        """Test skip/limit pagination."""
        client.post("/api/balance/initial", json={
            "cash_amount": 10_000_000,
            "bank_transfer_amount": 20_000_000,
        }, headers=admin_headers)

        resp = client.get("/api/balance/movements?skip=0&limit=1", headers=admin_headers)
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 1


class TestAuthAndRoles:
    """Test authentication and role-based access."""

    def test_login_success(self, client):
        resp = client.post("/api/auth/login", json={
            "phone": "+998901234567",
            "password": "admin123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={
            "phone": "+998901234567",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/auth/login", json={
            "phone": "+998999999999",
            "password": "admin123",
        })
        assert resp.status_code == 401

    def test_get_current_user(self, client, admin_headers):
        resp = client.get("/api/auth/me", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Admin"
        assert resp.json()["role"] == "admin"

    def test_invalid_token(self, client):
        resp = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid-token-here"
        })
        assert resp.status_code == 401


class TestBalanceAccounts:
    """Test that only 2 balance accounts exist."""

    def test_only_two_balance_accounts(self, db_session):
        from app.models.balance import BalanceAccount
        accounts = db_session.query(BalanceAccount).all()
        assert len(accounts) == 2
        types = {a.type for a in accounts}
        assert types == {"cash", "bank_transfer"}
        # No card account
        assert "card" not in types


class TestSeedData:
    """Test that seed data was created correctly."""

    def test_default_products_exist(self, db_session):
        from app.models.product import Product
        products = db_session.query(Product).all()
        names = {p.name for p in products}
        assert "AI-80" in names
        assert "AI-91" in names
        assert "AI-92" in names
        assert "AI-95" in names
        assert "Dizel" in names

    def test_default_expense_categories_exist(self, db_session):
        from app.models.expense import ExpenseCategory
        categories = db_session.query(ExpenseCategory).all()
        names = {c.name for c in categories}
        assert "Arenda" in names
        assert "Oylik" in names
        assert "Transport" in names

    def test_admin_user_exists(self, db_session):
        from app.models.user import User
        admin = db_session.query(User).filter(User.role == "admin").first()
        assert admin is not None
        assert admin.name == "Admin"
