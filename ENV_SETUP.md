# Natural Oil ERP — Environment Variables (Sozlamalar)

Bu hujjat `.env` fayllari haqida — qaysi qiymatlar nima uchun kerak.

---

## 📁 `.env` fayli qayerda?

`backend/.env` — backend sozlamalari

`backend/.env.example` — namuna fayl (real qiymatsiz)

---

## 🔑 Sozlamalar tushuntirilishi

### `DATABASE_URL`

Database ulanish manzili.

**Default (SQLite):**
DATABASE_URL=sqlite:///./natural_oil.db

**Production uchun (PostgreSQL):**
DATABASE_URL=postgresql://user:password@localhost/natural_oil

---

### `SECRET_KEY`

JWT token'larni shifrlash uchun maxfiy kalit.

**MUHIM:**
- Production'da albatta o'zgartiring
- Hech qachon GitHub'ga yuklamang
- Tasodifiy uzun matn bo'lishi kerak (kamida 32 belgi)

**Misol:**
SECRET_KEY=your-very-long-random-secret-key-min-32-chars

**Tasodifiy SECRET_KEY yaratish:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### `ACCESS_TOKEN_EXPIRE_MINUTES`

Login token qancha vaqt amal qilishi (daqiqada).

**Default:**
ACCESS_TOKEN_EXPIRE_MINUTES=1440

(1440 daqiqa = 24 soat)

---

### `FRONTEND_URL` / `BACKEND_URL`

Frontend va backend URL'lari (CORS uchun).

**Local:**
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

**Production:**
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://api.yourdomain.com

---

## 📝 To'liq `.env.example` namunasi

```env
# Database
DATABASE_URL=sqlite:///./natural_oil.db

# Auth
SECRET_KEY=change-this-to-a-random-string-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256

# CORS (frontend manzillari)
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

---

## ⚠️ MUHIM XAVFSIZLIK

### ✅ QILISH KERAK:

- `.env` faylini **`.gitignore`** ga qo'shing
- Production uchun har doim **yangi SECRET_KEY** yarating
- Parollarni `.env` da emas, alohida xavfsiz joyda saqlang
- Production'da kuchli admin paroldan foydalaning

### ❌ QILMASLIK KERAK:

- `.env` faylini GitHub'ga yuklamang
- Real `SECRET_KEY` ni hech kimga bermang
- Default `SECRET_KEY` ni production'da ishlatmang
- Database parolini koddagi qattiq kodlamang

---

## 🔄 Production'da SECRET_KEY almashtirish

1. Yangi tasodifiy SECRET_KEY yarating:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. `.env` faylida o'rniga qo'ying:

```env
SECRET_KEY=yangi_yaratilgan_kalit
```

3. Backendni qayta ishga tushiring

4. **DIQQAT:** Bu o'zgarishdan keyin **barcha foydalanuvchilar qayta login qilishi kerak**, chunki eski tokenlar yaroqsiz bo'ladi.

---

**Eslatma:** Lokal kompyuterda ishlash uchun default sozlamalar yetarli. Production deployment'dan oldin ushbu hujjatni qayta o'qing.