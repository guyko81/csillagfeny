"""Turn the raw extraction of the original site into the content files the build reads.

Usage:
    python tools/import/make_content.py <extracted.json> <picker_raw.json>

Writes content/apartments.json, content/buildings.json and content/privacy.html.
After the import these files are the source of truth and are edited by hand.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from images import image_id  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"


def area_number(label: str) -> float:
    m = re.search(r"(\d+),(\d+)", label)
    return float(f"{m.group(1)}.{m.group(2)}")


def natural_key(apt_id: str):
    return apt_id[0], int(apt_id[1:])


def main():
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    picker = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

    apartments = []
    for a in sorted(raw["apartments"], key=lambda x: natural_key(x["id"])):
        card = raw["listing"][a["id"]]
        level = int(re.search(r"(\d)\. szint", card["building_level"]).group(1))
        status = a["status"]
        assert status in ("Ez a lakás foglalt", "Ez a lakás elérhető"), status
        assert card["availability"] in ("Foglalt", "Elérhető"), card["availability"]
        available = status.endswith("elérhető")
        assert available == (card["availability"] == "Elérhető"), a["id"]
        assert int(re.sub(r"\D", "", card["price"])) == a["normal_price"], a["id"]
        apartments.append(
            {
                "id": a["id"],
                "name": a["name"],
                "building": a["id"][0].upper(),
                "level": level,
                "seo_heading": a["seo_heading"],
                "description_html": a["description_html"],
                "meta_description": a["meta_description"],
                "card_image": {"img": image_id(card["image"]["src"]), "alt": card["image"]["alt"]},
                "photos": [{"img": image_id(p["src"]), "alt": p["alt"]} for p in a["photos"]],
                "floorplan": {"img": image_id(a["floorplan"]["src"]), "alt": a["floorplan"]["alt"]},
                "rooms": a["rooms"],
                "total_area": area_number(a["total_area"]),
                "total_area_label": a["total_area"],
                "gross_area_label": a["gross_area"],
                "price": a["normal_price"],
                "available": available,
            }
        )
    (CONTENT / "apartments.json").write_text(json.dumps(apartments, ensure_ascii=False, indent=1), encoding="utf-8")

    buildings = []
    for b in picker["buildings"]:
        letter = b["term"][0].upper()
        levels = []
        for lv in b["levels"]:
            levels.append(
                {
                    "name": lv["name"],
                    "img": image_id(lv["img"]),
                    "alt": lv["alt"],
                    "viewBox": lv["viewBox"],
                    "apartments": [{"id": x["href"].rstrip("/").split("/")[-1], "d": x["d"]} for x in lv["apts"]],
                }
            )
        buildings.append(
            {
                "id": letter,
                "name": b["title"],
                "status": b["status"],
                "position": picker["button_positions"][b["term"]],
                "levels": levels,
            }
        )
    (CONTENT / "buildings.json").write_text(json.dumps(buildings, ensure_ascii=False, indent=1), encoding="utf-8")

    (CONTENT / "privacy.html").write_text(raw["privacy"]["html"] + "\n", encoding="utf-8")
    print(len(apartments), "apartments,", len(buildings), "buildings")


if __name__ == "__main__":
    main()
