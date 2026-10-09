// The pet photo field: preview, drag and drop, and the same limits the server checks.
(function () {
  "use strict";

  const drop = document.querySelector("[data-photo-drop]");
  if (!drop) return;
  const input = drop.querySelector("input[type=file]");
  const preview = drop.querySelector("[data-photo-preview]");
  const change = drop.querySelector("[data-photo-change]");
  const error = drop.parentElement.querySelector("[data-photo-error]");
  const accepted = ["image/jpeg", "image/png", "image/webp"];
  const maxBytes = 5 * 1024 * 1024;
  let url = null;

  const described = (input.getAttribute("aria-describedby") || "").split(" ").filter(Boolean);
  const fail = (message) => {
    error.textContent = message;
    error.classList.toggle("hidden", !message);
    input.setAttribute("aria-invalid", message ? "true" : "false");
    const ids = message ? [...described, error.id] : described;
    input.setAttribute("aria-describedby", ids.join(" "));
  };

  const show = () => {
    const file = input.files && input.files[0];
    if (url) URL.revokeObjectURL(url);
    url = null;
    if (!file) {
      preview.classList.add("hidden");
      change.classList.add("hidden");
      return;
    }
    if (!accepted.includes(file.type)) {
      fail("Envie uma imagem JPEG, PNG ou WEBP.");
      input.value = "";
      return show();
    }
    if (file.size > maxBytes) {
      fail("A foto passa de 5 MB.");
      input.value = "";
      return show();
    }
    fail("");
    url = URL.createObjectURL(file);
    preview.src = url;
    preview.classList.remove("hidden");
    change.classList.remove("hidden");
  };

  input.addEventListener("change", show);
  ["dragenter", "dragover"].forEach((name) =>
    drop.addEventListener(name, (event) => {
      event.preventDefault();
      drop.classList.add("is-dragging");
    }),
  );
  ["dragleave", "drop"].forEach((name) => drop.addEventListener(name, () => drop.classList.remove("is-dragging")));
  drop.addEventListener("drop", (event) => {
    event.preventDefault();
    if (event.dataTransfer && event.dataTransfer.files.length) {
      input.files = event.dataTransfer.files;
      show();
    }
  });
})();
