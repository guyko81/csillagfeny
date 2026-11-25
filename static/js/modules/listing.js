// Apartment list filters: building, level, availability, area range and price sort.
// State is mirrored into the URL (?epulet=C&szint=1&elerheto=1&min=40&max=60&rendezes=asc)
// so a filtered list can be bookmarked or shared.
export function initListing() {
  const form = document.querySelector("[data-filters]");
  const list = document.querySelector("[data-apt-list]");
  if (!form || !list) return;

  const rows = Array.from(list.children);
  const countEl = document.querySelector("[data-results-count]");
  const emptyEl = document.querySelector("[data-results-empty]");
  const range = form.querySelector("[data-range]");
  const minIn = range.querySelector('input[name="min"]');
  const maxIn = range.querySelector('input[name="max"]');
  const minOut = range.querySelector("[data-range-min]");
  const maxOut = range.querySelector("[data-range-max]");
  const lo = Number(range.dataset.min);
  const hi = Number(range.dataset.max);

  // restore from URL
  const params = new URLSearchParams(location.search);
  if (params.has("epulet")) form.epulet.value = params.get("epulet");
  if (params.has("szint")) form.szint.value = params.get("szint");
  if (params.has("rendezes")) form.rendezes.value = params.get("rendezes");
  if (params.get("elerheto") === "1") form.elerheto.checked = true;
  if (params.has("min")) minIn.value = params.get("min");
  if (params.has("max")) maxIn.value = params.get("max");

  const paintRange = () => {
    let a = Number(minIn.value);
    let b = Number(maxIn.value);
    if (a > b) [a, b] = [b, a];
    minOut.value = a;
    maxOut.value = b;
    const inner = range.querySelector(".range__inputs");
    inner.style.setProperty("--lo", `${((a - lo) / (hi - lo)) * 100}%`);
    inner.style.setProperty("--hi", `${((b - lo) / (hi - lo)) * 100}%`);
    return [a, b];
  };

  const apply = () => {
    const [aMin, aMax] = paintRange();
    const building = form.epulet.value;
    const level = form.szint.value;
    const onlyAvailable = form.elerheto.checked;
    const sort = form.rendezes.value;

    let shown = 0;
    for (const row of rows) {
      const d = row.dataset;
      const area = Number(d.area);
      const ok =
        (!building || d.building === building) &&
        (!level || d.level === level) &&
        (!onlyAvailable || d.available === "1") &&
        area >= aMin &&
        area <= aMax + 0.999; // the slider is whole m²; 72,53 m² belongs to "72"
      row.hidden = !ok;
      if (ok) shown++;
    }

    const ordered = [...rows].sort((x, y) => {
      if (sort === "asc") return x.dataset.price - y.dataset.price;
      if (sort === "desc") return y.dataset.price - x.dataset.price;
      return x.dataset.order - y.dataset.order;
    });
    ordered.forEach((row) => list.append(row));

    countEl.innerHTML = `<strong>${shown}</strong> lakás`;
    emptyEl.hidden = shown > 0;

    const p = new URLSearchParams();
    if (building) p.set("epulet", building);
    if (level) p.set("szint", level);
    if (onlyAvailable) p.set("elerheto", "1");
    if (aMin !== lo) p.set("min", aMin);
    if (aMax !== hi) p.set("max", aMax);
    if (sort) p.set("rendezes", sort);
    const qs = p.toString();
    history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
  };

  form.addEventListener("input", apply);
  form.addEventListener("change", apply);
  form.addEventListener("submit", (e) => e.preventDefault());
  form.addEventListener("reset", () => setTimeout(apply)); // after the browser has reset the fields
  apply();

  // mobile: filters as a bottom sheet
  const openBtn = document.querySelector("[data-filters-open]");
  const closeBtn = form.querySelector("[data-filters-close]");
  const setOpen = (open) => {
    form.classList.toggle("is-open", open);
    document.body.classList.toggle("filters-shown", open);
    if (open) form.querySelector("select")?.focus();
  };
  openBtn?.addEventListener("click", () => setOpen(true));
  closeBtn?.addEventListener("click", () => {
    setOpen(false);
    openBtn?.focus();
  });
  document.addEventListener("click", (e) => {
    if (form.classList.contains("is-open") && !form.contains(e.target) && !openBtn.contains(e.target)) setOpen(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && form.classList.contains("is-open")) setOpen(false);
  });
}
