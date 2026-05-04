# Natural Oil ERP — Manual Test Checklist

Bu hujjat ERP tizimining barcha asosiy oqimlarini brauzerda qo'lda tekshirish uchun.

Har bir bandga ✅ qo'yib boring. Xato bo'lsa — qaysi bandda ekanligini yozib qo'ying.

---

## 1. Login (Kirish)

- [ ] Admin login qila oladi (telefon + parol)
- [ ] Noto'g'ri parol bilan login bo'lmaydi
- [ ] Nofaol foydalanuvchi login qila olmaydi
- [ ] Login muvaffaqiyatli bo'lganda Dashboard ochiladi

---

## 2. Foydalanuvchilar (Users)

- [ ] Foydalanuvchilar sahifasi ochiladi
- [ ] Mavjud foydalanuvchilar ro'yxati ko'rinadi
- [ ] Yangi foydalanuvchi yaratiladi
- [ ] Yangi foydalanuvchi login qila oladi
- [ ] Mening parolim — joriy parolni almashtirish ishlaydi
- [ ] Boshqa foydalanuvchining parolini almashtirib bo'ladi
- [ ] Foydalanuvchini nofaol qilib bo'ladi
- [ ] Nofaol foydalanuvchi login qila olmaydi
- [ ] Oxirgi faol adminni nofaol qilib bo'lmaydi (xato chiqadi)

---

## 3. Mahsulotlar (Products)

- [ ] Mahsulotlar ro'yxati ko'rinadi
- [ ] Default mahsulotlar mavjud (AI-92, AI-95, dizel, va h.k.)
- [ ] Faol mahsulotlar Prixod va Sotuv formalarida ko'rinadi

---

## 4. Hamkorlar (Partners)

- [ ] Mijoz yaratish ishlaydi
- [ ] Yetkazib beruvchi yaratish ishlaydi
- [ ] "Ikkala tomon" turi yaratiladi
- [ ] Yaratilgan mijoz Sotuv formasida ko'rinadi
- [ ] Yaratilgan yetkazib beruvchi Prixod formasida ko'rinadi
- [ ] Hamkorni nofaol qilib bo'ladi

---

## 5. Prixod (Purchases)

- [ ] To'liq to'langan prixod yaratish (balans kamayadi)
- [ ] Qisman to'langan prixod (balans qisman kamayadi, qarz hosil bo'ladi)
- [ ] To'liq qarzga prixod (balans o'zgarmaydi, qarz hosil bo'ladi)
- [ ] Naqd to'lov bilan — naqd balans kamayadi
- [ ] Perechisleniya bilan — perechisleniya balansi kamayadi
- [ ] Split to'lov (naqd + perechisleniya) ishlaydi
- [ ] Inventory batch yaratiladi
- [ ] Yetkazib beruvchi qarzi hosil bo'ladi
- [ ] Money movement yaratiladi
- [ ] Prixodni bekor qilish ishlaydi (balans qaytadi)
- [ ] Karta to'lov turi YO'Q (faqat Naqd va Perechisleniya)

---

## 6. Ombor (Inventory)

- [ ] Ombor sahifasi ochiladi
- [ ] Har bir batch bo'yicha qoldiq ko'rinadi
- [ ] Tugagan batch'lar "Tugagan" deb belgilanadi
- [ ] Umumiy qoldiq mahsulot bo'yicha to'g'ri hisoblanadi

---

## 7. Sotuv (Sales)

- [ ] To'liq to'langan sotuv yaratiladi
- [ ] Qisman to'langan sotuv (mijoz qarzi hosil bo'ladi)
- [ ] Qarzga sotuv (balans o'zgarmaydi, qarz hosil bo'ladi)
- [ ] Inventory'dan miqdor kamayadi
- [ ] Naqd sotuv — naqd balans oshadi
- [ ] Perechisleniya sotuv — perechisleniya balansi oshadi
- [ ] Split to'lov ishlaydi
- [ ] Foyda hisob-kitobi to'g'ri (sotish narxi − tannarx)
- [ ] Sotuvni bekor qilish ishlaydi (inventory qaytadi, balans qaytadi)

---

## 8. Qarzdorlar (Customer Debts)

- [ ] Faol qarzlar ro'yxati ko'rinadi
- [ ] Qarzni qisman to'lash ishlaydi
- [ ] Qarzni to'liq to'lash — qarz "Yopilgan" bo'ladi
- [ ] Qarz to'lashda balans oshadi
- [ ] Qolgan qarzdan ko'p summa to'lab bo'lmaydi (xato chiqadi)

---

## 9. Bizning qarzlar (Supplier Debts)

- [ ] Faol qarzlar ro'yxati ko'rinadi
- [ ] Qarzni qisman to'lash ishlaydi
- [ ] Qarzni to'liq to'lash — qarz "Yopilgan" bo'ladi
- [ ] Qarz to'lashda balans kamayadi
- [ ] Balansda yetarli pul bo'lmasa — xato chiqadi

---

## 10. Xarajatlar (Expenses)

- [ ] Xarajat kategoriya yaratish ishlaydi
- [ ] Naqd xarajat — naqd balans kamayadi
- [ ] Perechisleniya xarajat — perechisleniya balansi kamayadi
- [ ] Balansda yetarli pul yo'q bo'lsa — xato chiqadi
- [ ] Xarajatni bekor qilish — balans qaytadi
- [ ] Bugungi/jami/naqd/perechisleniya xulosa kartochkalari to'g'ri

---

## 11. Hisobot (Reports)

- [ ] Dashboard'da bugungi sotuv, foyda, xarajat to'g'ri ko'rinadi
- [ ] Balans (naqd + perechisleniya + jami) to'g'ri
- [ ] Mijozlar va bizning qarzlar jami to'g'ri
- [ ] Hisobot sahifasida sana oraliq filteri ishlaydi
- [ ] Yalpi foyda = sotuv − tannarx
- [ ] Sof foyda = yalpi foyda − xarajat
- [ ] Pul oqimi (kirim/chiqim/saldo) to'g'ri
- [ ] Xarajatlar kategoriyalar bo'yicha to'g'ri taqsimlangan

---

## 12. Excel Export

Har bir tugma .xlsx fayl yuklab beradi va fayl Excel'da ochilishi kerak:

- [ ] Hisobot — "Excelga yuklash" ishlaydi
- [ ] Sotuv — Excel ishlaydi
- [ ] Prixod — Excel ishlaydi
- [ ] Ombor — Excel ishlaydi
- [ ] Qarzdorlar — Excel ishlaydi
- [ ] Bizning qarzlar — Excel ishlaydi
- [ ] Xarajatlar — Excel ishlaydi
- [ ] Excel fayllarda Uzbek sarlavhalar ko'rinadi
- [ ] Pul ustunlari to'g'ri formatda (1,234,567 ko'rinishida)
- [ ] JAMI qatori to'g'ri yig'indi ko'rsatadi

---

## 13. Umumiy

- [ ] Hech qaysi sahifada "card" to'lov turi yo'q (faqat Naqd / Perechisleniya)
- [ ] Login bo'lmaganda /login ga yo'naltiriladi
- [ ] Sidebar'da barcha modullar ochiladi
- [ ] Logout ishlaydi
- [ ] F5 (refresh) qilingach login holati saqlanib qoladi

---

**Test sanasi:** _______________
**Tester:** _______________
**Natija:** ☐ Hammasi ishlaydi  ☐ Xato bor (qaysi band: _______)