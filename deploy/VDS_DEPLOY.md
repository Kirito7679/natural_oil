# Natural Oil ERP — VDS serverga yuklash

> ⚠️ **Faqat bo'sh server uchun.** Bu yo'riqnoma va `deploy/install.sh`
> serverda boshqa hech narsa ishlamayotganini kutadi: o'zining Caddy'sini
> 80/443 portlariga qo'yadi, `/etc/caddy/Caddyfile` ni qayta yozadi va ufw
> yoqadi.
>
> **46.8.195.117 serveri uchun buni ISHLATMANG** — u yerda Evalon va
> Natural Print ishlayapti, ular ham o'sha portlarda. O'sha server uchun
> alohida yo'riqnoma bor: [`infra/vds/README.md`](../infra/vds/README.md)
> (Docker + umumiy Caddy orqali, qo'shnilarga tegmaydi).

Server talabi: **Ubuntu 24.04**, root huquqi. O'rnatuvchi (`deploy/install.sh`)
Caddy + HTTPS, systemd xizmati, ufw va kunlik backup'ni o'zi sozlaydi.

Ma'lumotlar `/var/lib/nop` da turadi — **qayta o'rnatganda o'chmaydi**.

---

## Yo'l 1 — Windows kompyuterdan (eng oson)

Loyiha papkasida `SERVERGA_YUBORISH.bat` faylini ikki marta bosing va
server IP manzilini kiriting. Skript o'zi:

1. fayllarni arxivlaydi,
2. `scp` orqali serverga yuboradi,
3. `install.sh` ni ishga tushiradi.

Server paroli ikki marta so'raladi. 3–7 daqiqa kutiladi.

---

## Yo'l 2 — serverning o'zida (GitHub orqali)

Evalon panelidagi konsolga yoki SSH orqali **root** bo'lib kiring va
quyidagini bajaring.

```bash
apt-get update -qq && apt-get install -y -qq git
```

```bash
rm -rf /opt/nop/src && mkdir -p /opt/nop && git clone --depth 1 -b claude/elegant-cannon-2pfm1s https://github.com/Kirito7679/natural_oil.git /opt/nop/src
```

> Repozitoriy **private** bo'lsa, `https://github.com/` o'rniga
> `https://<GITHUB_TOKEN>@github.com/` yozing (token: GitHub → Settings →
> Developer settings → Personal access tokens, `repo` huquqi bilan).

```bash
bash /opt/nop/src/deploy/install.sh
```

---

## Domen ulash

IP bo'yicha ishlatish uchun hech narsa kerak emas — o'rnatuvchi
`<IP>.sslip.io` manzilini va unga HTTPS sertifikatini o'zi oladi.

O'z domeningiz bo'lsa, avval domenning **A yozuvini** server IP'siga
yo'naltiring, so'ng:

```bash
NOP_DOMAIN=naturaloilerp.uz bash /opt/nop/src/deploy/install.sh
```

---

## O'rnatgandan keyin

O'rnatuvchi oxirida manzil va **birinchi parolni** chiqaradi:

```
TAYYOR: https://<domen>
Login: 95 810 06 00
Parol: <tasodifiy parol>
```

Bu parol **boshqa ko'rsatilmaydi** — saqlab oling. Kirgandan keyin tizimda
"Менинг паролим" orqali o'zgartiring.

Foydali buyruqlar:

```bash
systemctl status nop
```

```bash
journalctl -u nop -n 50 --no-pager
```

---

## Yangilash

Kodni yangilaganda o'sha buyruqni qayta ishga tushiring — ma'lumotlar
bazasi va `/etc/nop.env` dagi sozlamalar saqlanib qoladi:

```bash
cd /opt/nop/src && git pull && bash deploy/install.sh
```
