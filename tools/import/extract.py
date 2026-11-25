"""Extract apartment data from the downloaded original pages into JSON.

Usage: python -P -E extract.py <pages_dir> <out_json>
"""
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
pages = Path(sys.argv[1])
out = Path(sys.argv[2])


def srcset_list(img):
    items = []
    ss = img.get("srcset") or ""
    for part in ss.split(","):
        part = part.strip()
        if not part:
            continue
        bits = part.split()
        url = bits[0]
        w = int(bits[1][:-1]) if len(bits) > 1 and bits[1].endswith("w") else 0
        items.append({"url": url, "w": w})
    if not items and img.get("src"):
        items.append({"url": img["src"], "w": int(img.get("width") or 0)})
    return items


def img_info(img):
    return {
        "src": img.get("src"),
        "alt": img.get("alt", ""),
        "width": img.get("width"),
        "height": img.get("height"),
        "srcset": srcset_list(img),
    }


def text(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else ""


apartments = []
for f in sorted(pages.glob("elado-lakasok_*.html")):
    apt_id = f.stem.split("_", 1)[1]
    s = BeautifulSoup(f.read_text(encoding="utf-8"), "html.parser")
    main = s.find("main", id="brx-content")
    d = {"id": apt_id}
    d["seo_heading"] = text(main.find("h1", class_="apartment-subheading"))
    d["name"] = text(main.find(id="brxe-xuekyf"))
    d["photos"] = [img_info(i) for i in main.select(".apartment-photo-slider img")]
    fp = main.select_one("#brxe-hmkzel img")
    d["floorplan"] = img_info(fp) if fp else None
    desc = main.select_one("#brxe-fiicqe > .brxe-text")
    d["description_html"] = desc.decode_contents().strip() if desc else ""
    d["description_text"] = text(desc)
    rows = []
    for tr in main.select("table.apartment-data-table tr"):
        tds = [text(td) for td in tr.find_all("td")]
        if len(tds) == 3:
            rows.append({"level": tds[0], "room": tds[1], "area": tds[2]})
    d["rooms"] = rows
    d["total_area"] = text(main.select_one(".price-calculator__entire-area"))
    d["gross_area"] = text(main.select_one(".apartment-area-price__wrapper .text--dark-muted"))
    np_ = main.select_one(".price-calculator__normal-price")
    d["normal_price"] = int(re.sub(r"\D", "", text(np_))) if np_ else None
    # every info-box text inside the price calculator, to catch per-page differences
    d["calc_infos"] = [text(p) for p in main.select(".price-calculator .info-box p")]
    d["calc_tabs"] = [text(t) for t in main.select(".price-calculator__tab-name")]
    d["calc_open_tab"] = (main.select_one(".price-calculator__inner") or {}).get("data-open-tab")
    d["status"] = text(main.select_one(".apartment-available__status"))
    link = main.select_one(".apartment-available__link")
    d["status_link"] = {"text": text(link), "href": link.get("href")} if link else None
    d["extras"] = [
        {"desc": text(o.select_one(".parking-option__description")), "price": text(o.select_one(".parking-option__price"))}
        for o in main.select("#brxe-vffbsc .parking-option")
    ]
    d["more_heading"] = text(main.select_one("#brxe-yzwgtd h2"))
    d["more_cards"] = [
        {
            "href": a.select_one(".apartment-card__heading a")["href"],
            "level": text(a.select_one(".apartment-card__building-and-level")),
            "area": text(a.select_one(".apartment-card__entire-area")),
        }
        for a in main.select("article.apartment-card")
    ]
    title = s.find("title")
    d["page_title"] = text(title)
    md = s.find("meta", attrs={"name": "description"})
    d["meta_description"] = md.get("content") if md else ""
    apartments.append(d)

# listing page: building / level / availability / price per card, as displayed there
listing = {}
s = BeautifulSoup((pages / "elado-lakasok.html").read_text(encoding="utf-8"), "html.parser")
for card in s.select("article.apartment-list-card"):
    a = card.select_one(".apartment-list-card__seo-heading a")
    href = a["href"] if a else None
    apt_id = href.rstrip("/").split("/")[-1] if href else None
    listing[apt_id] = {
        "seo_heading": text(a),
        "title": text(card.select_one(".apartment-list-card__title")),
        "excerpt": text(card.select_one(".apartment-list-card__description")),
        "building_level": text(card.select_one(".apartment-list-card__building-and-level")),
        "area": text(card.select_one(".apartment-list-card__entire-area")),
        "availability": text(card.select_one(".apartment-list-card__availability")),
        "price": text(card.select_one(".apartment-list-card__price")),
        "image": img_info(card.select_one("img")) if card.select_one("img") else None,
    }

# privacy page body
s = BeautifulSoup((pages / "adatkezelesi-tajekoztato.html").read_text(encoding="utf-8"), "html.parser")
pc = s.select_one(".brxe-post-content")
for el in pc.find_all(True):
    for attr in ("class", "style"):
        el.attrs.pop(attr, None)
privacy = {"h1": text(s.select_one("main h1")), "html": pc.decode_contents().strip()}

out.write_text(
    json.dumps({"apartments": apartments, "listing": listing, "privacy": privacy}, ensure_ascii=False, indent=1),
    encoding="utf-8",
)
print(len(apartments), "apartments,", len(listing), "listing cards")
