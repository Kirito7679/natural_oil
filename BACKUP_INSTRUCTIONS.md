# Natural Oil ERP — Backup yo'riqnomasi

Backup — bu ma'lumotlar va kodning **zaxira nusxasi**. Kompyuter buzilsa, fayl o'chib ketsa yoki xato yuz bersa, backup'dan tiklab olish mumkin.

---

## 🔴 Nima uchun backup muhim?

`natural_oil.db` fayli — sizning **butun biznes ma'lumotingizni** o'z ichida saqlaydi:
- Barcha sotuvlar
- Barcha xaridlar
- Mijozlar va yetkazib beruvchilar
- Qarzlar va to'lovlar
- Xarajatlar
- Balanslar
- Foydalanuvchilar

**Agar bu fayl yo'qolsa — ma'lumotlarni qaytarib bo'lmaydi.**

---

## 📅 Qachon backup qilish kerak?

| Holat | Tavsiya |
|-------|---------|
| Har kuni | Tavsiya etiladi (kun oxirida) |
| Har hafta | Minimal — kamida haftada 1 marta |
| Yangilik kiritishdan oldin | Albatta backup qiling |
| Kompyuterni yangilashdan oldin | Albatta backup qiling |
| Katta operatsiyalardan oldin | Albatta (masalan, ko'p sotuv kiritishdan oldin) |

---

## 💾 1-usul: Faqat database backup (tezkor)

Eng muhim fayl bu **`backend/natural_oil.db`**.

### Qadamlar:

1. Backendni to'xtating (terminalda `Ctrl+C`)
2. `backend/` papkasiga kiring
3. `natural_oil.db` faylini boshqa joyga ko'chiring (kopiya qiling)
4. Faylga sanali nom bering:
5. Backendni qayta ishga tushiring

### Qayerda saqlash kerak?

- Tashqi disk (USB flash, tashqi HDD)
- Bulutli xizmat (Google Drive, Dropbox, Yandex Disk)
- Boshqa kompyuter
- **Bir nechta joyda** saqlash eng yaxshi

---

## 📦 2-usul: To'liq loyiha backup (tavsiya etiladi)

Butun loyihani zip qilib saqlash.

### Qadamlar:

1. Backend va frontend terminallarini to'xtating
2. `inner-feynman/` papkasini topib oling
3. Sichqonchaning o'ng tugmasini bosing → **Send to** → **Compressed (zipped) folder**
4. Yaratilgan zip fayliga nom bering:
5. Bu zip faylni xavfsiz joyga saqlang

### MUHIM:

- Zip qilishdan oldin `node_modules/` papkasini **chiqarib tashlash mumkin** (juda katta) — keyin `npm install` orqali qaytariladi
- Lekin **`backend/natural_oil.db` faylini ALBATTA qo'shing** — aks holda ma'lumotlar yo'qoladi

---

## 🔄 Backup'dan tiklash

### Faqat database tiklash:

1. Backendni to'xtating
2. Backup fayl (`natural_oil_backup_2026-05-03.db`) ni `backend/` papkasiga ko'chiring
3. Nomini `natural_oil.db` ga o'zgartiring (eski faylni o'chirib yoki nomini boshqa qilib)
4. Backendni qayta ishga tushiring

### To'liq loyihadan tiklash:

1. Yangi joyga zip faylni unzip qiling
2. `cd backend && pip install -r requirements.txt`
3. `cd frontend && npm install`
4. Odatdagidek ishga tushiring

---

## ⚠️ Backup nomlari uchun tavsiyalar

Yaxshi nom — bu **sana bilan**:

✅ Yaxshi:
❌ Yomon (qaysi sanasi noma'lum):
---

## 🚨 Eslatma

**Faqat kod backup qilish YETARLI EMAS.**

Agar siz kodni backup qilsangiz, lekin `natural_oil.db` faylini qo'shmasangiz — **biznes ma'lumotlari yo'qoladi**.

Backup ichida **DOIM** quyidagilar bo'lishi kerak:
- ✅ `backend/` papka (kod + database)
- ✅ `frontend/` papka (kod)
- ✅ `backend/natural_oil.db` (database fayli)
- ✅ `.env` fayllari (sozlamalar)

---

**Eng yaxshi tavsiya: Har kuni kun oxirida 1 marta `natural_oil.db` ni boshqa joyga nusxa ko'chiring.**