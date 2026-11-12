"""Noto'g'ri kiritilgan amalni TO'G'RILASH (o'chirish emas, o'zgartirish).

Mijoz talabi (12.11.2026): "ҳама нарсани ўчиришга ёки изминеш қилишга" —
boshliq hamma narsani o'chira yoki o'zgartira olishi kerak, va natijada baza
to'g'ri holatda qolishi kerak.
"""
from datetime import date

TODAY = str(date.today())


def _money(client, h, amount=50_000_000):
    client.post("/api/balance/adjust",
                json={"payment_type": "cash", "amount": amount}, headers=h)


def _balance(client, h):
    return client.get("/api/balance", headers=h).json()["total_balance"]


def _scene(client, h):
    pid = client.post("/api/products", json={"name": "Benzin 92"}, headers=h).json()["id"]
    partner = client.post("/api/partners", json={"name": "Aka Savdo", "type": "both"},
                          headers=h).json()["id"]
    _money(client, h)
    client.post("/api/purchases", json={"date": TODAY, "supplier_id": partner,
                                        "product_id": pid, "quantity_liters": 1000,
                                        "purchase_price_per_liter": 9000,
                                        "payments": [{"payment_type": "cash",
                                                      "amount": 9_000_000}]}, headers=h)
    batch = client.get("/api/inventory/batches", headers=h).json()["items"][0]["id"]
    return pid, partner, batch


# ── Sotuvni to'g'rilash ─────────────────────────────────────────────────────

def test_edit_sale_fixes_quantity_inventory_and_debt(client, admin_headers):
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    # 100 litr deb xato kiritildi, aslida 10 litr
    sale = client.post("/api/sales", json={"date": TODAY, "customer_id": partner,
                                           "product_id": pid, "inventory_batch_id": batch,
                                           "quantity_liters": 100,
                                           "sale_price_per_liter": 10000,
                                           "purchase_price_per_liter": 9000}, headers=h).json()
    assert client.get("/api/inventory/batches", headers=h).json()["items"][0]["remaining_quantity_liters"] == 900

    fixed = client.put(f"/api/sales/{sale['id']}",
                       json={"date": TODAY, "customer_id": partner, "product_id": pid,
                             "inventory_batch_id": batch, "quantity_liters": 10,
                             "sale_price_per_liter": 10000,
                             "purchase_price_per_liter": 9000}, headers=h)
    assert fixed.status_code == 200, fixed.text
    assert fixed.json()["quantity_liters"] == 10
    assert fixed.json()["id"] != sale["id"]           # yangi yozuv

    # ombor to'g'ri: 1000 - 10
    assert client.get("/api/inventory/batches", headers=h).json()["items"][0]["remaining_quantity_liters"] == 990
    # eskisi tarixda bekor qilingan bo'lib qoldi
    old = client.get(f"/api/sales/{sale['id']}", headers=h).json()
    assert old["status"] == "cancelled"
    # qarz ham bitta va to'g'ri summada
    debts = [d for d in client.get("/api/debts/customer", headers=h).json()["items"]
             if d["status"] == "active"]
    assert len(debts) == 1 and debts[0]["remaining_amount"] == 100000


def test_failed_edit_leaves_the_old_sale_untouched(client, admin_headers):
    """Eng muhimi: yangisi o'tmasa, eskisi joyida qolishi kerak."""
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    sale = client.post("/api/sales", json={"date": TODAY, "customer_id": partner,
                                           "product_id": pid, "inventory_batch_id": batch,
                                           "quantity_liters": 10,
                                           "sale_price_per_liter": 10000,
                                           "purchase_price_per_liter": 9000}, headers=h).json()

    # omborda 1000 litr bor, 5000 litr sotib bo'lmaydi
    bad = client.put(f"/api/sales/{sale['id']}",
                     json={"date": TODAY, "customer_id": partner, "product_id": pid,
                           "inventory_batch_id": batch, "quantity_liters": 5000,
                           "sale_price_per_liter": 10000,
                           "purchase_price_per_liter": 9000}, headers=h)
    assert bad.status_code == 400

    # eski sotuv o'z holicha: faol, 10 litr, ombor ham o'zgarmagan
    old = client.get(f"/api/sales/{sale['id']}", headers=h).json()
    assert old["status"] == "active" and old["quantity_liters"] == 10
    assert client.get("/api/inventory/batches", headers=h).json()["items"][0]["remaining_quantity_liters"] == 990


# ── Prixodni to'g'rilash ────────────────────────────────────────────────────

