#!/bin/bash
# Ночной бэкап Natural Oil: копия SQLite-базы через sqlite backup API
# (безопасно на живой базе, в отличие от простого cp при включённом WAL).
# Хранится 14 дней в /opt/naturaloil/backups/daily.
#
# crontab: 15 4 * * *  /opt/naturaloil/backup.sh >> /opt/naturaloil/backups/backup.log 2>&1
# Время специально своё: 03:30 занято Evalon, 03:45 — Natural Print.
set -euo pipefail
cd "$(dirname "$0")"
DIR=backups/daily
TS=$(date +%Y%m%d-%H%M)
mkdir -p "$DIR"

if ! docker compose ps --services --status running | grep -qx api; then
  echo "$(date -Iseconds) error контейнер api не запущен — база не скопирована"
  exit 1
fi

docker compose exec -T api python -c "
import sqlite3,sys
src=sqlite3.connect('/app/data/natural_oil.db'); dst=sqlite3.connect('/tmp/copy.db')
src.backup(dst); dst.close()
sys.stdout.buffer.write(open('/tmp/copy.db','rb').read())" > "$DIR/natural_oil-$TS.db"

# пустая или битая копия хуже, чем никакой
docker compose exec -T api python -c "
import sqlite3; c=sqlite3.connect('/app/data/natural_oil.db'); c.execute('pragma quick_check').fetchone()" > /dev/null

find "$DIR" -type f -mtime +14 -delete
echo "$(date -Iseconds) ok natural_oil=$(du -h "$DIR/natural_oil-$TS.db" | cut -f1)"
