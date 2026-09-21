# Issues Board

Live board of the open issues in a GitHub repository, served from the home lab.

The page reads the issues when it opens, every 60 seconds while it stays open, and whenever
**Refrescar** is pressed. Issues are grouped into one column per app and, inside each column,
split by readiness. Everything is derived from the issue labels.

## How it works

- `GET /` serves `static/index.html`.
- `GET /api/issues` reads the open issues from the GitHub REST API (paginated, pull requests
  dropped), classifies each one by its labels and returns the board JSON. Responses are cached
  in memory for 30 seconds; `?fresh=true` skips the cache.
- `GET /health` returns `{"message": "Server is up"}`.

The token and the board settings live only on the server. The browser only talks to
`/api/issues` and never receives the token.

## Configuration

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | Fine-grained token with **Issues: read-only** access to the tracked repository only |
| `GITHUB_REPO` | Tracked repository, as `owner/name` |
| `BOARD_TITLE` | Page title |
| `BOARD_APPS` | JSON list of columns: `[{"key": "backend", "name": "Backend", "desc": "Optional"}]`. An issue lands in a column when it has the label `app:<key>`; issues without any are skipped |
| `BOARD_ASSIGNEES` | JSON list mapping labels to who picks the issue up: `[{"label": "owner:bot", "name": "bot", "agent": true}]` |
| `BOARD_DEFAULT_ASSIGNEE` | Name shown when no assignee label matches |

Labels read from each issue:

- `listo` marks it ready; otherwise it goes under *Falta definir*.
- Type: the first of `bug`, `deuda`, `decision`, `tarea`, `indice`.
- Priority: the first of `prio:critico`, `prio:alto`, `prio:medio`, `prio:bajo` (default `medio`).
- Any label starting with `GO-` is shown as a tag.

## Setup

The image is built by GitHub Actions on every push to `main` that touches this folder and
published as `ghcr.io/sacon217/issues-board:latest` and `:<sha>`.

1. In Portainer, create a stack on the target node with the contents of `docker-compose.yml`
   (drop the `build:` block) and set the variables above as stack environment variables.
2. In Nginx Proxy Manager, add a proxy host pointing to `<node IP>:8010`.

To run it locally instead: `cp .env.example .env`, fill it in, then `docker compose up -d --build`.