def test_edit_purchase_fixes_price_and_balance(client, admin_headers):
    h = admin_headers
    pid = client.post("/api/products", json={"name": "Dizel"}, headers=h).json()["id"]
    sup = client.post("/api/partners", json={"name": "Postavshik", "type": "supplier"},
                      headers=h).json()["id"]
    _money(client, h)
    before = _balance(client, h)
    # narxi xato: 9000 o'rniga 19000 yozilgan
    p = client.post("/api/purchases", json={"date": TODAY, "supplier_id": sup,
                                            "product_id": pid, "quantity_liters": 100,
                                            "purchase_price_per_liter": 19000,
                                            "payments": [{"payment_type": "cash",
                                                          "amount": 1_900_000}]}, headers=h).json()
    assert _balance(client, h) == before - 1_900_000

    fixed = client.put(f"/api/purchases/{p['id']}",
                       json={"date": TODAY, "supplier_id": sup, "product_id": pid,
                             "quantity_liters": 100, "purchase_price_per_liter": 9000,
                             "payments": [{"payment_type": "cash", "amount": 900_000}]},
                       headers=h)
    assert fixed.status_code == 200, fixed.text
    assert fixed.json()["purchase_price_per_liter"] == 9000
    # balansdan faqat to'g'ri summa yechilgan
    assert _balance(client, h) == before - 900_000
    # omborda ham bitta partiya, 100 litr
    batches = [b for b in client.get("/api/inventory/batches", headers=h).json()["items"]
               if b["status"] == "active"]
    assert sum(b["remaining_quantity_liters"] for b in batches) == 100


def test_edit_purchase_blocked_when_already_sold(client, admin_headers):
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    purchase = client.get("/api/purchases", headers=h).json()["items"][0]
    client.post("/api/sales", json={"date": TODAY, "customer_id": partner,
                                    "product_id": pid, "inventory_batch_id": batch,
                                    "quantity_liters": 10, "sale_price_per_liter": 10000,
                                    "purchase_price_per_liter": 9000}, headers=h)
    r = client.put(f"/api/purchases/{purchase['id']}",
                   json={"date": TODAY, "supplier_id": partner, "product_id": pid,
                         "quantity_liters": 500, "purchase_price_per_liter": 9000},
                   headers=h)
    assert r.status_code == 400
    # prixod va ombor o'zgarmagan
    assert client.get("/api/purchases", headers=h).json()["items"][0]["status"] == "active"
    assert client.get("/api/inventory/batches", headers=h).json()["items"][0]["remaining_quantity_liters"] == 990


# ── Xarajatni to'g'rilash ───────────────────────────────────────────────────

def test_edit_expense_fixes_amount_and_balance(client, admin_headers):
    h = admin_headers
    _money(client, h)
    before = _balance(client, h)
    cat = client.get("/api/expenses/categories", headers=h).json()[0]["id"]
    e = client.post("/api/expenses", json={"date": TODAY, "category_id": cat,
                                           "amount": 5_000_000, "payment_type": "cash"},
                    headers=h).json()
    assert _balance(client, h) == before - 5_000_000

    fixed = client.put(f"/api/expenses/{e['id']}",
                       json={"date": TODAY, "category_id": cat, "amount": 500_000,
                             "payment_type": "cash"}, headers=h)
    assert fixed.status_code == 200, fixed.text
    assert fixed.json()["amount"] == 500_000
    assert _balance(client, h) == before - 500_000


# ── Balansni to'g'rilash ────────────────────────────────────────────────────

def test_wrong_cash_top_up_can_be_cancelled(client, admin_headers):
    """Xato kiritilgan "o'zida bor pul" ni qaytarib olish mumkin."""
    h = admin_headers
    before = _balance(client, h)
    r = client.post("/api/balance/add-initial",
                    json={"payment_type": "cash", "amount": 7_000_000, "date": TODAY},
                    headers=h)
    assert r.status_code == 200, r.text
    assert _balance(client, h) == before + 7_000_000

    mv = client.get("/api/balance/movements", headers=h).json()["items"][0]
    r = client.patch(f"/api/balance/movements/{mv['id']}/cancel", headers=h)
    assert r.status_code == 200, r.text
    assert _balance(client, h) == before

    # ikkinchi marta bekor qilib bo'lmaydi
    again = client.patch(f"/api/balance/movements/{mv['id']}/cancel", headers=h)
    assert again.status_code == 400
    assert _balance(client, h) == before


def test_document_movement_cannot_be_cancelled_from_balance(client, admin_headers):
    """Sotuvdan kelgan pul harakatini balansdan bekor qilish taqiqlanadi."""
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    client.post("/api/sales", json={"date": TODAY, "customer_id": partner,
                                    "product_id": pid, "inventory_batch_id": batch,
                                    "quantity_liters": 10, "sale_price_per_liter": 10000,
                                    "purchase_price_per_liter": 9000,
                                    "payments": [{"payment_type": "cash",
                                                  "amount": 100000}]}, headers=h)
    sale_mv = next(m for m in client.get("/api/balance/movements", headers=h).json()["items"]
                   if m["related_table"] == "sales")
    r = client.patch(f"/api/balance/movements/{sale_mv['id']}/cancel", headers=h)
    assert r.status_code == 400
    assert "ҳужжатнинг" in r.json()["detail"]
