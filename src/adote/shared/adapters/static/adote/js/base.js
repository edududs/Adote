// Behaviour shared by every page. Plain JavaScript, loaded with `defer`: the DOM is ready here.
// Everything degrades: without this file the pages still work, just without the niceties.
(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));
  const announcer = document.getElementById("announcer");
  const announce = (text) => {
    if (!announcer) return;
    announcer.textContent = "";
    setTimeout(() => {
      announcer.textContent = text;
    }, 100);
  };

  // Masks: (61) 99999-0000 / (61) 3333-0000 and 70000-000, applied while typing.
  const masks = {
    phone(digits) {
      const d = digits.slice(0, 11);
      if (d.length <= 2) return d.length ? `(${d}` : "";
      const area = `(${d.slice(0, 2)}) `;
      const rest = d.slice(2);
      const split = d.length === 11 ? 5 : 4;
      return rest.length > split ? `${area}${rest.slice(0, split)}-${rest.slice(split)}` : area + rest;
    },
    cep(digits) {
      const d = digits.slice(0, 8);
      return d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
    },
  };
  $$("input[data-mask]").forEach((input) => {
    const mask = masks[input.dataset.mask];
    if (!mask) return;
    const apply = () => {
      input.value = mask(input.value.replace(/\D/g, ""));
    };
    // Typing at the end reformats at once; an edit in the middle waits for blur, so the caret stays put.
    input.addEventListener("input", () => {
      if (input.selectionStart === input.value.length) apply();
    });
    input.addEventListener("blur", apply);
    apply();
  });

  // CEP: fill city, neighbourhood and state through ViaCEP. Only fills empty fields; all stay editable.
  $$("input[data-mask='cep']").forEach((cep) => {
    cep.addEventListener("blur", async () => {
      const digits = cep.value.replace(/\D/g, "");
      if (digits.length !== 8) return;
      try {
        const response = await fetch(`https://viacep.com.br/ws/${digits}/json/`);
        const data = response.ok ? await response.json() : { erro: true };
        if (data.erro) return;
        const field = (name) => cep.form.querySelector(`[name='${name}']`);
        const fill = (name, value) => {
          const input = field(name);
          if (input && value && !input.value) input.value = value;
        };
        fill("city", data.localidade);
        fill("neighborhood", data.bairro);
        const state = field("state");
        if (state && data.uf) state.value = data.uf;
        announce(`Endereço preenchido pelo CEP: ${data.localidade} - ${data.uf}.`);
      } catch (error) {
        // Offline or blocked: the person types the address.
      }
    });
  });

  // Multi-select with chips.
  if (window.TomSelect) {
    $$("select[data-enhance='tom-select']").forEach((select) => {
      const tomSelect = new window.TomSelect(select, {
        plugins: ["remove_button"],
        maxOptions: null,
        hidePlaceholder: true,
        placeholder: "Escolha uma ou mais",
        render: { no_results: () => '<div class="no-results p-3 text-ink-muted">Nada encontrado</div>' },
      });
      // The control the person types in carries the help, the errors and the invalid state.
      ["aria-describedby", "aria-invalid"].forEach((name) => {
        const value = select.getAttribute(name);
        if (value) tomSelect.control_input.setAttribute(name, value);
      });
    });
  }

  // Dialogs: [data-open-dialog="id"] opens one; [data-close-dialog] or a click on the backdrop closes it.
  $$("[data-open-dialog]").forEach((button) => {
    const dialog = document.getElementById(button.dataset.openDialog);
    if (!dialog) return;
    button.addEventListener("click", () => {
      dialog.showModal();
      button.setAttribute("aria-expanded", "true");
    });
    dialog.addEventListener("close", () => button.setAttribute("aria-expanded", "false"));
  });
  $$("dialog").forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close("cancel");
    });
    $$("[data-close-dialog]", dialog).forEach((button) => button.addEventListener("click", () => dialog.close()));
  });

  // Confirmation: forms with data-confirm ask in a dialog before submitting.
  const confirmDialog = document.getElementById("confirm-dialog");
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.dataset.confirm || form.dataset.confirmed) return;
    event.preventDefault();
    if (!confirmDialog) {
      if (window.confirm(form.dataset.confirm)) {
        form.dataset.confirmed = "1";
        form.requestSubmit();
      }
      return;
    }
    confirmDialog.querySelector("#confirm-title").textContent = form.dataset.confirmTitle || "Tem certeza?";
    confirmDialog.querySelector("#confirm-text").textContent = form.dataset.confirm;
    const ok = confirmDialog.querySelector("#confirm-ok");
    ok.textContent = form.dataset.confirmAction || "Confirmar";
    ok.className = `btn ${form.dataset.confirmTone === "primary" ? "btn-primary" : "btn-danger"}`;
    confirmDialog.querySelector("#confirm-cancel").textContent = form.dataset.confirmDismiss || "Voltar";
    confirmDialog.returnValue = "";
    confirmDialog.addEventListener(
      "close",
      () => {
        if (confirmDialog.returnValue === "ok") {
          form.dataset.confirmed = "1";
          form.requestSubmit();
        }
      },
      { once: true },
    );
    confirmDialog.showModal();
    confirmDialog.querySelector("#confirm-cancel").focus(); // the safe choice has the focus
  });

  // Busy buttons: forms with data-loading show the busy label and block a second submit.
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.hasAttribute("data-loading") || event.defaultPrevented) return;
    const button = event.submitter || form.querySelector("button[type=submit]");
    if (!button) return;
    const icon = button.querySelector("[data-pop-icon]");
    if (icon && !reduceMotion) icon.classList.add("motion-safe:animate-pop");
    // After this tick, so the browser still sends the button's name and value.
    setTimeout(() => {
      button.classList.add("is-loading");
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
    }, 0);
  });

  // Toasts: success and info hide by themselves (paused while hovered or focused); all can be closed.
  $$(".toast").forEach((toast) => {
    let timer;
    const leave = () => {
      toast.classList.add("is-leaving");
      setTimeout(() => toast.remove(), reduceMotion ? 0 : 200);
    };
    const schedule = () => {
      const delay = Number(toast.dataset.autohide);
      if (delay) timer = setTimeout(leave, delay);
    };
    toast.querySelector("[data-dismiss-toast]")?.addEventListener("click", leave);
    toast.addEventListener("mouseenter", () => clearTimeout(timer));
    toast.addEventListener("focusin", () => clearTimeout(timer));
    toast.addEventListener("mouseleave", schedule);
    toast.addEventListener("focusout", schedule);
    schedule();
  });
  // The toasts are in the page from the start, which screen readers do not announce: say them again.
  const said = $$(".toast p").map((p) => p.textContent.trim()).join(" ");
  if (said) announce(said);

  // A failed submit puts the focus on the first field that needs fixing.
  document.querySelector("form [aria-invalid='true']:not([type=hidden])")?.focus();

  // Back/forward cache: a page restored after submitting must not keep its buttons busy.
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    $$(".btn.is-loading").forEach((button) => {
      button.classList.remove("is-loading");
      button.disabled = false;
      button.removeAttribute("aria-busy");
    });
  });

  // Pet photos fade in over their placeholder once loaded. Only images not loaded yet are hidden.
  $$("img.pet-photo").forEach((img) => {
    if (img.complete) return;
    img.classList.add("is-loading");
    const done = () => {
      img.classList.remove("is-loading");
      img.classList.add("is-loaded");
    };
    img.addEventListener("load", done, { once: true });
    img.addEventListener("error", done, { once: true });
  });

  // The phone's sticky "Quero adotar" bar steps aside while the request form itself is on screen.
  const sticky = document.querySelector("[data-sticky-cta]");
  const target = document.getElementById("pedido");
  if (sticky && target && "IntersectionObserver" in window) {
    new IntersectionObserver(([entry]) => {
      sticky.classList.toggle("translate-y-full", entry.isIntersecting);
      sticky.classList.toggle("opacity-0", entry.isIntersecting);
      sticky.inert = entry.isIntersecting;
    }).observe(target);
  }

  // Board filters: on a phone they start folded unless a filter is active; the badge counts them.
  const filters = document.querySelector("details[data-filters]");
  if (filters) {
    const active = $$("select, input", filters).filter((field) => field.name && field.value.trim()).length;
    const badge = filters.querySelector("[data-filter-count]");
    if (badge && active) {
      badge.textContent = String(active);
      badge.classList.remove("hidden");
    }
    const phone = window.matchMedia("(max-width: 767px)");
    const sync = () => {
      filters.open = !phone.matches || active > 0;
    };
    sync();
    phone.addEventListener("change", sync);
  }
})();
