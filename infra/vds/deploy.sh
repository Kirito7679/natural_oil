#!/bin/bash
# Выкатка на VDS: подтянуть код из /opt/naturaloil/repo.git (туда пушим с
# машины: git push vds main), пересобрать образы, перезапустить.
# Запускать на сервере: /opt/naturaloil/deploy.sh   (первый раз — см. README.md)
set -euo pipefail
cd "$(dirname "$0")"

git -C src pull --ff-only
cp src/infra/vds/docker-compose.yml src/infra/vds/deploy.sh src/infra/vds/backup.sh .
chmod +x deploy.sh backup.sh

# маршруты общего Caddy: применяем только если файл изменился
if ! cmp -s src/infra/vds/caddy/naturaloil.caddy /opt/evalon/caddy-sites/naturaloil.caddy; then
  cp src/infra/vds/caddy/naturaloil.caddy /opt/evalon/caddy-sites/naturaloil.caddy
  /opt/evalon/caddy-apply.sh
fi

docker compose up -d --build --remove-orphans
docker image prune -f > /dev/null
docker compose ps --format '{{.Service}} {{.Status}}'
