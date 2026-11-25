// Building picker: pins open a per-building <dialog> with clickable floor-plan zones.
export function initPicker() {
  const dialogs = new Map();
  document.querySelectorAll("[data-building-dialog]").forEach((d) => dialogs.set(d.dataset.buildingDialog, d));
  if (!dialogs.size) return;

  document.addEventListener("click", (e) => {
    const opener = e.target.closest("[data-building-open]");
    if (opener) {
      const dialog = dialogs.get(opener.dataset.buildingOpen);
      if (!dialog) return;
      dialog.showModal();
      dialog.scrollTop = 0;
      document.body.classList.add("has-modal");
      return;
    }
    if (e.target.closest("[data-dialog-close]")) e.target.closest("dialog")?.close();
  });

  for (const dialog of dialogs.values()) {
    // click on the backdrop closes
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) dialog.close();
    });
    dialog.addEventListener("close", () => {
      document.body.classList.remove("has-modal");
      hideTip();
    });
  }

  // tooltip for floor-plan zones (mouse only; touch users get the list under each plan)
  const tip = document.querySelector("[data-plan-tip]");
  if (!tip) return;
  // the tooltip must live inside the open modal dialog to be rendered above it (top layer)
  const showTip = (a, x, y) => {
    const dialog = a.closest("dialog");
    if (tip.parentElement !== dialog) dialog.append(tip);
    tip.innerHTML = "";
    tip.append(a.dataset.tip);
    if (a.dataset.tipSub) {
      const s = document.createElement("small");
      s.textContent = a.dataset.tipSub;
      tip.append(s);
    }
    tip.style.left = `${x}px`;
    tip.style.top = `${y}px`;
    tip.hidden = false;
  };
  function hideTip() {
    tip.hidden = true;
  }
  document.addEventListener("pointermove", (e) => {
    if (e.pointerType !== "mouse") return;
    const a = e.target.closest?.("a[data-tip]");
    if (a) showTip(a, e.clientX, e.clientY);
    else if (!tip.hidden) hideTip();
  });
  document.addEventListener("focusin", (e) => {
    const a = e.target.closest?.("a[data-tip]");
    if (!a) return;
    const r = a.getBoundingClientRect();
    showTip(a, r.left + r.width / 2, r.top + r.height / 2);
  });
  document.addEventListener("focusout", hideTip);
}
