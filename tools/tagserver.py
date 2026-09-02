#!/usr/bin/env python3
"""Static server for index.html plus a tiny tag-recording API.

The page is otherwise dependency-free and works from the filesystem; running it
through this server is what turns the Tag column from a per-browser scratchpad
into shared, recorded state.

    python3 tools/tagserver.py --port 10045

Endpoints (same origin as the page, so no CORS is needed):

    GET  /api/tags              -> {"ok": true, "tags": {slug: [tag, ...]}, "vocab": [...]}
    POST /api/tags              <- {"slug": "sakana-ai", "tags": [...], "actor": "tjb"}
                               -> {"ok": true, "slug": ..., "tags": [...]}

State lives in two files under data/, both created on demand:

    data/tags.json       current tags per slug (the thing the page reads back)
    data/tags-log.jsonl  append-only record of every write, one JSON object per line
"""

import argparse
import json
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
STORE = os.path.join(DATA_DIR, "tags.json")
LOG = os.path.join(DATA_DIR, "tags-log.jsonl")

# Kept in sync with TAGS in index.html; the server is the one that says no.
VOCAB = ["Model", "Harness", "Infra", "Data/Eval", "Applications"]

MAX_BODY = 64 * 1024
_lock = threading.Lock()


def load_store():
    try:
        with open(STORE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_store(store):
    """Write through a temp file so a crash mid-write can't truncate the store."""
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, STORE)


def append_log(entry):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class Handler(SimpleHTTPRequestHandler):
    # Without an explicit charset the browser is free to guess, and on a CJK
    # locale it guesses GBK and renders the page as mojibake.
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".md": "text/markdown; charset=utf-8",
    }

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    # ---------- helpers ----------
    def send_json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None, "bad Content-Length"
        if length <= 0:
            return None, "empty body"
        if length > MAX_BODY:
            return None, "body too large"
        try:
            return json.loads(self.rfile.read(length).decode("utf-8")), None
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            return None, "invalid JSON: %s" % e

    # ---------- routes ----------
    def do_GET(self):
        if self.path.split("?")[0] == "/api/tags":
            with _lock:
                store = load_store()
            self.send_json(200, {"ok": True, "tags": store, "vocab": VOCAB})
            return
        super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/tags":
            self.send_error(404, "no such endpoint")
            return

        payload, err = self.read_json()
        if err:
            self.send_json(400, {"ok": False, "error": err})
            return

        slug = payload.get("slug")
        tags = payload.get("tags")
        if not isinstance(slug, str) or not slug.strip():
            self.send_json(400, {"ok": False, "error": "slug is required"})
            return
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            self.send_json(400, {"ok": False, "error": "tags must be a list of strings"})
            return

        unknown = [t for t in tags if t not in VOCAB]
        if unknown:
            self.send_json(400, {"ok": False, "error": "unknown tags: %s" % ", ".join(unknown)})
            return

        slug = slug.strip()[:120]
        # Dedupe and store in vocabulary order so the file reads the same way every time.
        tags = [t for t in VOCAB if t in tags]
        actor = payload.get("actor")
        actor = actor.strip()[:60] if isinstance(actor, str) and actor.strip() else "anon"

        with _lock:
            store = load_store()
            before = store.get(slug, [])
            if tags:
                store[slug] = tags
            else:
                store.pop(slug, None)
            save_store(store)
            append_log({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "slug": slug,
                "before": before,
                "after": tags,
                "actor": actor,
            })

        self.send_json(200, {"ok": True, "slug": slug, "tags": tags})


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=10045)
    ap.add_argument("--bind", default="0.0.0.0")
    args = ap.parse_args()

    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    print("serving %s on http://%s:%d/  (tags -> %s)" % (ROOT, args.bind, args.port, STORE))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
