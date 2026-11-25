"""Download every page listed in the original site's sitemap.

Usage: python tools/import/crawl.py <out_dir>
Files are named after the URL path: home.html, elado-lakasok.html, elado-lakasok_c1.html, ...

Note: the building-picker popups are loaded by AJAX on the original site and are not in these
pages; their data (picker_raw.json: floor plans + SVG zones per building) was captured from the
live popups in a browser.
"""
import re
import sys
import urllib.request
from pathlib import Path

SITE = "https://csillagfenylakopark.hu/"
UA = {"User-Agent": "Mozilla/5.0 (site migration)"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    urls = re.findall(r"<loc>([^<]+)</loc>", get(SITE + "sitemap.xml").decode("utf-8"))
    urls.append(SITE + "elado-lakasok/")
    for url in urls:
        name = url[len(SITE):].strip("/").replace("/", "_") or "home"
        (out / f"{name}.html").write_bytes(get(url))
        print(name)


if __name__ == "__main__":
    main()
