"""Build the static site from content/ + templates/ + static/ into dist/.

Usage: python tools/build.py [--out dist]

Every page uses relative links (``root`` is the path back to the site root), so the
output works under any base path: a GitHub Pages project URL or a custom domain.
"""
import argparse
import hashlib
import json
import math
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from jinja2 import Environment, FileSystemLoader, StrictUndefined, pass_context, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
TEMPLATES = ROOT / "templates"

LEVEL_NAMES = {0: "Földszint", 1: "Emelet", 2: "Tetőtér"}


def load_json(name):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def js_round(x: float) -> int:
    """Math.round semantics (half up), so build-time numbers match the browser."""
    return math.floor(x + 0.5)


def huf(n) -> str:
    return f"{int(n):,}".replace(",", " ") + " Ft"


def area(x: float) -> str:
    return f"{x:.2f}".replace(".", ",") + " ㎡"


class Site:
    def __init__(self, out: Path):
        self.out = out
        self.site = load_json("site.json")
        self.images = load_json("images.json")
        self.apartments = load_json("apartments.json")
        self.buildings = load_json("buildings.json")
        self.privacy_html = (CONTENT / "privacy.html").read_text(encoding="utf-8")
        self.by_id = {a["id"]: a for a in self.apartments}
        self.asset_versions = {}
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES),
            autoescape=select_autoescape(["html", "xml", "svg"]),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters.update(huf=huf, area=area, js_round=js_round)
        self.env.globals.update(
            site=self.site,
            apartments=self.apartments,
            buildings=self.buildings,
            level_names=LEVEL_NAMES,
            img=self.img_tag,
            img_url=self.img_url,
            img_path=self.img_url_plain,
            asset=self.asset_url,
            year=date.today().year,
            available_count=sum(a["available"] for a in self.apartments),
        )

    # ---------- helpers exposed to templates ----------
    def image(self, img_id):
        try:
            return self.images[img_id]
        except KeyError:
            raise KeyError(f"image '{img_id}' is not in content/images.json") from None

    @pass_context
    def img_url(self, ctx, img_id, width=None):
        im = self.image(img_id)
        if im.get("vector"):
            return ctx["root"] + im["file"]
        sizes = sorted(im["sizes"].items(), key=lambda kv: int(kv[0]))
        if width is None:
            return ctx["root"] + sizes[-1][1]
        fit = [p for w, p in sizes if int(w) >= width]
        return ctx["root"] + (fit[0] if fit else sizes[-1][1])

    @pass_context
    def img_tag(self, ctx, img_id, alt="", sizes="100vw", cls="", loading="lazy", priority=False, attrs=""):
        im = self.image(img_id)
        root = ctx["root"]
        a = [f'alt="{escape(alt)}"']
        if cls:
            a.append(f'class="{escape(cls)}"')
        if im.get("vector"):
            a.insert(0, f'src="{root}{im["file"]}"')
        else:
            ordered = sorted(im["sizes"].items(), key=lambda kv: int(kv[0]))
            w0, p0 = ordered[0]
            a.insert(0, f'src="{root}{p0}"')
            if len(ordered) > 1:
                a.append('srcset="' + ", ".join(f"{root}{p} {w}w" for w, p in ordered) + '"')
                a.append(f'sizes="{escape(sizes)}"')
            a.append(f'width="{im["w"]}" height="{im["h"]}"')
        if priority:
            a.append('fetchpriority="high"')
        else:
            a.append(f'loading="{loading}" decoding="async"')
        if attrs:
            a.append(attrs)
        return Markup("<img " + " ".join(a) + ">")

    @pass_context
    def asset_url(self, ctx, rel):
        if rel not in self.asset_versions:
            digest = hashlib.sha256((STATIC / rel).read_bytes()).hexdigest()[:10]
            self.asset_versions[rel] = digest
        return f"{ctx['root']}{rel}?v={self.asset_versions[rel]}"

    # ---------- data shaped for pages ----------
    def apartment_view(self, a):
        price = a["price"]
        pc = self.site["price_calculator"]
        discounted = js_round(price * (1 - pc["prepay_discount"]))
        return {
            **a,
            "level_label": f"{a['level']}. szint",
            "building_level": f"({a['building']}. épület) {a['level']}. szint",
            "discounted_price": discounted,
            "discount_saving": price - discounted,
            "sqm_price": js_round(price / a["total_area"]),
            "discounted_sqm_price": js_round(discounted / a["total_area"]),
        }

    def building_counts(self):
        counts = {b["id"]: 0 for b in self.buildings}
        for a in self.apartments:
            counts[a["building"]] += 1
        return counts

    def level_counts(self):
        counts = {}
        for a in self.apartments:
            counts[a["level"]] = counts.get(a["level"], 0) + 1
        return dict(sorted(counts.items()))

    def picker_data(self):
        """Building picker payload: geometry from buildings.json, status from apartments.json."""
        out = []
        for b in self.buildings:
            apts = [a for a in self.apartments if a["building"] == b["id"]]
            out.append(
                {
                    **b,
                    "available": sum(a["available"] for a in apts),
                    "total": len(apts),
                    "levels": [
                        {
                            **lv,
                            "src": self.img_url_plain(lv["img"]),
                            "apartments": [
                                {
                                    **x,
                                    "name": self.by_id[x["id"]]["name"],
                                    "available": self.by_id[x["id"]]["available"],
                                    "area": area(self.by_id[x["id"]]["total_area"]),
                                    "price": huf(self.by_id[x["id"]]["price"]),
                                }
                                for x in lv["apartments"]
                            ],
                        }
                        for lv in b["levels"]
                    ],
                }
            )
        return out

    def img_url_plain(self, img_id):
        im = self.image(img_id)
        return max(im["sizes"].items(), key=lambda kv: int(kv[0]))[1]

    # ---------- rendering ----------
    def render(self, template, rel_path, **ctx):
        depth = rel_path.count("/")
        root = "../" * depth
        path_url = rel_path[: -len("index.html")] if rel_path.endswith("index.html") else rel_path
        html = self.env.get_template(template).render(
            root=root, canonical=self.site["site_url"] + path_url, path_url=path_url, **ctx
        )
        dest = self.out / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")

    def build(self):
        if self.out.exists():
            shutil.rmtree(self.out)
        shutil.copytree(STATIC, self.out)
        views = [self.apartment_view(a) for a in self.apartments]
        available = [v for v in views if v["available"]]
        picker = self.picker_data()

        self.render("home.html", "index.html", page="home", picker=picker, has_contact=True)
        # default list order as on the original site: available apartments first
        listing_views = sorted(views, key=lambda v: (not v["available"], v["building"], int(v["id"][1:])))
        self.render(
            "listing.html",
            "elado-lakasok/index.html",
            page="listing",
            views=listing_views,
            building_counts=self.building_counts(),
            level_counts=self.level_counts(),
            area_min=math.floor(min(a["total_area"] for a in self.apartments)),
            area_max=math.ceil(max(a["total_area"] for a in self.apartments)),
            has_contact=True,
        )
        for v in views:
            more = [x for x in available if x["id"] != v["id"]]
            # same order as the original "További lakások" slider: newest first (C11 … C1)
            more.sort(key=lambda x: (x["building"], int(x["id"][1:])), reverse=True)
            self.render(
                "apartment.html", f"elado-lakasok/{v['id']}/index.html", page="apartment", a=v, more=more, has_contact=True
            )
        self.render("privacy.html", "adatkezelesi-tajekoztato/index.html", page="privacy", body=Markup(self.privacy_html), has_contact=False)
        self.render("404.html", "404.html", page="404", has_contact=False,
                    base_path=urlsplit(self.site["site_url"]).path)

        urls = ["", "elado-lakasok/", "adatkezelesi-tajekoztato/"] + [f"elado-lakasok/{a['id']}/" for a in self.apartments]
        if self.site["indexable"]:
            sitemap = "\n".join(f"  <url><loc>{self.site['site_url']}{u}</loc></url>" for u in urls)
            (self.out / "sitemap.xml").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + sitemap + "\n</urlset>\n", encoding="utf-8")
            robots = f"User-agent: *\nAllow: /\nSitemap: {self.site['site_url']}sitemap.xml\n"
            (self.out / "robots.txt").write_text(robots, encoding="utf-8")
        # When not indexable, every page carries <meta name="robots" content="noindex">
        # (a robots.txt below a project sub-path would be ignored by crawlers anyway).
        print(f"built {len(urls) + 1} pages into {self.out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist"))
    args = ap.parse_args()
    Site(Path(args.out)).build()


if __name__ == "__main__":
    main()
