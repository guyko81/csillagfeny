"""Serve dist/ the way GitHub Pages will: under the site's base path, with 404.html for misses.

Usage: python tools/serve.py [port]   ->  http://localhost:<port>/csillagfeny/
Caching is disabled so a rebuild is visible on the next reload.
"""
import functools
import http.server
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
BASE = urlsplit(json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))["site_url"]).path


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        path = urlsplit(self.path).path
        if path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", BASE)
            self.end_headers()
            return None
        if not path.startswith(BASE.rstrip("/")):
            return self._not_found()
        self.path = "/" + self.path[len(BASE):] if self.path.startswith(BASE) else "/"
        fs = Path(self.translate_path(self.path))
        if not fs.exists():
            return self._not_found()
        return super().send_head()

    def _not_found(self):
        body = (DIST / "404.html").read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return None


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    handler = functools.partial(Handler, directory=str(DIST))
    print(f"http://localhost:{port}{BASE}")
    http.server.ThreadingHTTPServer(("", port), handler).serve_forever()


if __name__ == "__main__":
    main()
