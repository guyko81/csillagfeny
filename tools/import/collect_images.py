"""Collect every image the original site uses, choosing the largest source per image.

Usage: python -P -E collect_images.py <pages_dir> <building_picker_json> <out_json>
Writes {"<original src url>": "<best source url>"} so templates can map original -> local.
"""
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
pages = Path(sys.argv[1])
picker = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
out = Path(sys.argv[3])

UP = "https://csillagfenylakopark.hu/wp-content/uploads/"
MAX_W = 2048
best = {}  # original src -> best url


def best_from_srcset(img):
    cands = []
    for part in (img.get("srcset") or "").split(","):
        bits = part.strip().split()
        if len(bits) == 2 and bits[1].endswith("w"):
            cands.append((int(bits[1][:-1]), bits[0]))
    cands = [c for c in cands if c[0] <= MAX_W] or cands
    if cands:
        return max(cands)[1]
    return img.get("src")


for f in sorted(pages.glob("*.html")):
    html = f.read_text(encoding="utf-8")
    s = BeautifulSoup(html, "html.parser")
    for img in s.find_all("img"):
        src = img.get("src") or ""
        if not src.startswith(UP):
            continue
        best.setdefault(src, best_from_srcset(img))
    for m in re.finditer(r"url\(['\"]?((?:https://csillagfenylakopark\.hu)?/wp-content/uploads/[^'\")]+\.(?:webp|jpg|jpeg|png|svg|avif))['\"]?\)", html):
        u = m.group(1)
        if u.startswith("/"):
            u = "https://csillagfenylakopark.hu" + u
        best.setdefault(u, u)
    for m in re.finditer(r'href="(https://csillagfenylakopark\.hu/wp-content/uploads/[^"]+\.(?:png|svg|ico|webp))"', html):
        best.setdefault(m.group(1), m.group(1))

for b in picker["buildings"]:
    for lv in b["levels"]:
        best.setdefault(lv["img"], lv["img"])

out.write_text(json.dumps(best, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(best), "images;", len(set(best.values())), "unique sources")
