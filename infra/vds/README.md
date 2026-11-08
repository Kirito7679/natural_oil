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
  repo.git             голый репозиторий — сюда пушим с рабочей машины
  src/                 рабочая копия main, из неё собираются образы
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

Перед началом — запас на машине (диск был занят на ~85 %):

```bash
ssh evalon-vds "df -h / ; free -m ; docker system df"
```

Если свободно меньше 3 ГБ — сначала чистка или расширение диска, потом выкатка.

### 1. Каталог и голый репозиторий — на сервере

```bash
ssh evalon-vds "sudo mkdir -p /opt/naturaloil/backups/daily && sudo chown -R \$USER:\$USER /opt/naturaloil && git init --bare -b main /opt/naturaloil/repo.git"
```

### 2. Отправить код с рабочей машины

В PowerShell, в папке проекта. Коммит с инфраструктурой лежит на ветке
`claude/elegant-cannon-2pfm1s` на GitHub; `FETCH_HEAD` позволяет не
переключать ветку и не трогать рабочие файлы:

```bash
git remote add vds evalon-vds:/opt/naturaloil/repo.git
```

```bash
git fetch origin claude/elegant-cannon-2pfm1s; git push vds FETCH_HEAD:refs/heads/main
```

> Remote только через алиас `evalon-vds`. Прямой адрес
> `ubuntu@46.8.195.117:...` падает с Permission denied: в `~/.ssh/config`
> стоит `IdentitiesOnly` и ключ не подставляется.

### 3. Рабочая копия, секреты, первая выкатка — на сервере

```bash
ssh evalon-vds "git clone /opt/naturaloil/repo.git /opt/naturaloil/src && cp /opt/naturaloil/src/infra/vds/deploy.sh /opt/naturaloil/src/infra/vds/backup.sh /opt/naturaloil/ && chmod +x /opt/naturaloil/deploy.sh /opt/naturaloil/backup.sh"
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
ssh evalon-vds "echo '15 4 * * * ubuntu /opt/naturaloil/backup.sh >> /opt/naturaloil/backups/backup.log 2>&1' | sudo tee /etc/cron.d/naturaloil"
```

Время своё: 03:30 занято Evalon, 03:45 — Natural Print.

### 5. Проверка

```bash
ssh evalon-vds "curl -fsS -o /dev/null -w '%{http_code}\n' http://naturaloil-web-1/api/health"
```

Снаружи — открыть `https://oil.46-8-195-117.sslip.io` и войти.

---

## Обновление

```bash
git push origin main; git push vds main; ssh evalon-vds "/opt/naturaloil/deploy.sh"
```

В PowerShell 5.1 **не работает `&&`** — разделять `;`. Всё, что должно
выполниться на сервере, класть внутрь кавычек `ssh "..."`, тогда `&&`
разбирает уже bash.

Сервер тянет код из `repo.git`, **не из GitHub**. Забыли `git push vds` —
`git -C src pull` скажет «Already up to date», и выкатится старое.

## Диагностика

```bash
ssh evalon-vds "cd /opt/naturaloil && docker compose ps && docker compose logs --tail 50 api"
```

## Данные

База — SQLite на томе `naturaloil_api-data`, в git не кладётся
(`.dockerignore`, `.gitignore`). При первом старте на пустой базе `seed`
создаёт основного пользователя, категории расходов и счета (наличные,
перечисление). Товары не создаются — вводятся в тизиме.

Если нужно перенести базу с рабочей машины — это отдельная задача:
остановить `api`, положить файл на том, проверить `pragma integrity_check`,
поднять. Прежний файл **переименовывать, а не удалять**.
