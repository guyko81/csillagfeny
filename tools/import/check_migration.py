"""Check that every piece of visible text of the original site is present on the new site.

Usage:
    python tools/import/check_migration.py <original_pages_dir> <dist_dir> [picker_raw.json]

For each original page, every text node of <main> and <footer> is looked up in the text of
the matching new page. Comparison ignores whitespace and thousands separators, because the
new site formats numbers as "53 713 000 Ft" where the original printed "53713000" or
"53,713,000". Prints a table (page, text nodes, found, missing) and the missing strings.
"""
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Comment

sys.path.insert(0, str(Path(__file__).resolve().parent))
from images import image_id  # noqa: E402  (same id rule as the importer)

sys.stdout.reconfigure(encoding="utf-8")

# Text that only existed as JS placeholders / widget chrome on the original
IGNORED = {"?", "0", "Ft", "Min", "Max", "37", "72", "Szűrő - Jelölőnégyzet", "imunify-bot-check", "Új lapon nyílik meg"}


def norm(s: str) -> str:
    s = s.replace("⁨", "").replace("⁩", "")
    s = re.sub(r"(?<=\d)[ ,.  ](?=\d{3}\b)", "", s)  # thousands separators
    return re.sub(r"\s+", "", s)


def texts(html: str, scopes=("main", "footer")):
    s = BeautifulSoup(html, "html.parser")
    for t in s(["script", "style", "noscript", "svg", "template"]):
        t.decompose()
    for c in s.find_all(string=lambda x: isinstance(x, Comment)):
        c.extract()
    out = []
    for scope in scopes:
        for root in s.find_all(scope):
            for node in root.find_all(string=True):
                t = re.sub(r"\s+", " ", node).strip()
                if t and t not in IGNORED:
                    out.append(t)
    return out


def page_text(html: str) -> str:
    s = BeautifulSoup(html, "html.parser")
    # accessible names count as content (e.g. the floor-plan zones are links with aria-labels)
    attrs = " ".join(v for el in s.find_all(True) for k, v in el.attrs.items() if k in ("alt", "aria-label", "title", "data-caption", "data-tip") and isinstance(v, str))
    for t in s(["script", "style", "noscript", "svg"]):
        t.decompose()
    return norm(s.get_text(" ") + " " + attrs)


def needle(t: str) -> str:
    """The original listing cut excerpts with '...'; the new list shows the full text (CSS clamps it)."""
    return norm(re.sub(r"(\.\.\.|…)$", "", t))


def main():
    orig = Path(sys.argv[1])
    dist = Path(sys.argv[2])
    pairs = [("home.html", "index.html"), ("elado-lakasok.html", "elado-lakasok/index.html"),
             ("adatkezelesi-tajekoztato.html", "adatkezelesi-tajekoztato/index.html")]
    for f in sorted(orig.glob("elado-lakasok_*.html")):
        apt = f.stem.split("_", 1)[1]
        pairs.append((f.name, f"elado-lakasok/{apt}/index.html"))

    extra, extra_imgs = {}, {}
    if len(sys.argv) > 3:  # building-picker popups were loaded by AJAX; their content belongs to the home page
        picker = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        items = []
        for b in picker["buildings"]:
            items += [b["title"], b["badge"]]
            items += [t.strip() for t in re.split(r"<[^>]+>", b["info"]) if t.strip()]
            for lv in b["levels"]:
                items += [lv["name"], lv["alt"]] + [a["title"] for a in lv["apts"]]
        extra["home.html"] = items
        extra_imgs["home.html"] = {image_id(lv["img"]) for b in picker["buildings"] for lv in b["levels"]}

    rows, missing_all = [], {}
    for o, n in pairs:
        o_texts = texts((orig / o).read_text(encoding="utf-8")) + extra.get(o, [])
        hay = page_text((dist / n).read_text(encoding="utf-8"))
        missing = [t for t in dict.fromkeys(o_texts) if needle(t) not in hay]
        rows.append((o, len(set(o_texts)), len(set(o_texts)) - len(missing), len(missing)))
        if missing:
            missing_all[o] = missing

    print(f"{'original page':40} {'texts':>6} {'found':>6} {'missing':>8}")
    for r in rows:
        print(f"{r[0]:40} {r[1]:>6} {r[2]:>6} {r[3]:>8}")
    print(f"{'TOTAL':40} {sum(r[1] for r in rows):>6} {sum(r[2] for r in rows):>6} {sum(r[3] for r in rows):>8}")
    for o, ms in missing_all.items():
        print(f"\n--- {o}")
        for m in ms:
            print("   ", m)

    # images: every <img> of an original page must be referenced by the matching new page
    print(f"\n{'original page':40} {'images':>6} {'found':>6} {'missing':>8}")
    total = missing_total = 0
    for o, n in pairs:
        s = BeautifulSoup((orig / o).read_text(encoding="utf-8"), "html.parser")
        ids = {
            image_id(i["src"])
            for root in s.find_all(["main", "header", "footer"])
            for i in root.find_all("img")
            if "/wp-content/uploads/" in (i.get("src") or "")
        } | extra_imgs.get(o, set())
        new_html = (dist / n).read_text(encoding="utf-8")
        miss = sorted(i for i in ids if not re.search(rf"img/{re.escape(i)}(-\d+)?\.(webp|svg|png)", new_html))
        total += len(ids)
        missing_total += len(miss)
        print(f"{o:40} {len(ids):>6} {len(ids) - len(miss):>6} {len(miss):>8}" + (f"   {', '.join(miss)}" if miss else ""))
    print(f"{'TOTAL':40} {total:>6} {total - missing_total:>6} {missing_total:>8}")


if __name__ == "__main__":
    main()
