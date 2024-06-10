from django import forms
from formset.collection import FormCollection
from formset.renderers.tailwind import FormRenderer

from .models import EquimentOrderQuantity, EquipmentOrder


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = EquipmentOrder
        fields = ("name", "use_guid", "species", "sample_types", "notes")


class EquipmentOrderQuantityForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)

    class Meta:
        model = EquimentOrderQuantity
        fields = ("id", "equipment", "quantity")


class EquipmentQuantityCollection(FormCollection):
    min_siblings = 1
    add_label = "Add equipment"
    equipment = EquipmentOrderQuantityForm()
    related_field = "order"
    legend = "Equipments required"

    def retrieve_instance(self, data):
        if data := data.get("equipment"):
            try:
                return self.instance.equipments.get(id=data.get("id") or -1)
            except (AttributeError, EquimentOrderQuantity.DoesNotExist, ValueError):
                return EquimentOrderQuantity(
                    quantity=data.get("quantity"), order=self.instance
                )


class EquipmentOrderCollection(FormCollection):
    order = EquipmentForm()
    equipments = EquipmentQuantityCollection()
    default_renderer = FormRenderer(field_css_classes="mb-3")
