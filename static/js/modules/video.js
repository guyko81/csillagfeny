// Click-to-load YouTube (privacy-enhanced domain): nothing is requested from YouTube before the click.
export function initVideo() {
  document.querySelectorAll("[data-video]").forEach((box) => {
    const btn = box.querySelector("[data-video-play]");
    btn?.addEventListener("click", () => {
      const id = box.dataset.youtube;
      const iframe = document.createElement("iframe");
      iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?autoplay=1&rel=0`;
      iframe.title = "Csillagfény Lakópark – bemutató videó";
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
      iframe.allowFullscreen = true;
      iframe.referrerPolicy = "strict-origin-when-cross-origin";
      box.append(iframe);
      btn.remove();
      iframe.focus();
    });
  });
}
