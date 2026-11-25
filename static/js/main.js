// Entry point: every module scans the page for its own data-* hooks and does nothing if absent.
import { initHeader } from "./modules/header.js";
import { initReveal } from "./modules/reveal.js";
import { initCarousels } from "./modules/carousel.js";
import { initLightbox } from "./modules/lightbox.js";
import { initPicker } from "./modules/picker.js";
import { initVideo } from "./modules/video.js";
import { initListing } from "./modules/listing.js";
import { initCalculator } from "./modules/calculator.js";
import { initContactForm } from "./modules/contact-form.js";

const modules = [initHeader, initReveal, initCarousels, initLightbox, initPicker, initVideo, initListing, initCalculator, initContactForm];

for (const init of modules) {
  try {
    init();
  } catch (err) {
    // one broken widget must not take the rest of the page down
    console.error(err);
  }
}
