// Scroll-snap carousels: native swipe/scroll, plus prev/next buttons and a position counter.
export function initCarousels() {
  document.querySelectorAll("[data-carousel]").forEach(setup);
}

function setup(root) {
  const track = root.querySelector("[data-carousel-track]");
  const prev = root.querySelector("[data-carousel-prev]");
  const next = root.querySelector("[data-carousel-next]");
  const count = root.querySelector("[data-carousel-count]");
  if (!track) return;
  const slides = () => Array.from(track.children);

  const step = () => {
    const items = slides();
    if (items.length < 2) return track.clientWidth;
    const gap = items[1].offsetLeft - items[0].offsetLeft;
    // move by as many whole items as are fully visible (at least one)
    return Math.max(1, Math.floor(track.clientWidth / gap)) * gap;
  };

  const update = () => {
    const items = slides();
    const max = track.scrollWidth - track.clientWidth - 2;
    if (prev) prev.disabled = track.scrollLeft <= 2;
    if (next) next.disabled = track.scrollLeft >= max;
    if (count && items.length) {
      const first = items[0].offsetLeft;
      let idx = 0;
      items.forEach((el, i) => {
        if (el.offsetLeft - first <= track.scrollLeft + 4) idx = i;
      });
      const perView = Math.max(1, Math.round(track.clientWidth / (items[1] ? items[1].offsetLeft - items[0].offsetLeft : track.clientWidth)));
      const last = Math.min(items.length, idx + perView);
      count.textContent = perView > 1 ? `${idx + 1}–${last} / ${items.length}` : `${idx + 1} / ${items.length}`;
    }
  };

  prev?.addEventListener("click", () => track.scrollBy({ left: -step(), behavior: "smooth" }));
  next?.addEventListener("click", () => track.scrollBy({ left: step(), behavior: "smooth" }));
  track.addEventListener("scroll", () => requestAnimationFrame(update), { passive: true });
  window.addEventListener("resize", update);
  update();

  // keep the carousel and the lightbox in sync: when the lightbox moves, scroll here too
  root.addEventListener("lightbox:show", (e) => {
    const el = e.detail?.trigger?.closest("[data-carousel-track] > *");
    if (el) track.scrollTo({ left: el.offsetLeft - slides()[0].offsetLeft, behavior: "instant" });
  });
}
