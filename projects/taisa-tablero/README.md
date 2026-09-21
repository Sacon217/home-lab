# Taisa Board

Live board of the open issues in `Sacon217/taisa-issues`, served from the home lab.

The page reads the issues when it opens, every 60 seconds while it stays open, and whenever
**Refrescar** is pressed. Issues are split by app (API, web, Tiendita) and, inside each app,
into *Listo* and *Falta definir*, all derived from the tracker labels.

## How it works

- `GET /` serves `static/index.html`.
- `GET /api/issues` reads the open issues from the GitHub REST API (paginated, pull requests
  dropped), classifies each one by its labels and returns the board JSON. Responses are cached
  in memory for 30 seconds; `?fresh=true` skips the cache.
- `GET /health` returns `{"message": "Server is up"}`.

The GitHub token lives only on the server, in `.env`. The browser only talks to `/api/issues`
and never receives the token.

## Setup

1. Create a fine-grained token with **Issues: read-only** access to `Sacon217/taisa-issues` only.
2. `cp .env.example .env` and set `GITHUB_TOKEN`.
3. Check the real name of the Nginx Proxy Manager `edge` network with `docker network ls` and
   adjust `networks.edge.name` in `docker-compose.yml` if it is not `core-services_edge`.
4. `docker compose up -d --build`
5. In Nginx Proxy Manager, add a proxy host pointing to `taisa-tablero:8000`.

The image is also published by GitHub Actions as `ghcr.io/sacon217/taisa-tablero`.
