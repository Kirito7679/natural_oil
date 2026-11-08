#!/bin/bash
# Заполняет /opt/naturaloil/.env перед первой выкаткой. Ключи генерирует сам,
# придумывать и присылать в чат ничего не нужно.
#
# Запускать на сервере:
#   /opt/naturaloil/src/infra/vds/setup-env.sh
#
# Уже заполненные значения НЕ меняет — повторный запуск безопасен.
# Прежний .env сохраняется рядом как .env.bak-<дата>.
set -euo pipefail

ENV_FILE=${1:-/opt/naturaloil/.env}
[ -f "$ENV_FILE" ] || { umask 077; : > "$ENV_FILE"; echo "создан $ENV_FILE"; }
BAK="$ENV_FILE.bak-$(date +%Y%m%d-%H%M)"
[ -f "$BAK" ] || cp "$ENV_FILE" "$BAK"

hex() { openssl rand -hex 32; }
# без конвейера: head в конвейере закрывает его и под `set -o pipefail`
# роняет скрипт (SIGPIPE, код 141) — грабли Natural Print
pass() { openssl rand -hex 6; }

declared() { grep -qE "^$1=" "$ENV_FILE"; }
filled()   { grep -qE "^$1=.+" "$ENV_FILE"; }

# имя значение комментарий
set_var() {
	if filled "$1"; then echo "  $1 — уже задан, не меняю"; return; fi
	if declared "$1"; then
		sed -i "s|^$1=.*|$1=$2|" "$ENV_FILE"
	else
		printf '%s\n%s=%s\n' "# $3" "$1" "$2" >> "$ENV_FILE"
	fi
	echo "  $1 — задан"
}

echo "Переменные Natural Oil в $ENV_FILE:"
declared NOP_SECRET_KEY || printf '# ─── Natural Oil ERP ───\n' >> "$ENV_FILE"

set_var NOP_SECRET_KEY     "$(hex)"        "подпись JWT"
set_var NOP_FRONTEND_URL   "https://oil.46-8-195-117.sslip.io" "публичный адрес; сменить на домен, когда появится"
set_var NOP_MAIN_USER_NAME "Хумоюн"        "основной пользователь (раҳбар)"
set_var NOP_MAIN_USER_LOGIN "95 810 06 00" "его логин"

# Пароль основного пользователя применяется ТОЛЬКО при первом старте на
# пустой базе. Если база уже с данными — seed пользователя не трогает.
PASS_NEW=""
if declared NOP_MAIN_USER_PASSWORD; then
	echo "  NOP_MAIN_USER_PASSWORD — уже объявлен, не меняю"
else
	PASS_NEW=$(pass)
	printf '%s\n%s=%s\n' "# пароль основного пользователя при первом старте на пустой базе" \
		"NOP_MAIN_USER_PASSWORD" "$PASS_NEW" >> "$ENV_FILE"
	echo "  NOP_MAIN_USER_PASSWORD — задан"
fi

chmod 600 "$ENV_FILE"

echo
echo "────────────────────────────────────────────────────────────"
if [ -n "$PASS_NEW" ]; then
	echo "  Вход в Natural Oil ERP"
	echo
	echo "      логин:  95 810 06 00"
	echo "      пароль: $PASS_NEW"
	echo
	echo "  Пароль действует при первом старте на пустой базе."
	echo "  Сохраните его и смените в тизиме: «Менинг паролим»."
else
	echo "  Пароль уже был в .env — смотрите NOP_MAIN_USER_PASSWORD."
fi
echo "────────────────────────────────────────────────────────────"
echo
echo "Дальше:  /opt/naturaloil/deploy.sh"
