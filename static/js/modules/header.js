// Sticky header state + mobile navigation panel.
export function initHeader() {
  const header = document.querySelector("[data-header]");
  if (!header) return;

  const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 24);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  const toggle = header.querySelector("[data-nav-toggle]");
  const panel = document.querySelector("[data-mobile-nav]");
  if (!toggle || !panel) return;

  const setOpen = (open) => {
    toggle.setAttribute("aria-expanded", String(open));
    if (open) {
      panel.hidden = false;
      // next frame, so the panel's fade/slide-in transition actually runs
      requestAnimationFrame(() => {
        header.classList.add("is-open");
        document.body.classList.add("nav-open");
      });
    } else {
      header.classList.remove("is-open");
      document.body.classList.remove("nav-open");
      panel.hidden = true;
    }
  };

  toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));
  panel.addEventListener("click", (e) => {
    if (e.target.closest("a")) setOpen(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      setOpen(false);
      toggle.focus();
    }
  });
  window.matchMedia("(min-width: 901px)").addEventListener("change", (e) => {
    if (e.matches) setOpen(false);
  });
}
