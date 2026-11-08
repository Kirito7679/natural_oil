"""Ҳисобот таблари — сотув, приход ва харажатдан кейин рақамлар тўғри чиқишини текширади."""
from datetime import date

TODAY = str(date.today())
TABS = ["transactions", "cashflow", "profit", "expenses", "sales", "purchases", "debts", "inventory"]


def _setup(client, h):
    pid = client.post("/api/products", json={"name": "Report Fuel"}, headers=h).json()["id"]
    sup = client.post("/api/partners", json={"name": "Sup R", "type": "supplier"}, headers=h).json()["id"]
    cus = client.post("/api/partners", json={"name": "Cus R", "type": "customer"}, headers=h).json()["id"]
    client.post("/api/balance/adjust", json={"payment_type": "cash", "amount": 10_000_000}, headers=h)
    client.post("/api/purchases", json={"date": TODAY, "supplier_id": sup, "product_id": pid, "quantity_liters": 1000,
                                        "purchase_price_per_liter": 9000,
                                        "payments": [{"payment_type": "cash", "amount": 4_000_000}]}, headers=h)
    batch = client.get("/api/inventory/batches", headers=h).json()["items"][0]["id"]
    client.post("/api/sales", json={"date": TODAY, "customer_id": cus, "product_id": pid, "inventory_batch_id": batch,
                                    "quantity_liters": 100, "sale_price_per_liter": 11000, "purchase_price_per_liter": 9000,
                                    "payments": [{"payment_type": "cash", "amount": 600_000}]}, headers=h)
    cat = client.get("/api/expenses/categories", headers=h).json()[0]["id"]
    client.post("/api/expenses", json={"date": TODAY, "category_id": cat, "amount": 50_000, "payment_type": "cash"}, headers=h)


def test_all_tabs_respond(client, admin_headers):
    _setup(client, admin_headers)
    for t in TABS:
        r = client.get(f"/api/reports/tabs/{t}", params={"date_from": TODAY, "date_to": TODAY}, headers=admin_headers)
        assert r.status_code == 200, (t, r.text)


def test_profit_numbers(client, admin_headers):
    _setup(client, admin_headers)
    t = client.get("/api/reports/tabs/profit", params={"date_from": TODAY, "date_to": TODAY}, headers=admin_headers).json()["totals"]
    assert t["revenue"] == 1_100_000
    assert t["cost"] == 900_000
    assert t["gross_profit"] == 200_000
    assert t["expenses"] == 50_000
    assert t["net_profit"] == 150_000


def test_debts_and_inventory(client, admin_headers):
    _setup(client, admin_headers)
    d = client.get("/api/reports/tabs/debts", headers=admin_headers).json()["totals"]
    assert d["customer_total"] == 500_000
    assert d["supplier_total"] == 5_000_000
    inv = client.get("/api/reports/tabs/inventory", params={"date_from": TODAY, "date_to": TODAY}, headers=admin_headers).json()["totals"]
    assert inv["liters"] == 900
    assert inv["period_in"] == 1000 and inv["period_out"] == 100


def test_product_stats(client, admin_headers):
    _setup(client, admin_headers)
    r = client.get("/api/reports/tabs/products", params={"date_from": TODAY, "date_to": TODAY}, headers=admin_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["highlights"]["most_sold"]["product"] == "Report Fuel"
    top = d["ranking"][0]
    assert top["liters"] == 100 and top["profit"] == 200_000 and top["liters_share"] == 100
    assert "all" in d["timeline"]["series"]


def test_excel_respects_filters(client, admin_headers):
    import io
    from openpyxl import load_workbook
    _setup(client, admin_headers)
    r = client.get("/api/reports/tabs/transactions/excel",
                   params={"date_from": TODAY, "date_to": TODAY, "direction": "outgoing"}, headers=admin_headers)
    assert r.status_code == 200
    ws = load_workbook(io.BytesIO(r.content)).active
    values = [c.value for row in ws.iter_rows() for c in row if c.value is not None]
    assert "Филтр: Фақат чиқим" in values
    assert "Кирим" not in values          # faqat chiqimlar
    assert "Чиқим" in values
    for tab in ["cashflow", "profit", "products", "expenses", "sales", "purchases", "debts", "inventory"]:
        rr = client.get(f"/api/reports/tabs/{tab}/excel", params={"date_from": TODAY, "date_to": TODAY}, headers=admin_headers)
        assert rr.status_code == 200, tab
