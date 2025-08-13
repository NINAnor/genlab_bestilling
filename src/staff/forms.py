from dal import autocomplete
from django import forms
from formset.renderers.tailwind import FormRenderer

from capps.users.models import User
from genlab_bestilling.models import Genrequest, Order


class OrderStaffForm(forms.Form):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    responsible_staff = forms.MultipleChoiceField(
        label="Ansvarlige",
        widget=forms.CheckboxSelectMultiple,
        help_text="Velg hvilke ansatte som er ansvarlige for denne bestillingen.",
        required=False,
    )

    def __init__(self, *args, order: Order | Genrequest | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["responsible_staff"].choices = self.get_all_staff()  # type: ignore[attr-defined]

        if order:
            self.fields["responsible_staff"].initial = [
                user.id for user in self.get_assigned_staff(order)
            ]

    def get_assigned_staff(self, order: Order | Genrequest) -> list[User]:
        return list(order.responsible_staff.all())

    def get_all_staff(self) -> list[tuple[int, str]]:
        return [
            (user.id, f"{user}")
            for user in User.objects.filter(groups__name="genlab").all()
        ]


class ResponsibleStaffForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput(), required=True)

    responsible_staff = forms.ModelMultipleChoiceField(
        label="",
        queryset=User.objects.filter(groups__name="genlab"),
        widget=autocomplete.ModelSelect2Multiple(
            url="autocomplete:staff-user",
            attrs={"data-placeholder": "Assign staff"},
        ),
    )

    def __init__(self, *args, order: Order | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if order:
            self.fields["id"].initial = order.id
            self.fields["responsible_staff"].initial = order.responsible_staff.all()

    class Meta:
        model = Order
        fields = (
            "id",
            "responsible_staff",
        )
