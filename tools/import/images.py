"""Download the original site's images and convert them to responsive WebP files.

Usage:
    python tools/import/images.py <images.json from collect_images.py> <download_cache_dir>

Writes processed files to static/img/ and the manifest to content/images.json:
    {"<image id>": {"w": .., "h": .., "sizes": {"<width>": "img/<file>"}, "orig": "<original url>"}}
Templates refer to images by id only; the manifest says which files exist.
"""
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "static" / "img"
MANIFEST = ROOT / "content" / "images.json"

PHOTO_WIDTHS = (720, 1600)  # card / inline size, lightbox / hero size
PLAN_WIDTHS = (1600,)  # floor plans: one sharp size is enough
UA = {"User-Agent": "Mozilla/5.0 (site migration)"}


def image_id(url: str) -> str:
    name = url.rsplit("/", 1)[-1]
    name = re.sub(r"(\.(webp|jpg|jpeg|png|avif|svg|ico))+$", "", name, flags=re.I)
    name = re.sub(r"-(\d+x\d+|scaled)$", "", name)
    return name


def is_plan(img_id: str) -> bool:
    return img_id.startswith("alaprajz-") or re.fullmatch(r"[ABC]\d{1,2}", img_id) is not None


def download(url: str, cache: Path) -> Path:
    dest = cache / url.rsplit("/", 1)[-1]
    if not dest.exists():
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
    return dest


def main():
    sources = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    cache = Path(sys.argv[2])
    cache.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for orig, best in sorted(sources.items()):
        img_id = image_id(orig)
        if img_id in manifest:
            continue
        raw = download(best, cache)
        ext = raw.suffix.lower()
        if ext in (".svg", ".ico"):
            target = OUT_DIR / f"{img_id}{ext}"
            shutil.copyfile(raw, target)
            manifest[img_id] = {"vector": True, "file": f"img/{target.name}", "orig": orig}
            continue
        if img_id == "favicon":
            shutil.copyfile(raw, OUT_DIR / "favicon.png")
        with Image.open(raw) as im:
            im.load()
            has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            im = im.convert("RGBA" if has_alpha else "RGB")
            w, h = im.size
            widths = PLAN_WIDTHS if is_plan(img_id) else PHOTO_WIDTHS
            quality = 90 if is_plan(img_id) else 80
            sizes = {}
            for tw in widths:
                tw = min(tw, w)
                if str(tw) in sizes:
                    continue
                th = round(h * tw / w)
                out = im if tw == w else im.resize((tw, th), Image.LANCZOS)
                name = f"{img_id}-{tw}.webp"
                out.save(OUT_DIR / name, "WEBP", quality=quality, method=6)
                sizes[str(tw)] = f"img/{name}"
            manifest[img_id] = {"w": w, "h": h, "sizes": sizes, "orig": orig}
        print(img_id, w, h, list(sizes))
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(manifest), "images in manifest")


if __name__ == "__main__":
    main()
