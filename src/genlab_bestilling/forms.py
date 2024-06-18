from django import forms
from formset.collection import FormCollection
from formset.renderers.tailwind import FormRenderer
from formset.utils import FormMixin
from formset.widgets import DualSortableSelector, Selectize

from .models import (
    AnalysisOrder,
    EquimentOrderQuantity,
    EquipmentOrder,
    Marker,
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
            "species": DualSortableSelector(
                search_lookup="name_icontains", filter_by={"area": "area__id"}
            ),
            "sample_types": DualSortableSelector(search_lookup="name_icontains"),
            "analysis_types": DualSortableSelector(search_lookup="name_icontains"),
        }


class EquipmentOrderForm(FormMixin, forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

        self.fields["species"].queryset = project.species.all()
        self.fields["sample_types"].queryset = project.sample_types.all()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.project = self.project
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    class Meta:
        model = EquipmentOrder
        fields = (
            "name",
            "use_guid",
            "species",
            "sample_types",
            "notes",
            "tags",
        )
        widgets = {
            "species": DualSortableSelector(
                search_lookup="name_icontains",
            ),
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


class AnalysisOrderForm(FormMixin, forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

        self.fields["species"].queryset = project.species.all()
        self.fields["sample_types"].queryset = project.sample_types.all()
        self.fields["markers"].queryset = Marker.objects.filter(
            species__projects__id=project.id
        )

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.project = self.project
        if commit:
            obj.save()
            self.save_m2m()
        return obj

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
            "species": DualSortableSelector(
                search_lookup="name_icontains",
            ),
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
    legend = "Samples"


class SamplesCollection(FormCollection):
    samples = SampleCollection()
