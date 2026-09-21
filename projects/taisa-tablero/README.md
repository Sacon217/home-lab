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

The GitHub token lives only on the server (Portainer stack variable or `.env`). The browser only talks to `/api/issues`
and never receives the token.

## Setup

The image is built by GitHub Actions on every push to `main` that touches this folder and
published as `ghcr.io/sacon217/taisa-tablero:latest` and `:<sha>`.

1. Create a fine-grained token with **Issues: read-only** access to `Sacon217/taisa-issues` only.
2. In Portainer, create a stack on the target node with the contents of `docker-compose.yml`
   (drop the `build:` block) and set `GITHUB_TOKEN` as a stack environment variable.
3. In Nginx Proxy Manager, add a proxy host pointing to `<node IP>:8010`.

To run it locally instead: `cp .env.example .env`, set `GITHUB_TOKEN`, then
`docker compose up -d --build`.
