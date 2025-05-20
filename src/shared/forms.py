from django import forms


class ActionForm(forms.Form):
    hidden = forms.CharField(required=False, widget=forms.widgets.HiddenInput())

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
