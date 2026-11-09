# Natural Oil ERP на VDS 46.8.195.117

Сервер общий с **Evalon** и **Natural Print**. Их каталоги (`/opt/evalon`,
`/opt/naturalprint`), тома и общий Caddy на 80/443 **не трогаем**. HTTPS для
наших адресов даёт Caddy Evalon через внешнюю docker-сеть `edge`.

> **Не запускать на этом сервере `deploy/install.sh`** из корня репозитория.
> Тот скрипт рассчитан на чистую машину: ставит свой Caddy на 80/443,
> переписывает `/etc/caddy/Caddyfile` и включает ufw. Здесь это сломает
> Evalon и Natural Print. На этом сервере — только то, что описано ниже.

```
/opt/naturaloil/
  .env                 секреты, chmod 600, в git не кладётся (env.template)
  docker-compose.yml   копия infra/vds/docker-compose.yml
  deploy.sh            выкатка: git pull из repo.git, пересборка, перезапуск
  backup.sh            ночной бэкап (crontab 04:15)
  src/                 клон репозитория с GitHub, из него собираются образы
  backups/daily/       копии базы, 14 дней
```

## Состав

| Сервис | Что | Порт внутри | Данные |
|---|---|---|---|
| api | FastAPI + SQLite | 8010 | том `naturaloil_api-data` |
| web | nginx: панель + прокси `/api` | 80 | — |

Память: api 256M, web 64M — **320M** суммарно. Диска под образы и кэш
сборки — около 1 ГБ.

Адреса: временный `https://oil.46-8-195-117.sslip.io` работает сразу.
Боевой `naturaloilerp.uz` — раскомментировать блок в
`caddy/naturaloil.caddy`, когда в Cloudflare появится запись A на
46.8.195.117 (Proxied, SSL/TLS = Full).

---

## Первая установка

Всё выполняется **с рабочей машины через `ssh evalon-vds`** — на сервер
заходить не нужно, локальный клон репозитория тоже не нужен: сервер
скачивает код с GitHub сам (репозиторий публичный).

> Команды написаны для **cmd.exe**. В PowerShell 5.1 нет `&&` (разделять
> `;`), а `$(...)` он попытается раскрыть у себя — поэтому всё серверное
> держим внутри кавычек `ssh "..."`, тогда и `&&`, и `$(...)` разбирает
> уже bash на сервере.
>
> Только алиас `evalon-vds`. Прямой `root@46.8.195.117` отвечает
> Permission denied: вход не под root и ключ подставляется лишь для
> `Host evalon-vds` (в `~/.ssh/config` стоит `IdentitiesOnly`).

### 1. Место на диске

```bash
ssh evalon-vds "df -h / ; free -m ; docker system df"
```

Нужно свободно хотя бы 3 ГБ. Основной едок — кэш сборки Docker, общий на
все проекты сервера. Сколько из него можно освободить, показывает колонка
RECLAIMABLE строки Build Cache:

```bash
ssh evalon-vds "docker builder prune -f"
```

Чистка безопасна: удаляются только промежуточные слои прошлых сборок,
работающие контейнеры и образы не трогаются. Следующая сборка у соседей
просто пройдёт дольше.

### 2. Каталог на сервере

```bash
ssh evalon-vds "sudo install -d -o $(id -un) -g $(id -gn) /opt/naturaloil /opt/naturaloil/backups /opt/naturaloil/backups/daily"
```

### 3. Код, секреты, первая выкатка

```bash
ssh evalon-vds "git clone -b claude/elegant-cannon-2pfm1s https://github.com/Kirito7679/natural_oil.git /opt/naturaloil/src && cp /opt/naturaloil/src/infra/vds/deploy.sh /opt/naturaloil/src/infra/vds/backup.sh /opt/naturaloil/ && chmod +x /opt/naturaloil/deploy.sh /opt/naturaloil/backup.sh"
```

```bash
ssh evalon-vds "/opt/naturaloil/src/infra/vds/setup-env.sh"
```

Скрипт напечатает **логин и пароль входа** — сохранить, больше не покажет.

```bash
ssh evalon-vds "/opt/naturaloil/deploy.sh"
```

### 4. Ночной бэкап

```bash
ssh evalon-vds "crontab -l 2>/dev/null | grep -q naturaloil/backup.sh || (crontab -l 2>/dev/null; echo '15 4 * * * /opt/naturaloil/backup.sh >> /opt/naturaloil/backups/backup.log 2>&1') | crontab -"
```

Задание кладётся в crontab текущего пользователя, а не в `/etc/cron.d`:
там не нужна колонка с именем пользователя, и команду можно выполнить
повторно — второй строки не появится.

Время своё: 03:30 занято Evalon, 03:45 — Natural Print.

### 5. Проверка

```bash
ssh evalon-vds "curl -fsS -o /dev/null -w '%{http_code}\n' http://naturaloil-web-1/api/health"
```

Снаружи — открыть `https://oil.46-8-195-117.sslip.io` и войти.

---

## Обновление

Код ушёл в GitHub — на сервере одна команда:

```bash
ssh evalon-vds "/opt/naturaloil/deploy.sh"
```

`deploy.sh` делает `git pull` в `src/`, обновляет compose и маршруты
Caddy, пересобирает образы и перезапускает контейнеры.

Сервер тянет ту ветку, которую склонировали (`claude/elegant-cannon-2pfm1s`).
Если изменения ушли в другую ветку — `git -C src pull` скажет «Already up
to date», и выкатится старое. Переключить ветку:

```bash
ssh evalon-vds "git -C /opt/naturaloil/src fetch origin && git -C /opt/naturaloil/src checkout main"
```

## Диагностика

```bash
ssh evalon-vds "cd /opt/naturaloil && docker compose ps && docker compose logs --tail 50 api"
```

### 502 на всех `/api/*`, при этом сайт открывается

Было 09.11.2026. Признак: `api` — `Up (healthy)`, в его логе **только
`/api/health`** и ни одного реального запроса, а в логе `web`:

```
connect() failed (111: Connection refused) while connecting to upstream
```

Причина: `web` подключён и к нашей сети, и к общей `edge`, а встроенный DNS
Docker ищет имя во всех сетях контейнера. У соседей в `edge` есть свой
контейнер с именем **`api`**, и короткое имя уводило nginx к нему.

Поэтому к нашему backend обращаемся только по псевдониму **`naturaloil-api`**
(задан в `docker-compose.yml`, существует только в нашей сети). Короткие
имена вроде `api`, `db`, `web` в этой сети использовать нельзя.

Проверить, куда резолвится имя:

```bash
ssh evalon-vds "docker exec naturaloil-web-1 getent hosts naturaloil-api; docker exec naturaloil-api-1 hostname -i"
```

Оба адреса должны совпасть.

## Данные

База — SQLite на томе `naturaloil_api-data`, в git не кладётся
(`.dockerignore`, `.gitignore`). При первом старте на пустой базе `seed`
создаёт основного пользователя, категории расходов и счета (наличные,
перечисление). Товары не создаются — вводятся в тизиме.

Если нужно перенести базу с рабочей машины — это отдельная задача:
остановить `api`, положить файл на том, проверить `pragma integrity_check`,
поднять. Прежний файл **переименовывать, а не удалять**.
