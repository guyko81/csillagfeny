// Payment options on an apartment page. Same arithmetic as the original site:
//   prepay:  discounted = round(price × (1 − discount)), saving = price − discounted
//   own:     price, price per m² = round(price / area)
//   loan:    loan = round((price − own) × (1 + surcharge)), saved = round(own × surcharge),
//            price per m² = round((own + loan) / area)
// Build-time HTML already shows the initial values; this module keeps them live.
const fmt = new Intl.NumberFormat("hu-HU", { maximumFractionDigits: 0 });
const huf = (n) => `${fmt.format(n)} Ft`;

export function initCalculator() {
  document.querySelectorAll("[data-calc]").forEach(setupCalc);
}

function setupCalc(root) {
  setupTabs(root);
  const price = Number(root.dataset.price);
  const area = Number(root.dataset.area);
  const surcharge = Number(root.dataset.surcharge);
  const input = root.querySelector("[data-calc-own]");
  const out = (key) => root.querySelector(`[data-calc-out="${key}"]`);
  if (!input) return;

  const recalc = () => {
    let own = Number(input.value.replace(/\D/g, "")) || 0;
    if (own > price) own = price;
    const loan = Math.round((price - own) * (1 + surcharge));
    out("own").textContent = huf(own);
    out("loan").textContent = huf(loan);
    out("saved").textContent = huf(Math.round(own * surcharge));
    out("sqm").textContent = huf(Math.round((own + loan) / area));
    return own;
  };

  input.addEventListener("input", () => {
    const own = recalc();
    const digits = input.value.replace(/\D/g, "");
    input.value = digits ? fmt.format(own) : "";
  });
  recalc();
}

function setupTabs(root) {
  const tabs = Array.from(root.querySelectorAll('[role="tab"]'));
  const select = (tab, focus) => {
    for (const t of tabs) {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
      root.querySelector(`#${t.getAttribute("aria-controls")}`).hidden = !on;
    }
    if (focus) tab.focus();
    if (tab.id === "tab-loan") root.querySelector("[data-calc-own]")?.focus({ preventScroll: true });
  };
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", (e) => {
      const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (d) {
        e.preventDefault();
        select(tabs[(i + d + tabs.length) % tabs.length], true);
      }
    });
  });
}
