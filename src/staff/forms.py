from django import forms
from django.forms import ModelForm
from formset.renderers.tailwind import FormRenderer

from capps.users.models import User
from genlab_bestilling.models import ExtractionPlate, Order


class ExtractionPlateForm(ModelForm):
    class Meta:
        model = ExtractionPlate
        fields = ("name",)


class OrderStaffForm(forms.Form):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    responsible_staff = forms.MultipleChoiceField(
        label="Ansvarlige",
        widget=forms.CheckboxSelectMultiple,
        help_text="Velg hvilke ansatte som er ansvarlige for denne bestillingen.",
        required=False,
    )

    def __init__(self, *args, order: Order | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["responsible_staff"].choices = self.get_all_staff()

        if order:
            self.fields["responsible_staff"].initial = [
                user.id for user in self.get_assigned_staff(order)
            ]

    def get_assigned_staff(self, order: Order) -> list[User]:
        return list(order.responsible_staff.all())

    def get_all_staff(self) -> list[tuple[int, str]]:
        return [
            (user.id, f"{user.first_name} {user.last_name}")
            for user in User.objects.filter(groups__name="genlab").all()
        ]
