# Deploying Raven

One small Linux server runs everything: Caddy (HTTPS and the UI), the API, and Postgres.
Only ports 80 and 443 are open; the API and database are reachable only inside Docker.

## 1. Server

Any VPS with 2 GB RAM and 20 GB disk is enough (Hetzner, DigitalOcean, AWS Lightsail and similar).

```bash
# Ubuntu: install Docker and the compose plugin
curl -fsSL https://get.docker.com | sh
```

Point a DNS **A record** for your domain (e.g. `raven.example.org`) at the server's IP.
Caddy fetches the HTTPS certificate automatically once the domain resolves.

## 2. Code and source data

```bash
git clone https://github.com/kart747/Raven.git && cd Raven
git clone https://github.com/cvrajeesh/electoral-bond-data cvrajeesh_repo
git clone https://github.com/mkonchady/fcra fcra_repo

cp backend/.env.example backend/.env
```

Edit `backend/.env`:

- `GROQ_API_KEY`: optional, enables the weekly AI brief
- `ADMIN_API_KEY`: a long random string if you want the admin import endpoint, otherwise leave it empty

## 3. Start

```bash
export DOMAIN=raven.example.org
export POSTGRES_PASSWORD="$(openssl rand -hex 24)"   # keep this somewhere safe

docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm ingest     # first data load
```

The first load takes a while, mostly the rate-limited MyNeta pages; they are cached in
`backend/data_cache/`, so later runs are quick. Copying an existing `backend/data_cache/` to the
server first skips almost all of it.

Open `https://raven.example.org`.

## What is configured for you

| Concern | How |
|---|---|
| HTTPS | Caddy, automatic certificates, HTTP redirects to HTTPS |
| Same-origin API | Caddy proxies `/api`, `/docs` and `/openapi.json`, so no CORS setup is needed |
| Security headers | HSTS, `nosniff`, strict referrer policy; framing allowed so embeds work (no cookies or logins exist to protect) |
| Rate limiting | 120 API requests per minute per IP (`RATE_LIMIT_PER_MINUTE`) |
| Database | Postgres on a Docker volume, never exposed to the internet |
| Freshness | Lok Sabha activity re-imported weekly; AI brief regenerated weekly |
| Live headlines | The `live` service polls the feeds every few minutes (robots.txt honoured, conditional requests, back-off); the API streams new rows to browsers. Set `LIVE_RETENTION_DAYS` to change how long headlines are kept (default 60). |

## Updating

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Re-run a single dataset at any time, for example:

```bash
docker compose -f docker-compose.prod.yml run --rm ingest python -m app.cli ingest-questions
```

## Backups

```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U raven raven | gzip > raven-$(date +%F).sql.gz
```

Everything can also be rebuilt from source with `ingest-all`, so the database is replaceable;
`data/*.csv` (your sourced corrections and events) is the part worth backing up separately.

## Before going public

- Read the "Data quality and known gaps" section of the README; those caveats are shown in the UI.
- Make sure "Report an error" links to an issue tracker you watch.
- Raven names real people and organisations. Handle correction requests quickly and publicly.
