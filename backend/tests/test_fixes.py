"""Тузатилган хатолар ва инвестор роли учун тестлар."""
from datetime import date

TODAY = str(date.today())


def _base(client, h):
    pid = client.post("/api/products", json={"name": "Fix Fuel"}, headers=h).json()["id"]
    sup = client.post("/api/partners", json={"name": "Sup F", "type": "supplier"}, headers=h).json()["id"]
    cus = client.post("/api/partners", json={"name": "Cus F", "type": "customer"}, headers=h).json()["id"]
    client.post("/api/purchases", json={"date": TODAY, "supplier_id": sup, "product_id": pid, "quantity_liters": 100,
                                        "purchase_price_per_liter": 9000}, headers=h)
    batch = client.get("/api/inventory/batches", headers=h).json()["items"][0]["id"]
    return pid, sup, cus, batch


def test_unknown_customer_returns_400(client, admin_headers):
    pid, sup, cus, batch = _base(client, admin_headers)
    r = client.post("/api/sales", json={"date": TODAY, "customer_id": 99999, "product_id": pid, "inventory_batch_id": batch,
                                        "quantity_liters": 1, "sale_price_per_liter": 10000, "purchase_price_per_liter": 9000},
                    headers=admin_headers)
    assert r.status_code == 400


def test_supplier_cannot_be_customer(client, admin_headers):
    pid, sup, cus, batch = _base(client, admin_headers)
    r = client.post("/api/sales", json={"date": TODAY, "customer_id": sup, "product_id": pid, "inventory_batch_id": batch,
                                        "quantity_liters": 1, "sale_price_per_liter": 10000, "purchase_price_per_liter": 9000},
                    headers=admin_headers)
    assert r.status_code == 400


def test_unknown_supplier_returns_400(client, admin_headers):
    pid, *_ = _base(client, admin_headers)
    r = client.post("/api/purchases", json={"date": TODAY, "supplier_id": 99999, "product_id": pid, "quantity_liters": 1,
                                            "purchase_price_per_liter": 1}, headers=admin_headers)
    assert r.status_code == 400


def test_no_ghost_debt_on_fractional_sale(client, admin_headers):
    pid, sup, cus, batch = _base(client, admin_headers)
    r = client.post("/api/sales", json={"date": TODAY, "customer_id": cus, "product_id": pid, "inventory_batch_id": batch,
                                        "quantity_liters": 0.1, "sale_price_per_liter": 10500.7, "purchase_price_per_liter": 9000,
                                        "payments": [{"payment_type": "cash", "amount": 1050.07}]}, headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["debt_amount"] == 0
    assert client.get("/api/debts/customer", headers=admin_headers).json()["total"] == 0


def _investor_headers(client, admin_headers):
    r = client.post("/api/users", json={"name": "Investor", "phone": "investor1", "password": "secret12",
                                        "confirm_password": "secret12", "role": "investor"}, headers=admin_headers)
    assert r.status_code == 201, r.text
    tok = client.post("/api/auth/login", json={"phone": "investor1", "password": "secret12"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_investor_can_read_but_not_write(client, admin_headers):
    _base(client, admin_headers)
    inv = _investor_headers(client, admin_headers)
    assert client.get("/api/reports/dashboard", headers=inv).status_code == 200
    assert client.get("/api/reports/tabs/profit", headers=inv).status_code == 200
    assert client.get("/api/products", headers=inv).status_code == 200
    assert client.post("/api/products", json={"name": "X"}, headers=inv).status_code == 403
    assert client.post("/api/balance/adjust", json={"payment_type": "cash", "amount": 1}, headers=inv).status_code == 403
    assert client.get("/api/users", headers=inv).status_code == 403
    r = client.post("/api/users/me/change-password", json={"current_password": "secret12", "new_password": "secret34",
                                                           "confirm_password": "secret34"}, headers=inv)
    assert r.status_code == 200


def test_backdated_sale_goes_to_its_own_day(client, admin_headers):
    from datetime import timedelta
    pid, sup, cus, batch = _base(client, admin_headers)
    yday = str(date.today() - timedelta(days=1))
    client.post("/api/sales", json={"date": yday, "customer_id": cus, "product_id": pid, "inventory_batch_id": batch,
                                    "quantity_liters": 10, "sale_price_per_liter": 10000, "purchase_price_per_liter": 9000,
                                    "payments": [{"payment_type": "cash", "amount": 100000}]}, headers=admin_headers)
    t_y = client.get("/api/reports/tabs/transactions", params={"date_from": yday, "date_to": yday}, headers=admin_headers).json()
    assert t_y["totals"]["income"] == 100000
    t_today = client.get("/api/reports/tabs/transactions", params={"date_from": TODAY, "date_to": TODAY}, headers=admin_headers).json()
    assert t_today["totals"]["income"] == 0


def test_main_user_login_variants(client):
    """Asosiy foydalanuvchi: Хумоюн, login 95 810 06 00 — har xil yozilishda kiradi."""
    for login in ["95 810 06 00", "958100600", "+998 95 810-06-00", "+998958100600"]:
        r = client.post("/api/auth/login", json={"phone": login, "password": "1234567"})
        assert r.status_code == 200, login
        assert r.json()["user"]["name"] == "Хумоюн"


def test_add_user_by_name_and_change_password(client, admin_headers):
    r = client.post("/api/users", json={"name": "Азиз", "phone": "Азиз", "password": "secret12",
                                        "confirm_password": "secret12"}, headers=admin_headers)
    assert r.status_code == 201
    # bir xil login (harf kattaligi boshqacha) qayta qo'shilmaydi
    r2 = client.post("/api/users", json={"name": "Азиз 2", "phone": "азиз", "password": "secret12",
                                         "confirm_password": "secret12"}, headers=admin_headers)
    assert r2.status_code == 400
    assert client.post("/api/auth/login", json={"phone": "азиз", "password": "secret12"}).status_code == 200
    # asosiy foydalanuvchi parolini o'zgartira oladi
    r3 = client.post("/api/users/me/change-password", json={"current_password": "1234567", "new_password": "yangi123",
                                                            "confirm_password": "yangi123"}, headers=admin_headers)
    assert r3.status_code == 200
    assert client.post("/api/auth/login", json={"phone": "958100600", "password": "yangi123"}).status_code == 200


def test_cleanup_migration_keeps_one_user(db_session):
    """Eski bazada bir nechta foydalanuvchi va standart mahsulotlar bo'lsa — bittasi qoladi."""
    from sqlalchemy import text
    from app.models.user import User
    from app.models.product import Product
    from app.seed import seed_database, MIGRATION_KEY
    from app.utils.auth import hash_password
    db_session.execute(text("DELETE FROM app_meta WHERE key = :k"), {"k": MIGRATION_KEY})
    db_session.add_all([User(name="Admin", phone="+998901234567", role="admin", password_hash=hash_password("x12345")),
                        User(name="Admin2", phone="admin2", role="admin", password_hash=hash_password("x12345")),
                        Product(name="AI-95", unit="liter"), Product(name="AI-100", unit="liter")])
    db_session.commit()
    seed_database(db_session)
    users = db_session.query(User).all()
    assert len(users) == 1 and users[0].name == "Хумоюн"
    assert [p.name for p in db_session.query(Product).all()] == ["AI-100"]  # o'zi qo'shgani qoladi
