"""How every form of the app looks: Tailwind classes on the widgets, and one template per field."""

from django import forms
from django.forms.renderers import TemplatesSetting


class AdoteFormRenderer(TemplatesSetting):
    """`{{ form.field.as_field_group }}` renders label, widget, help and errors with forms/field.html."""

    field_template_name = "forms/field.html"


class StyledForm(forms.BaseForm):
    """Base for every form of the app: each widget gets its class, and invalid ones are marked."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # pyright: ignore[reportArgumentType] - Django's own signature
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput | forms.RadioSelect | forms.CheckboxSelectMultiple):
                continue
            if isinstance(widget, forms.FileInput):
                css = "sr-only"  # the visible part is the template's drop zone
            elif isinstance(widget, forms.Select):
                css = "select"
            elif isinstance(widget, forms.Textarea):
                css = "textarea"
            else:
                css = "input"
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
            self.fields[name].widget.attrs["aria-invalid"] = "true"
