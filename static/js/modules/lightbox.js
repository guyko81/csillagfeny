// One shared <dialog> lightbox. Any element with data-lightbox="<group>" data-full="<url>" opens it;
// elements sharing the same group value form one browsable set, in document order.
export function initLightbox() {
  const dialog = document.querySelector("[data-lightbox-dialog]");
  if (!dialog || !document.querySelector("[data-lightbox]")) return;

  const img = dialog.querySelector("[data-lightbox-img]");
  const caption = dialog.querySelector("[data-lightbox-caption]");
  const counter = dialog.querySelector("[data-lightbox-count]");
  const prevBtn = dialog.querySelector("[data-lightbox-prev]");
  const nextBtn = dialog.querySelector("[data-lightbox-next]");
  let items = [];
  let index = 0;
  let opener = null;

  const show = (i) => {
    index = (i + items.length) % items.length;
    const el = items[index];
    img.classList.toggle("is-plan", /alaprajz/.test(el.dataset.caption || "") || /alaprajz/.test(el.dataset.lightbox || ""));
    img.src = el.dataset.full;
    img.alt = el.dataset.caption || "";
    caption.textContent = el.dataset.caption || "";
    counter.textContent = items.length > 1 ? `${index + 1} / ${items.length}` : "";
    prevBtn.hidden = nextBtn.hidden = items.length < 2;
    el.closest("[data-carousel]")?.dispatchEvent(new CustomEvent("lightbox:show", { detail: { trigger: el } }));
    // warm the cache for the neighbours
    [index + 1, index - 1].forEach((j) => {
      const n = items[(j + items.length) % items.length];
      if (n) new Image().src = n.dataset.full;
    });
  };

  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-lightbox]");
    if (!trigger) return;
    e.preventDefault();
    const group = trigger.dataset.lightbox;
    items = Array.from(document.querySelectorAll("[data-lightbox]")).filter((el) => el.dataset.lightbox === group);
    opener = trigger;
    show(items.indexOf(trigger));
    dialog.showModal();
    document.body.classList.add("has-modal");
  });

  prevBtn.addEventListener("click", () => show(index - 1));
  nextBtn.addEventListener("click", () => show(index + 1));
  dialog.querySelector("[data-lightbox-close]").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog || e.target.classList.contains("lightbox__frame")) dialog.close();
  });
  dialog.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") show(index - 1);
    if (e.key === "ArrowRight") show(index + 1);
  });
  dialog.addEventListener("close", () => {
    document.body.classList.remove("has-modal");
    img.removeAttribute("src");
    opener?.focus({ preventScroll: true });
  });

  // swipe left/right on touch screens
  let startX = null;
  img.addEventListener("pointerdown", (e) => (startX = e.clientX));
  img.addEventListener("pointerup", (e) => {
    if (startX === null) return;
    const dx = e.clientX - startX;
    startX = null;
    if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
  });
}
