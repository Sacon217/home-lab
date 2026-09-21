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

REPO = "Sacon217/taisa-issues"
ISSUES_URL = f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=100"
CACHE_SECONDS = 30
APPS = ["api", "web", "tiendita"]
PRIOS = ["critico", "alto", "medio", "bajo"]
TIPOS = ["bug", "deuda", "decision", "tarea", "indice"]
STATIC = Path(__file__).parent / "static"

cache = {"at": 0.0, "data": None}
lock = threading.Lock()

app = FastAPI()


def next_page(link_header):
    for part in (link_header or "").split(","):
        match = re.search(r'<([^>]+)>;\s*rel="next"', part)
        if match:
            return match.group(1)
    return None


def fetch_open_issues():
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "taisa-tablero",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    items = []
    url = ISSUES_URL
    while url:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=15) as response:
            items.extend(json.load(response))
            url = next_page(response.headers.get("Link"))

    return [item for item in items if "pull_request" not in item]


def classify(issue):
    labels = {label["name"] for label in issue["labels"]}
    apps = [a for a in APPS if f"app:{a}" in labels]
    if not apps:
        return None

    return {
        "n": issue["number"],
        "t": issue["title"],
        "url": issue["html_url"],
        "apps": apps,
        "tipo": next((t for t in TIPOS if t in labels), "otro"),
        "liston": "listo" if "listo" in labels else "falta",
        "quien": ("agente" if "hace:agente" in labels
                  else "gabriel" if "handoff:gabriel" in labels else "sergio"),
        "prio": next((p for p in PRIOS if f"prio:{p}" in labels), "medio"),
        "go": next((l for l in sorted(labels) if l.startswith("GO-")), ""),
    }


def build_board():
    read_at = datetime.datetime.now(datetime.timezone.utc)
    issues = [c for c in map(classify, fetch_open_issues()) if c]
    issues.sort(key=lambda x: (PRIOS.index(x["prio"]), -x["n"]))

    return {
        "meta": {
            "total": len(issues),
            "actualizado": read_at.isoformat(timespec="seconds").replace("+00:00", "Z"),
            "repo": REPO,
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
            data = build_board()
        except urllib.error.HTTPError as e:
            logger.error(f"GitHub answered {e.code}: {e.reason}")
            return JSONResponse(status_code=502, content={"message": f"GitHub answered {e.code}"})
        except Exception as e:
            logger.error(f"Error reading GitHub: {e}")
            return JSONResponse(status_code=502, content={"message": "Could not reach GitHub"})

        cache["at"] = time.monotonic()
        cache["data"] = data

    return JSONResponse(data, headers={"Cache-Control": "no-store"})
