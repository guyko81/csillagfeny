# Csillagfény Lakópark – modernizált weboldal

A [csillagfenylakopark.hu](https://csillagfenylakopark.hu/) teljes tartalmának újraépítése modern,
gyors, statikus weboldalként. Élő előnézet: **https://guyko81.github.io/csillagfeny/**

- minden eredeti oldal megvan, ugyanazokon az útvonalakon: főoldal, `elado-lakasok/`, a 33 lakás
  adatlapja (`elado-lakasok/a1/` … `c11/`) és az `adatkezelesi-tajekoztato/`;
- reszponzív (320 px-től), sötét módot támogat, akadálymentes (billentyűzet, ARIA), nincs külső
  JavaScript-könyvtár és nincs követőkód / süti;
- interaktív lakásválasztó (épület → szintenkénti alaprajz kattintható lakásokkal), szűrhető és
  rendezhető lakáslista (a szűrés a linkben is megmarad), árkalkulátor (előrefizetés / önerő / hitel),
  képgalériák nagyítóval.

## Felépítés

```
content/            a weboldal adatai – ezeket kell szerkeszteni
  site.json         elérhetőségek, extrák (tároló, parkoló), kalkulátor-paraméterek, térkép, videó
  apartments.json   a 33 lakás: ár, elérhetőség, helyiségek, fotók, alaprajz, leírás
  buildings.json    az épületek státusza és a lakásválasztó alaprajz-zónái
  privacy.html      az adatkezelési tájékoztató szövege
  images.json       a képek listája (a képimportáló generálja)
templates/          Jinja2 sablonok (oldalak + közös részek)
static/             css, js (ES modulok), self-hosted betűtípusok, reszponzív WebP képek
tools/build.py      statikus oldal generálása a dist/ mappába
tools/serve.py      helyi előnézet a GitHub Pages-szel azonos /csillagfeny/ útvonalon
tools/check_links.py  minden helyi hivatkozás / kép meglétének ellenőrzése
tools/import/       egyszeri import az eredeti WordPress oldalról (+ tartalmi teljességi ellenőrzés)
```

## Helyi futtatás

```powershell
pip install -r requirements.txt
python tools/build.py
python tools/serve.py        # http://localhost:8765/csillagfeny/
```

## Tartalom módosítása

- **Ár vagy foglaltság**: `content/apartments.json` → az adott lakás `price` / `available` mezője.
  Minden ebből számolódik: lista, adatlap, kalkulátor, lakásválasztó színei és számlálói,
  „További lakások" sáv, főoldali „elérhető lakás" szám.
- **Elérhetőségek, extrák, kalkulátor-kedvezmények**: `content/site.json`.
- **Épület státusza** (pl. „Most épül" → „Költözhető"): `content/buildings.json`.
- Feltöltés után (`git push` a `main` ágra) a GitHub Actions újraépíti és kiteszi az oldalt.

## Tudnivalók

- **Kapcsolati űrlap**: a GitHub Pages-nek nincs szervere, ezért az űrlap ellenőrzés után a látogató
  levelezőprogramját nyitja meg előre kitöltött levéllel (`mailto:`). Valódi űrlap-szolgáltatás
  bekötéséhez csak a `static/js/modules/contact-form.js` `deliver` függvényét kell lecserélni.
- **Keresők**: amíg ez előnézet, minden oldal `noindex` (`"indexable": false` a `site.json`-ban),
  hogy ne versenyezzen az eredeti oldallal a keresőkben. Saját domainre költözéskor állítsa
  `true`-ra és írja át a `site_url`-t.
- **Térkép**: OpenStreetMap beágyazás (nem kell API-kulcs, nem tesz sütit), mellette Google Maps
  útvonaltervező link.
- **Videó**: a YouTube csak a lejátszás gombra kattintva töltődik be (youtube-nocookie.com).
- A képek, szövegek és a logó az eredeti weboldal tulajdonosáé.

## Újraimportálás az eredeti oldalról

A `tools/import/` szkriptjei (`crawl.py` → `extract.py` → `collect_images.py` → `images.py` →
`make_content.py`) állították elő a `content/` és `static/img/` tartalmát; a `check_migration.py`
ellenőrzi, hogy az eredeti oldalak minden szövege és képe szerepel-e az újakon
(`pip install -r tools/import/requirements.txt`). A lakásválasztó felugró ablakait az eredeti oldal
AJAX-szal tölti be, ezek adatait (alaprajzok, lakászónák) böngészőből mentettük ki.
A `make_content.py` felülírja a `content/` fájljait – kézi szerkesztés után ne futtassa újra.
