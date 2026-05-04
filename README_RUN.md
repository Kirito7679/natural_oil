# Natural Oil ERP — Ishga tushirish bo'yicha qo'llanma

Bu hujjat ERP tizimini kompyuterda ishga tushirish bo'yicha to'liq yo'riqnoma.

---

## 📋 Talablar

Quyidagilar o'rnatilgan bo'lishi kerak:

- **Python 3.11+** — backend uchun
- **Node.js 18+** va **npm** — frontend uchun
- Brauzer (Chrome, Edge, Firefox)

---

## 🚀 Birinchi marta ishga tushirish

### 1-qadam: Backend tayyorlash

Terminal oching va loyiha papkasiga kiring:

```bash
cd backend
pip install -r requirements.txt
```

### 2-qadam: Frontend tayyorlash

**Yangi terminal** oching:

```bash
cd frontend
npm install
```

---

## ▶️ Har kuni ishga tushirish

**Ikkita terminal ochiladi — biri backend, biri frontend uchun.**

### Terminal 1 — Backend:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Backend ishlayotganini bilish uchun:
INFO: Application startup complete.
INFO: Uvicorn running on http://127.0.0.1:8000

### Terminal 2 — Frontend:

```bash
cd frontend
npm run dev
```

Frontend ishlayotganini bilish uchun:
VITE ready in xxx ms
Local: http://localhost:5173

---

## 🌐 Saytga kirish

Brauzerda quyidagi manzilni oching:

- **http://localhost:5173** (yoki 5174 — terminal yozadi)

Login qilish uchun admin akkauntdan foydalaning.

---

## 💾 Database (Ma'lumotlar bazasi)

- Database fayli: **`backend/natural_oil.db`**
- Bu SQLite fayl. Ichida hamma ma'lumot saqlanadi (sotuvlar, xaridlar, balans, qarzlar, foydalanuvchilar va h.k.)
- **MUHIM:** Bu faylni o'chirib yubormang! Aks holda hamma ma'lumot yo'qoladi.
- Backup uchun: `BACKUP_INSTRUCTIONS.md` ga qarang.

---

## ❓ Tez-tez beriladigan savollar

### Kompyuter o'chsa nima bo'ladi?

- Backend va frontend to'xtaydi (sayt ishlamaydi)
- Lekin **ma'lumotlar yo'qolmaydi** — `natural_oil.db` faylida saqlanadi
- Kompyuterni qayta yoqqach, yana **2 ta terminalni ochib** backend va frontend'ni qayta ishga tushiring

### Qayta yoqqandan keyin nima qilish kerak?

```bash
# Terminal 1
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2
cd frontend
npm run dev
```

Va brauzerda http://localhost:5173 ni oching.

### Antigravity kerakmi?

YO'Q. Antigravity faqat dasturni qurish jarayonida ishlatilgan. Sayt ishlashi uchun **faqat backend va frontend terminallari** ochiq bo'lishi kifoya.

### Port band bo'lsa nima qilish kerak?

Boshqa terminal yoki dastur portni ishlatayotgan bo'lishi mumkin. Yechim:
- Boshqa terminallarni yoping
- Yoki kompyuterni qayta yoqing

### Login parolini unutdim?

Boshqa admin foydalanuvchidan **Foydalanuvchilar → Parolni almashtirish** orqali tiklang.

Agar **hech bir admin login qila olmasa** — `BACKUP_INSTRUCTIONS.md` ga qarang yoki dasturchi bilan bog'laning.

---

## 📞 Texnik yordam

Texnik muammo bo'lsa:
- Terminallardagi xato xabarlarini saqlang (screenshot)
- Browser konsolidagi xato xabarini ham qo'shing (F12 → Console)
- Dasturchi bilan bog'laning

---

**Versiya:** Phase 10 (Stable)
**So'nggi yangilanish:** 2026