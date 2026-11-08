#!/usr/bin/env bash
# Natural Oil ERP: Ubuntu 24.04 serverga o'rnatish va yangilash. Qayta ishga tushirsa bo'ladi.
# Ma'lumotlar /var/lib/nop da turadi, yangilashda o'chmaydi.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

SRC=/opt/nop/src
VENV=/opt/nop/venv
DATA=/var/lib/nop
BACKUPS=/var/backups/nop
WEB=/var/www/nop
ENV_FILE=/etc/nop.env
DOMAIN_FILE=/etc/nop.domain
FIRST_PASSWORD=""

[ "$(id -u)" -eq 0 ] || { echo "root sifatida ishga tushiring"; exit 1; }

echo "[1/8] Server vaqti: Toshkent"
timedatectl set-timezone Asia/Tashkent

echo "[2/8] Swap"
if [ "$(swapon --noheadings | wc -l)" -eq 0 ] && [ ! -e /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile >/dev/null
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "[3/8] Dasturlar"
apt-get update -qq
apt-get install -y -qq python3-venv sqlite3 curl openssl ufw caddy cron >/dev/null
node_major=$(node -v 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/' || true)
if [ -z "$node_major" ] || [ "$node_major" -lt 22 ]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/dev/null
  apt-get install -y -qq nodejs >/dev/null
fi

echo "[4/8] Sozlamalar"
id nop >/dev/null 2>&1 || useradd --system --home-dir "$DATA" --shell /usr/sbin/nologin nop
mkdir -p "$DATA" "$BACKUPS" "$WEB"
chown nop:nop "$DATA"
chmod 750 "$DATA"
if [ ! -f "$DOMAIN_FILE" ]; then
  ip=$(curl -4 -fsS https://api.ipify.org || hostname -I | awk '{print $1}')
  echo "${NOP_DOMAIN:-$ip.sslip.io}" > "$DOMAIN_FILE"
fi
[ -z "${NOP_DOMAIN:-}" ] || echo "$NOP_DOMAIN" > "$DOMAIN_FILE"
DOMAIN=$(cat "$DOMAIN_FILE")
if [ ! -f "$ENV_FILE" ]; then
  FIRST_PASSWORD=$(openssl rand -hex 6)
  umask 077
  cat > "$ENV_FILE" <<ENV
DATABASE_URL=sqlite:///$DATA/natural_oil.db
SECRET_KEY=$(openssl rand -hex 32)
MAIN_USER_PASSWORD=$FIRST_PASSWORD
FRONTEND_URL=https://$DOMAIN
ENV
  umask 022
fi
sed -i "s#^FRONTEND_URL=.*#FRONTEND_URL=https://$DOMAIN#" "$ENV_FILE"
chown root:nop "$ENV_FILE"
chmod 640 "$ENV_FILE"

echo "[5/8] Backend"
[ -d "$VENV" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$SRC/backend/requirements.txt"
cat > /etc/systemd/system/nop.service <<UNIT
[Unit]
Description=Natural Oil ERP
After=network.target

[Service]
User=nop
Group=nop
WorkingDirectory=$SRC/backend
EnvironmentFile=$ENV_FILE
ExecStart=$VENV/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010 --workers 1 --proxy-headers
Restart=always
RestartSec=3
NoNewPrivileges=true
ProtectSystem=full
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable nop >/dev/null 2>&1
systemctl restart nop

echo "[6/8] Frontend"
cd "$SRC/frontend"
unset VITE_API_URL
npm ci --no-audit --no-fund || { rm -f package-lock.json; npm install --no-audit --no-fund; }
npm run build
rm -rf "${WEB:?}"/*
cp -r dist/. "$WEB/"
rm -rf node_modules

echo "[7/8] Veb-server va himoya"
cat > /etc/caddy/Caddyfile <<CADDY
$DOMAIN {
    encode gzip
    handle /api/* {
        reverse_proxy 127.0.0.1:8010
    }
    handle {
        root * $WEB
        try_files {path} /index.html
        file_server
    }
}
CADDY
systemctl enable caddy >/dev/null 2>&1
systemctl restart caddy
ufw allow OpenSSH >/dev/null
ufw allow 80/tcp >/dev/null
ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null

echo "[8/8] Kunlik zaxira nusxa"
cat > /etc/cron.d/nop-backup <<CRON
0 3 * * * root sqlite3 $DATA/natural_oil.db ".backup '$BACKUPS/nop-\$(date +\%F).db'" && find $BACKUPS -name 'nop-*.db' -mtime +14 -delete
CRON

for _ in $(seq 1 20); do
  curl -fsS http://127.0.0.1:8010/api/health >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS http://127.0.0.1:8010/api/health >/dev/null || {
  echo "XATO: backend ishga tushmadi"
  journalctl -u nop -n 30 --no-pager
  exit 1
}

echo
echo "=================================================="
echo " TAYYOR: https://$DOMAIN"
if [ -n "$FIRST_PASSWORD" ]; then
  echo " Login: 95 810 06 00"
  echo " Parol: $FIRST_PASSWORD"
  echo " Bu parol boshqa ko'rsatilmaydi, saqlab oling!"
fi
echo "=================================================="
