"""Bootstrap classes for Django widgets, so templates render fields without per-field markup."""

from django import forms


class BootstrapForm(forms.BaseForm):
    """Base for every form of the app: each widget gets its Bootstrap class, invalid ones are marked."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # pyright: ignore[reportArgumentType] - Django's own signature
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple | forms.RadioSelect | forms.CheckboxInput):
                continue
            css = "form-select" if isinstance(widget, forms.Select) else "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()

    def full_clean(self) -> None:
        super().full_clean()
        for name in self.errors:
            self._mark_invalid(name)

    def add_error(self, field: str | None, error: object) -> None:
        """Errors a view adds after validation (a rule of the domain) are marked like the form's own."""
        super().add_error(field, error)  # pyright: ignore[reportArgumentType] - Django accepts str, list or dict
        if field is not None:
            self._mark_invalid(field)

    def _mark_invalid(self, name: str) -> None:
        if name in self.fields:
            widget = self.fields[name].widget
            if "is-invalid" not in widget.attrs.get("class", ""):
                widget.attrs["class"] = f"{widget.attrs.get('class', '')} is-invalid".strip()
            widget.attrs["aria-invalid"] = "true"
