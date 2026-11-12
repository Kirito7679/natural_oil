"""Bekor qilish hammani oldingi holatiga qaytarishi va o'zaro hisob-kitob.

Mijoz talabi (12.11.2026):
  1. Noto'g'ri kiritilgan amalni o'chirganda baza oldingi holatiga qaytsin.
  2. Bitta odam ham mijoz, ham yetkazib beruvchi bo'lsa, qarzlari bir-biridan
     ayirilsin — hozir ikkalasi alohida ko'rinadi.
"""
from datetime import date

TODAY = str(date.today())


def _scene(client, h):
    """Mahsulot, hamkor, to'langan prixod va omborda partiya.

    Prixod to'liq to'lanadi: aks holda sahna o'zi yetkazib beruvchi qarzini
    yaratib, o'zaro hisob-kitob tekshiruvini chalkashtiradi.
    """
    pid = client.post("/api/products", json={"name": "Benzin 92"}, headers=h).json()["id"]
    partner = client.post("/api/partners", json={"name": "Aka Savdo", "type": "both"},
                          headers=h).json()["id"]
    client.post("/api/balance/adjust",
                json={"payment_type": "cash", "amount": 50_000_000}, headers=h)
    r = client.post("/api/purchases", json={"date": TODAY, "supplier_id": partner,
                                            "product_id": pid, "quantity_liters": 1000,
                                            "purchase_price_per_liter": 9000,
                                            "payments": [{"payment_type": "cash",
                                                          "amount": 9_000_000}]}, headers=h)
    assert r.status_code == 201, r.text
    assert client.get("/api/debts/supplier", headers=h).json()["total"] == 0
    batch = client.get("/api/inventory/batches", headers=h).json()["items"][0]["id"]
    return pid, partner, batch


def _balance(client, h):
    return client.get("/api/balance", headers=h).json()["total_balance"]


def _sale_on_credit(client, h, pid, partner, batch, liters=10):
    """To'lovsiz sotuv — to'liq qarzga ketadi."""
    r = client.post("/api/sales", json={"date": TODAY, "customer_id": partner,
                                        "product_id": pid, "inventory_batch_id": batch,
                                        "quantity_liters": liters,
                                        "sale_price_per_liter": 10000,
                                        "purchase_price_per_liter": 9000}, headers=h)
    assert r.status_code == 201, r.text
    sale = r.json()
    debt = next(d for d in client.get("/api/debts/customer", headers=h).json()["items"]
                if d["sale_id"] == sale["id"])
    return sale, debt


# ── 1. Qarz to'lovini bekor qilish ──────────────────────────────────────────

