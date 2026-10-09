// Behaviour shared by every page: input masks and the enhanced multi-select.
// Loaded with `defer`, after jQuery and its plugins, so the DOM is ready when this runs.
(function () {
  "use strict";

  const $ = window.jQuery;
  if (!$) {
    return;
  }

  // (00) 0000-0000 for landlines, (00) 00000-0000 for mobiles: the mask follows the typed length.
  const phoneMask = function (value) {
    return value.replace(/\D/g, "").length === 11 ? "(00) 00000-0000" : "(00) 0000-00009";
  };
  $("input[data-mask='phone']").mask(phoneMask, {
    onKeyPress: function (value, event, field, options) {
      field.mask(phoneMask.apply({}, arguments), options);
    },
  });
  $("input[data-mask='cep']").mask("00000-000");

  if ($.fn.select2) {
    $("select[data-enhance='select2']").select2({ width: "100%" });
  }
})();

// Forms that destroy or decide something ask first. The text lives in the form's data-confirm.
document.addEventListener("submit", function (event) {
  const question = event.target.dataset && event.target.dataset.confirm;
  if (question && !window.confirm(question)) {
    event.preventDefault();
  }
});
