from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import datetime
import json
import logging
import os
import re
import threading
import time
import urllib.error
import urllib.request

logger = logging.getLogger("fastapi")

CACHE_SECONDS = 30
PRIOS = ["critico", "alto", "medio", "bajo"]
TIPOS = ["bug", "deuda", "decision", "tarea", "indice"]
STATIC = Path(__file__).parent / "static"

cache = {"at": 0.0, "data": None}
lock = threading.Lock()

app = FastAPI()


def env_json(name, default):
    raw = os.environ.get(name, "").strip()
    return json.loads(raw) if raw else default


def load_settings():
    return {
        "repo": os.environ.get("GITHUB_REPO", "").strip(),
        "title": os.environ.get("BOARD_TITLE", "").strip() or "Issues board",
        "apps": env_json("BOARD_APPS", []),
        "assignees": env_json("BOARD_ASSIGNEES", []),
        "default_assignee": os.environ.get("BOARD_DEFAULT_ASSIGNEE", "").strip(),
    }


def next_page(link_header):
    for part in (link_header or "").split(","):
        match = re.search(r'<([^>]+)>;\s*rel="next"', part)
        if match:
            return match.group(1)
    return None


def fetch_open_issues(repo):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "issues-board",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    items = []
    url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=100"
    while url:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=15) as response:
            items.extend(json.load(response))
            url = next_page(response.headers.get("Link"))

    return [item for item in items if "pull_request" not in item]


def classify(issue, settings):
    labels = {label["name"] for label in issue["labels"]}
    apps = [a["key"] for a in settings["apps"] if f"app:{a['key']}" in labels]
    if not apps:
        return None

    assignee = next((a for a in settings["assignees"] if a["label"] in labels), None)

    return {
        "n": issue["number"],
        "t": issue["title"],
        "url": issue["html_url"],
        "apps": apps,
        "tipo": next((t for t in TIPOS if t in labels), "otro"),
        "liston": "listo" if "listo" in labels else "falta",
        "quien": assignee["name"] if assignee else settings["default_assignee"],
        "agente": bool(assignee and assignee.get("agent")),
        "prio": next((p for p in PRIOS if f"prio:{p}" in labels), "medio"),
        "go": next((l for l in sorted(labels) if l.startswith("GO-")), ""),
    }


def build_board(settings):
    read_at = datetime.datetime.now(datetime.timezone.utc)
    issues = [c for c in (classify(i, settings) for i in fetch_open_issues(settings["repo"])) if c]
    issues.sort(key=lambda x: (PRIOS.index(x["prio"]), -x["n"]))

    return {
        "meta": {
            "total": len(issues),
            "actualizado": read_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "repo": settings["repo"],
            "titulo": settings["title"],
            "apps": settings["apps"],
        },
        "issues": issues,
    }


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/health", status_code=200)
def health():
    return {"message": "Server is up"}


@app.get("/api/issues")
def issues(fresh: bool = False):
    with lock:
        if not fresh and cache["data"] and time.monotonic() - cache["at"] < CACHE_SECONDS:
            return JSONResponse(cache["data"], headers={"Cache-Control": "no-store"})

        try:
            settings = load_settings()
            if not settings["repo"] or not settings["apps"]:
                return JSONResponse(status_code=500, content={"message": "GITHUB_REPO and BOARD_APPS must be set"})
            data = build_board(settings)
        except urllib.error.HTTPError as e:
            logger.error(f"GitHub answered {e.code}: {e.reason}")
            return JSONResponse(status_code=502, content={"message": f"GitHub answered {e.code}"})
        except json.JSONDecodeError as e:
            logger.error(f"Invalid board settings: {e}")
            return JSONResponse(status_code=500, content={"message": "Invalid BOARD_APPS or BOARD_ASSIGNEES"})
        except Exception as e:
            logger.error(f"Error reading GitHub: {e}")
            return JSONResponse(status_code=502, content={"message": "Could not reach GitHub"})

        cache["at"] = time.monotonic()
        cache["data"] = data

    return JSONResponse(data, headers={"Cache-Control": "no-store"})
