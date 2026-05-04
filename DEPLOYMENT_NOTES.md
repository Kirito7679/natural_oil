# Natural Oil ERP — Deployment yo'riqnomasi

Bu hujjat — ERP tizimini qayerda ishga tushirish kerakligi haqida tavsiyalar.

**Hozircha haqiqiy deployment qilinmagan** — bu faqat kelgusi rejalar uchun yo'riqnoma.

---

## 🏠 Variant 1: Lokal kompyuter

ERP tizimni shaxsiy kompyuterda ishga tushirish.

### ✅ Afzalliklar:
- Bepul
- Tezkor (lokal)
- Internet kerak emas
- Sozlash juda oson

### ❌ Kamchiliklar:
- Faqat **kompyuter yoqilganda** ishlaydi
- Backend va frontend terminallari **ochiq bo'lishi kerak**
- Boshqa qurilmadan kirib bo'lmaydi (faqat shu kompyuterda)
- Kompyuter o'chsa — sayt ham o'chadi
- Kompyuter buzilsa — ma'lumotlarni yo'qotish xavfi (backup yo'q bo'lsa)

### Kim uchun mos?

- Yangi boshlovchilar
- Sinov uchun
- Faqat 1 kishi ishlatadigan biznes

---

## 🌐 Variant 2: VPS Server (TAVSIYA ETILADI)

Internetga ulangan virtual server.

### ✅ Afzalliklar:
- **24/7 ishlaydi** (kompyuter yoqilishi shart emas)
- Har qanday qurilmadan kirish mumkin (telefon, planshet, boshqa kompyuter)
- Bir nechta foydalanuvchi bir vaqtda ishlaydi
- Backup avtomatik qilish mumkin
- Domen ulash mumkin (yourcompany.com)
- HTTPS (xavfsiz ulanish) mumkin

### ❌ Kamchiliklar:
- Oylik to'lov ($5-20/oy)
- Sozlash ozgina texnik bilim talab qiladi
- Internet zarur

### Tavsiya etiladigan VPS provayderlar:

| Xizmat | Narx | Mos kelishi |
|--------|------|-------------|
| **Hetzner** | €4/oy | Eng arzon, kuchli |
| **DigitalOcean** | $6/oy | Oson, hujjatlari yaxshi |
| **Vultr** | $5/oy | Tezkor |
| **Linode** | $5/oy | Ishonchli |

### Kim uchun mos?

- Kichik va o'rta biznes
- Bir nechta xodimlar ishlatadigan kompaniya
- Doimiy ishlaydigan tizim kerak bo'lganda

---

## ☁️ Variant 3: Cloud Platforms

Boshqaruv osonroq, ammo qimmatroq.

### Tavsiya etiladigan platformalar:

#### **Render**
- Bepul plan bor (lekin sekin)
- Pulli: $7/oy
- Eng oson sozlash
- Backend + frontend birga

#### **Railway**
- Bepul kreditlar bor
- Pulli: $5/oy dan
- Ma'lumotlar bazasi qo'shish oson

#### **Fly.io**
- Bepul tier bor
- Pulli: $1.94/oy dan
- Tezkor

### Kim uchun mos?

- Texnik bilim kam bo'lganlar
- Tezkor ishga tushirmoqchilar

---

## 🗄️ Database tavsiyalari

### Lokal va kichik biznes uchun:
**SQLite** — hozirgi `natural_oil.db` fayli yetarli.

### O'rta va katta biznes uchun:
**PostgreSQL** — ishonchli, tez, ko'p foydalanuvchili.

### Migration:

SQLite'dan PostgreSQL'ga o'tish kerak bo'lsa:

1. Yangi PostgreSQL database yarating
2. `.env` faylida `DATABASE_URL` ni o'zgartiring:
DATABASE_URL=postgresql://user:password@host/dbname
3. Tablitsalar avtomatik yaratiladi (startup'da)
4. Eski ma'lumotlarni `pgloader` yoki shunga o'xshash vosita orqali ko'chiring

---

## 🔒 Production xavfsizligi

Internet'ga chiqarishdan oldin **albatta**:

### 1. SECRET_KEY ni almashtiring

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Default parolni o'zgartiring

`seed.py` da default admin parol bor — production'da:
- Yangi admin yarating
- Eski default adminni o'chiring yoki paroli o'zgartiring

### 3. HTTPS yoqing

- VPS'da: **Let's Encrypt** (bepul)
- Cloud platformlarda: avtomatik

### 4. Firewall sozlang

Faqat zaruriy portlarni oching:
- 80 (HTTP)
- 443 (HTTPS)
- 22 (SSH — admin uchun)

### 5. Avtomatik backup sozlang

Har kuni database faylini boshqa joyga ko'chirish (cron job).

### 6. CORS sozlamalarini yangilang

`main.py` da `allow_origins` ga faqat real domen qo'shing:
```python
allow_origins=["https://yourdomain.com"]
```

---

## 📋 Production tayyorgarlik Checklist

Internet'ga chiqarishdan oldin tekshiring:

- [ ] SECRET_KEY almashtirildi
- [ ] Default admin paroli o'zgartirildi
- [ ] `.env` fayli GitHub'ga yuklanmagan
- [ ] HTTPS yoqilgan
- [ ] Firewall sozlangan
- [ ] Avtomatik backup ishlaydi
- [ ] CORS faqat real domen uchun
- [ ] Database PostgreSQL (kichik bo'lmasa)
- [ ] Server logs yoqilgan
- [ ] Monitoring sozlangan (UptimeRobot va h.k.)

---

## 💰 Taxminiy oylik xarajat

| Variant | Oylik xarajat |
|---------|---------------|
| Lokal kompyuter | 0$ |
| VPS (Hetzner) | ~$5/oy |
| VPS (DigitalOcean) | ~$6/oy |
| Cloud (Render Pro) | ~$7/oy |
| Domen | ~$10-15/yil |
| **Jami (production)** | **~$5-8/oy + $1/oy domen** |

---

## 🎯 Tavsiya qilingan yo'l

1. **Hozir:** Lokal kompyuterda foydalaning, biznesni o'rganib oling
2. **3-6 oydan keyin:** Hetzner yoki DigitalOcean'da VPS oling
3. **1 yildan keyin:** Agar biznes katta bo'lsa — PostgreSQL'ga ko'chiring

---

**Eslatma:** Ushbu hujjat — kelgusi rejalar uchun. Hozir lokal foydalanish to'liq ishlaydi va ko'p kichik biznes uchun yetarli.