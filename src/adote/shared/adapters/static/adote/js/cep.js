// Fills city, neighbourhood and state from the CEP, through the public ViaCEP API.
// Only a convenience: every field stays editable and the server validates all of them.
(function () {
  "use strict";

  const cep = document.querySelector("input[data-mask='cep']");
  if (!cep) {
    return;
  }
  const form = cep.form;
  const field = function (name) {
    return form.querySelector("[name='" + name + "']");
  };

  cep.addEventListener("blur", async function () {
    const digits = cep.value.replace(/\D/g, "");
    if (digits.length !== 8) {
      return;
    }
    try {
      const response = await fetch("https://viacep.com.br/ws/" + digits + "/json/");
      if (!response.ok) {
        return;
      }
      const data = await response.json();
      if (data.erro) {
        return;
      }
      const set = function (name, value) {
        const input = field(name);
        if (input && value && !input.value) {
          input.value = value;
        }
      };
      set("city", data.localidade);
      set("neighborhood", data.bairro);
      const state = field("state");
      if (state && data.uf) {
        state.value = data.uf;
      }
    } catch (error) {
      // Offline or blocked: the person types the address by hand.
    }
  });
})();
