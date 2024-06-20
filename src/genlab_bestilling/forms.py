from collections.abc import Mapping
from typing import Any

from django import forms
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList
from formset.renderers.tailwind import FormRenderer
from formset.utils import FormMixin
from formset.widgets import DateInput, DualSortableSelector, Selectize

from .libs.formset import ContextFormCollection
from .models import (
    AnalysisOrder,
    EquimentOrderQuantity,
    EquipmentOrder,
    Marker,
    Project,
    Sample,
)


class ProjectForm(FormMixin, forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

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
                search_lookup="name_icontains",
                filter_by={"area": "area__id"},
                attrs={"df-hide": ".area==''"},
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

    def reinit(self, context):
        self.order_id = context["order_id"]

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.order_id = self.order_id
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    class Meta:
        model = EquimentOrderQuantity
        fields = ("id", "equipment", "quantity")
        widgets = {
            "equipment": Selectize(search_lookup="name_icontains"),
        }


class EquipmentQuantityCollection(ContextFormCollection):
    min_siblings = 1
    add_label = "Add equipment"
    equipments = EquipmentOrderQuantityForm()
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def retrieve_instance(self, data):
        if data := data.get("equipments"):
            try:
                return EquimentOrderQuantity.objects.get(id=data.get("id") or -1)
            except (AttributeError, EquimentOrderQuantity.DoesNotExist, ValueError):
                return EquimentOrderQuantity(
                    equipment_id=data.get("equipment"),
                    quantity=data.get("quantity"),
                )

    def update_holder_instances(self, name, holder):
        if name == "equipments":
            holder.reinit(self.context)


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

    def reinit(self, context):
        self.project = context["project"]
        self.order_id = context["order_id"]
        self.fields["type"].queryset = self.project.sample_types.all()
        self.fields["species"].queryset = self.project.species.all()
        self.fields["markers"].queryset = Marker.objects.filter(
            species__projects__id=self.project.id
        )

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.order_id = self.order_id
        obj.area = self.project.area
        if commit:
            obj.save()
            self.save_m2m()
        return obj

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
            "location",
            "volume",
        )

        widgets = {
            "species": Selectize(
                search_lookup="name_icontains",
            ),
            "location": Selectize(search_lookup="name_icontains"),
            "type": Selectize(search_lookup="name_icontains"),
            "markers": Selectize(search_lookup="name_icontains"),
            "date": DateInput(),
            "notes": forms.widgets.Textarea(attrs={"rows": 1, "cols": 10}),
        }


class SamplesCollection(ContextFormCollection):
    min_siblings = 1
    add_label = "Add sample"
    samples = SampleForm()
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def update_holder_instances(self, name, holder):
        if name == "samples":
            holder.reinit(self.context)

    def retrieve_instance(self, data):
        if data := data.get("samples"):
            try:
                return Sample.objects.get(id=data.get("id") or -1)
            except (AttributeError, Sample.DoesNotExist, ValueError):
                return Sample(
                    guid=data.get("guid"),
                    type_id=data.get("type"),
                    species_id=data.get("species"),
                    date=data.get("date"),
                    notes=data.get("notes"),
                    pop_id=data.get("pop_id"),
                    location_id=data.get("location"),
                    volume=data.get("volume"),
                )


class ActionForm(forms.Form):
    hidden = forms.CharField(required=False, widget=forms.widgets.HiddenInput())

    def __init__(
        self,
        data: Mapping[str, Any] | None,
        files: Mapping[str, Any] | None,
        auto_id: bool | str | None = None,
        prefix: str | None = None,
        initial: Mapping[str, Any] | None = None,
        error_class: type[ErrorList] = None,
        label_suffix: str | None = None,
        empty_permitted: bool = None,
        field_order: list[str] | None = None,
        use_required_attribute: bool | None = None,
        renderer: type[BaseRenderer] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            data,
            files,
            auto_id,
            prefix,
            initial,
            error_class,
            label_suffix,
            empty_permitted,
            field_order,
            use_required_attribute,
            renderer,
        )
