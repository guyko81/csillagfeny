// Contact form. GitHub Pages has no server, so a valid form opens the visitor's e-mail
// client with the message pre-filled (mailto:, RFC 6068). To use a form backend later,
// replace `deliver` only; validation and UI stay as they are.
export function initContactForm() {
  document.querySelectorAll("[data-contact-form]").forEach(setup);
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function deliver(form, data) {
  const subject = `Érdeklődés – Csillagfény Lakópark${data.page ? ` (${data.page})` : ""}`;
  const lines = [data.message, "", "—", `Név: ${data.name}`, `Email: ${data.email}`, `Telefonszám: ${data.phone}`];
  if (data.page) lines.push(`Lakás: ${data.page}`);
  const body = lines.join("\r\n");
  const href = `mailto:${form.dataset.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  window.location.href = href;
  return Promise.resolve();
}

function setup(form) {
  const status = form.querySelector("[data-form-status]");

  const check = (field) => {
    const wrap = field.closest(".field");
    const err = wrap.querySelector(".field__error");
    let ok;
    if (field.type === "checkbox") ok = field.checked;
    else if (field.type === "email") ok = EMAIL_RE.test(field.value.trim());
    else if (field.type === "tel") ok = field.value.replace(/\D/g, "").length >= 6;
    else ok = field.value.trim().length > 0;
    wrap.classList.toggle("is-invalid", !ok);
    field.setAttribute("aria-invalid", String(!ok));
    err.textContent = ok ? "" : err.dataset.error;
    return ok;
  };

  const fields = Array.from(form.querySelectorAll("input, textarea"));
  fields.forEach((f) => {
    f.addEventListener("blur", () => f.value && check(f));
    f.addEventListener("input", () => f.closest(".field").classList.contains("is-invalid") && check(f));
    f.addEventListener("change", () => f.type === "checkbox" && check(f));
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const results = fields.map(check);
    if (results.includes(false)) {
      fields[results.indexOf(false)].focus();
      return;
    }
    const fd = new FormData(form);
    await deliver(form, {
      name: fd.get("name").trim(),
      email: fd.get("email").trim(),
      phone: fd.get("phone").trim(),
      message: fd.get("message").trim(),
      page: form.dataset.page || "",
    });
    status.hidden = false;
    status.textContent = `Megnyitottuk a levelezőprogramját az üzenettel – küldje el onnan. Ha nem nyílt meg, írjon nekünk közvetlenül: ${form.dataset.email}`;
  });
}
