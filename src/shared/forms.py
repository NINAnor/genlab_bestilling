# ruff: noqa: ANN001, PLR0913
from django import forms


class ActionForm(forms.Form):
    """
    A form with an hidden field
    use this as to submit forms that don't require extra parameters
        or specific GET pages
    based on Django standard form

    NOTE: it ignores the additional kwargs provided
    """

    hidden = forms.CharField(required=False, widget=forms.widgets.HiddenInput())

    def __init__(
        self,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        initial=None,
        error_class=forms.utils.ErrorList,
        label_suffix=None,
        empty_permitted=False,
        field_order=None,
        use_required_attribute=None,
        renderer=None,
        bound_field_class=None,
        **kwargs,
    ) -> None:
        super().__init__(
            data=data,
            files=files,
            auto_id=auto_id,
            prefix=prefix,
            initial=initial,
            error_class=error_class,
            label_suffix=label_suffix,
            empty_permitted=empty_permitted,
            field_order=field_order,
            use_required_attribute=use_required_attribute,
            renderer=renderer,
            bound_field_class=bound_field_class,
        )