def test_cancelling_debt_payment_restores_everything(client, admin_headers):
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    sale, debt = _sale_on_credit(client, h, pid, partner, batch)
    assert debt["remaining_amount"] == 100000

    before = _balance(client, h)
    r = client.post(f"/api/debts/customer/{debt['id']}/pay",
                    json={"date": TODAY, "amount": 100000, "payment_type": "cash"}, headers=h)
    assert r.status_code == 201, r.text
    payment_id = r.json()["id"]

    # to'lovdan keyin: qarz yopildi, pul keldi
    paid = client.get(f"/api/debts/customer/{debt['id']}", headers=h).json()
    assert paid["status"] == "closed" and paid["remaining_amount"] == 0
    assert _balance(client, h) == before + 100000

    # bekor qilamiz
    r = client.patch(f"/api/debts/payments/{payment_id}/cancel", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"

    # hammasi oldingi holatida
    back = client.get(f"/api/debts/customer/{debt['id']}", headers=h).json()
    assert back["status"] == "active"
    assert back["remaining_amount"] == 100000
    assert back["paid_amount"] == 0
    assert back["last_payment_date"] is None
    assert _balance(client, h) == before


def test_cancelled_payment_disappears_from_history_and_cannot_repeat(client, admin_headers):
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    sale, debt = _sale_on_credit(client, h, pid, partner, batch)
    pay = client.post(f"/api/debts/customer/{debt['id']}/pay",
                      json={"date": TODAY, "amount": 40000, "payment_type": "cash"},
                      headers=h).json()

    detail = client.get(f"/api/debts/customer/{debt['id']}/detail", headers=h).json()
    assert len(detail["payments"]) == 1

    assert client.patch(f"/api/debts/payments/{pay['id']}/cancel", headers=h).status_code == 200
    detail = client.get(f"/api/debts/customer/{debt['id']}/detail", headers=h).json()
    assert detail["payments"] == []

    # ikkinchi marta bekor qilib bo'lmaydi
    again = client.patch(f"/api/debts/payments/{pay['id']}/cancel", headers=h)
    assert again.status_code == 400
    assert "бекор қилинган" in again.json()["detail"]


def test_payment_cancel_unblocks_sale_cancel(client, admin_headers):
    """Asosiy to'siq: to'lov qilingan sotuvni bekor qilib bo'lmasdi."""
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    sale, debt = _sale_on_credit(client, h, pid, partner, batch)
    pay = client.post(f"/api/debts/customer/{debt['id']}/pay",
                      json={"date": TODAY, "amount": 30000, "payment_type": "cash"},
                      headers=h).json()

    # to'lov turganda sotuv bekor qilinmaydi — tizim "avval to'lovni bekor qiling" deydi
    blocked = client.patch(f"/api/sales/{sale['id']}/cancel", headers=h)
    assert blocked.status_code == 400
    assert "қарз тўлаган" in blocked.json()["detail"]

    # endi buni qilish mumkin
    assert client.patch(f"/api/debts/payments/{pay['id']}/cancel", headers=h).status_code == 200
    freed = client.patch(f"/api/sales/{sale['id']}/cancel", headers=h)
    assert freed.status_code == 200, freed.text
    assert freed.json()["status"] == "cancelled"

    # ombor ham qaytdi
    b = client.get("/api/inventory/batches", headers=h).json()["items"][0]
    assert b["remaining_quantity_liters"] == 1000


def test_supplier_payment_cancel_returns_money(client, admin_headers):
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    # qo'lda yetkazib beruvchi qarzi
    debt = client.post("/api/debts/supplier/manual",
                       json={"partner_id": partner, "total_amount": 500000,
                             "date": TODAY}, headers=h).json()
    client.post("/api/balance/adjust",
                json={"payment_type": "cash", "amount": 1000000}, headers=h)
    before = _balance(client, h)

    pay = client.post(f"/api/debts/supplier/{debt['id']}/pay",
                      json={"date": TODAY, "amount": 200000, "payment_type": "cash"},
                      headers=h).json()
    assert _balance(client, h) == before - 200000

    assert client.patch(f"/api/debts/payments/{pay['id']}/cancel", headers=h).status_code == 200
    assert _balance(client, h) == before
    back = client.get(f"/api/debts/supplier/{debt['id']}", headers=h).json()
    assert back["remaining_amount"] == 500000 and back["status"] == "active"


# ── 2. Qo'lda kiritilgan qarzni bekor qilish ────────────────────────────────

def test_manual_debt_can_be_cancelled(client, admin_headers):
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    debt = client.post("/api/debts/customer/manual",
                       json={"partner_id": partner, "total_amount": 70000,
                             "date": TODAY}, headers=h).json()
    r = client.patch(f"/api/debts/customer/{debt['id']}/cancel", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"
    assert r.json()["remaining_amount"] == 0


def test_sale_linked_debt_cannot_be_cancelled_directly(client, admin_headers):
    """Sotuvdan kelgan qarz faqat sotuv orqali bekor qilinadi — aks holda ikkisi ajralib qoladi."""
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    sale, debt = _sale_on_credit(client, h, pid, partner, batch)
    r = client.patch(f"/api/debts/customer/{debt['id']}/cancel", headers=h)
    assert r.status_code == 400
    assert "сотувни" in r.json()["detail"]


def test_manual_debt_with_payment_asks_to_cancel_payment_first(client, admin_headers):
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    debt = client.post("/api/debts/customer/manual",
                       json={"partner_id": partner, "total_amount": 70000,
                             "date": TODAY}, headers=h).json()
    pay = client.post(f"/api/debts/customer/{debt['id']}/pay",
                      json={"date": TODAY, "amount": 20000, "payment_type": "cash"},
                      headers=h).json()
    blocked = client.patch(f"/api/debts/customer/{debt['id']}/cancel", headers=h)
    assert blocked.status_code == 400
    # to'lovni bekor qilgach — mumkin
    client.patch(f"/api/debts/payments/{pay['id']}/cancel", headers=h)
    assert client.patch(f"/api/debts/customer/{debt['id']}/cancel", headers=h).status_code == 200


# ── 3. O'zaro hisob-kitob ───────────────────────────────────────────────────

def test_net_balance_offsets_both_sides_for_one_partner(client, admin_headers):
    """Mijoz talabi: 10 mln u bizga, 15 mln biz unga → natija 5 mln biz unga."""
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    client.post("/api/debts/customer/manual",
                json={"partner_id": partner, "total_amount": 10_000_000, "date": TODAY},
                headers=h)
    client.post("/api/debts/supplier/manual",
                json={"partner_id": partner, "total_amount": 15_000_000, "date": TODAY},
                headers=h)

    data = client.get("/api/debts/net", headers=h).json()
    row = next(i for i in data["items"] if i["partner_id"] == partner)
    assert row["they_owe_us"] == 10_000_000
    assert row["we_owe_them"] == 15_000_000
    assert row["net"] == -5_000_000      # minus = biz qarzdormiz
    assert row["mutual"] is True
    assert data["mutual_count"] == 1


def test_net_ignores_cancelled_and_paid_debts(client, admin_headers):
    h = admin_headers
    pid, partner, batch = _scene(client, h)
    gone = client.post("/api/debts/customer/manual",
                       json={"partner_id": partner, "total_amount": 1_000_000,
                             "date": TODAY}, headers=h).json()
    client.patch(f"/api/debts/customer/{gone['id']}/cancel", headers=h)
    client.post("/api/debts/supplier/manual",
                json={"partner_id": partner, "total_amount": 2_000_000, "date": TODAY},
                headers=h)

    data = client.get("/api/debts/net", headers=h).json()
    row = next(i for i in data["items"] if i["partner_id"] == partner)
    assert row["they_owe_us"] == 0
    assert row["we_owe_them"] == 2_000_000
    assert row["net"] == -2_000_000
    assert row["mutual"] is False


def test_net_is_empty_without_debts(client, admin_headers):
    data = client.get("/api/debts/net", headers=admin_headers).json()
    assert data["items"] == [] and data["mutual_count"] == 0
