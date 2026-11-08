"""DEV roli: direktor bilan bir xil to'liq huquq, faqat nomi boshqa.

Direktor (admin) — biznes egasi. DEV — tizimga javob beradigan texnik ma'mur.
"""


def _dev_headers(client, admin_headers):
    r = client.post("/api/users", json={"name": "Dilmurod Nurkhonov", "phone": "900350151",
                                        "password": "secret12", "confirm_password": "secret12",
                                        "role": "dev"}, headers=admin_headers)
    assert r.status_code == 201, r.text
    assert r.json()["role"] == "dev"
    tok = client.post("/api/auth/login", json={"phone": "900350151", "password": "secret12"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_dev_has_same_access_as_director(client, admin_headers):
    dev = _dev_headers(client, admin_headers)
    # foydalanuvchilarni boshqarish — faqat to'liq huquqli rollar uchun
    assert client.get("/api/users", headers=dev).status_code == 200
    # yozish amallari
    assert client.post("/api/products", json={"name": "Dev Fuel"}, headers=dev).status_code == 201
    assert client.post("/api/balance/adjust", json={"payment_type": "cash", "amount": 1},
                       headers=dev).status_code in (200, 201)
    # o'qish
    assert client.get("/api/reports/dashboard", headers=dev).status_code == 200


def test_dev_can_login_with_any_phone_format(client, admin_headers):
    _dev_headers(client, admin_headers)
    for login in ("+998900350151", "90 035 01 51", "900350151"):
        r = client.post("/api/auth/login", json={"phone": login, "password": "secret12"})
        assert r.status_code == 200, f"{login}: {r.text}"
        assert r.json()["user"]["role"] == "dev"


def test_dev_does_not_replace_last_director(client, admin_headers):
    """DEV bor bo'lsa ham oxirgi faol direktorni o'chirib/rolini o'zgartirib bo'lmaydi."""
    _dev_headers(client, admin_headers)
    director = next(u for u in client.get("/api/users", headers=admin_headers).json() if u["role"] == "admin")
    assert client.patch(f"/api/users/{director['id']}", json={"is_active": False},
                        headers=admin_headers).status_code == 400
    assert client.patch(f"/api/users/{director['id']}", json={"role": "investor"},
                        headers=admin_headers).status_code == 400


def test_operator_and_investor_still_blocked_from_user_management(client, admin_headers):
    for role in ("operator", "investor"):
        r = client.post("/api/users", json={"name": f"U {role}", "phone": f"login-{role}",
                                            "password": "secret12", "confirm_password": "secret12",
                                            "role": role}, headers=admin_headers)
        assert r.status_code == 201, r.text
        tok = client.post("/api/auth/login", json={"phone": f"login-{role}",
                                                   "password": "secret12"}).json()["access_token"]
        h = {"Authorization": f"Bearer {tok}"}
        assert client.get("/api/users", headers=h).status_code == 403
