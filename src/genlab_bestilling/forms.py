from django import forms
from formset.collection import FormCollection
from formset.renderers.tailwind import FormRenderer
from formset.widgets import DualSortableSelector, Selectize

from .models import (
    AnalysisOrder,
    EquimentOrderQuantity,
    EquipmentOrder,
    Project,
    Sample,
)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = (
            "number",
            "name",
            "area",
            "species",
            "sample_types",
            "analysis_types",
            "expected_total_samples",
            # "analysis_timerange",
        )
        widgets = {
            "area": Selectize(search_lookup="name_icontains"),
            "species": DualSortableSelector(search_lookup="name_icontains"),
            "sample_types": DualSortableSelector(search_lookup="name_icontains"),
            "analysis_types": DualSortableSelector(search_lookup="name_icontains"),
        }


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = EquipmentOrder
        fields = ("name", "use_guid", "species", "sample_types", "notes", "tags")
        widgets = {
            "species": DualSortableSelector(search_lookup="name_icontains"),
            "sample_types": DualSortableSelector(search_lookup="name_icontains"),
        }


class EquipmentOrderQuantityForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)

    class Meta:
        model = EquimentOrderQuantity
        fields = ("id", "equipment", "quantity")
        widgets = {
            "equipment": Selectize(search_lookup="name_icontains"),
        }


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


class AnalysisOrderForm(forms.ModelForm):
    class Meta:
        model = AnalysisOrder
        fields = (
            "name",
            "has_guid",
            "species",
            "sample_types",
            "notes",
            "tags",
            "isolate_samples",
            "markers",
            "return_samples",
        )
        widgets = {
            "species": DualSortableSelector(search_lookup="name_icontains"),
            "sample_types": DualSortableSelector(search_lookup="name_icontains"),
            "markers": DualSortableSelector(search_lookup="name_icontains"),
        }


class SampleForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)

    class Meta:
        model = Sample
        fields = (
            "id",
            "guid",
            "type",
            "species",
            "markers",
            "date",
            "notes",
            "pop_id",
            "area",
            "location",
            "volume",
        )


class SampleCollection(FormCollection):
    min_siblings = 1
    add_label = "Add sample"
    sample = SampleForm()
    related_field = "order"
    legend = "Samples"

    def retrieve_instance(self, data):
        if data := data.get("sample"):
            try:
                return self.instance.samples.get(id=data.get("id") or -1)
            except (AttributeError, Sample.DoesNotExist, ValueError):
                return Sample(**data, order=self.instance)


class AnalysisOrderCollection(FormCollection):
    order = AnalysisOrderForm()
    # samples = SampleCollection()
    default_renderer = FormRenderer(field_css_classes="mb-3")
