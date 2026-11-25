"""Fail if any local href/src/srcset in the built site points to a file that does not exist.

Usage: python tools/check_links.py [dist_dir]
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

SKIP = re.compile(r"^(https?:|mailto:|tel:|#|data:)")


def main():
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "dist")
    broken, checked = [], 0
    for page in sorted(dist.rglob("*.html")):
        html = page.read_text(encoding="utf-8")
        html = re.sub(r"<base [^>]*>", "", html)
        # 404.html is served at arbitrary paths and resolves links against <base href> = site root
        base = "/" if page.name == "404.html" else "/" + page.relative_to(dist).as_posix()
        urls = re.findall(r'(?:href|src|data-full)="([^"]+)"', html)
        for srcset in re.findall(r'srcset="([^"]+)"', html):
            urls += [part.strip().split()[0] for part in srcset.split(",")]
        for u in urls:
            if SKIP.match(u):
                continue
            checked += 1
            path = unquote(urlsplit(urljoin(base, u.replace("&amp;", "&"))).path)
            target = dist / path.lstrip("/")
            if path.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                broken.append(f"{page.relative_to(dist)}: {u}")
    print(f"{checked} local references checked, {len(broken)} broken")
    for b in broken:
        print("  ", b)
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
