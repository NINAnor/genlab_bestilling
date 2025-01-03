from collections.abc import Mapping
from typing import Any

from django import forms

# from django.core.exceptions import ValidationError
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList
from formset.renderers.tailwind import FormRenderer
from formset.utils import FormMixin
from formset.widgets import DualSortableSelector, Selectize
from nina.models import Project

from .libs.formset import ContextFormCollection
from .models import (
    AnalysisOrder,
    EquimentOrderQuantity,
    EquipmentOrder,
    Genrequest,
    Marker,
    Sample,
)


class DateInput(forms.DateInput):
    input_type = "date"


class GenrequestForm(FormMixin, forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if "project" in self.fields:
            self.fields["project"].queryset = Project.objects.filter(
                memberships=user,
            )

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.user:
            obj.creator = self.user
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    class Meta:
        model = Genrequest
        fields = (
            "project",
            "name",
            "area",
            "species",
            "samples_owner",
            "sample_types",
            "markers",
            "expected_total_samples",
            "tags",
            # "analysis_timerange",
        )
        widgets = {
            "area": Selectize(search_lookup="name_icontains"),
            "samples_owner": Selectize(search_lookup="name_icontains"),
            "project": Selectize(search_lookup="number_istartswith"),
            "species": DualSortableSelector(
                search_lookup="name_icontains",
                filter_by={"area": "area__id"},
            ),
            "sample_types": DualSortableSelector(
                search_lookup="name_icontains",
                filter_by={"area": "areas__id"},
            ),
            "markers": DualSortableSelector(
                search_lookup="name_icontains",
                filter_by={"species": "species__id"},
            ),
            # "analysis_timerange": RangeWidget(DateInput),
        }


class GenrequestEditForm(GenrequestForm):
    class Meta(GenrequestForm.Meta):
        fields = (
            "area",
            "name",
            "species",
            "sample_types",
            "markers",
            # "analysis_timerange",
            "expected_total_samples",
            "tags",
        )
        widgets = {
            **GenrequestForm.Meta.widgets,
            "area": forms.widgets.HiddenInput(),
        }

    # def clean_species(self) -> dict[str, Any]:
    #     species = self.cleaned_data.get("species")

    #     difference = set(
    #         list(self.instance.species.all().values_list("id", flat=True))
    #     ) - set(map(lambda s: s.id, species))

    #     if difference:
    #         raise ValidationError("Cannot remove old species, only add is allowed")

    #     return species

    # def clean_sample_types(self) -> dict[str, Any]:
    #     species = self.cleaned_data.get("sample_types")

    #     difference = set(
    #         list(self.instance.sample_types.all().values_list("id", flat=True))
    #     ) - set(map(lambda s: s.id, species))

    #     if difference:
    #         raise ValidationError(
    #           "Cannot remove old sample types, only add is allowed")

    #     return species

    # def clean_analysis_types(self) -> dict[str, Any]:
    #     species = self.cleaned_data.get("analysis_types")

    #     difference = set(
    #         list(self.instance.analysis_types.all().values_list("id", flat=True))
    #     ) - set(map(lambda s: s.id, species))

    #     if difference:
    #         raise ValidationError(
    #             "Cannot remove old analysis types, only add is allowed"
    #         )

    #     return species


class EquipmentOrderForm(FormMixin, forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def __init__(self, *args, genrequest, **kwargs):
        super().__init__(*args, **kwargs)
        self.genrequest = genrequest

        # self.fields["species"].queryset = genrequest.species.all()
        self.fields["sample_types"].queryset = genrequest.sample_types.all()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.genrequest = self.genrequest
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    class Meta:
        model = EquipmentOrder
        fields = (
            "name",
            "needs_guid",
            # "species",
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


YES_NO_CHOICES = ((False, "No"), (True, "Yes"))


class AnalysisOrderForm(FormMixin, forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    needs_guid = forms.TypedChoiceField(
        label="I need to generate GUID",
        help_text="Choose yes if your samples don't have already a GUID, "
        + "the system will generate a new GUID",
        coerce=lambda x: x == "True",
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect,
    )
    isolate_samples = forms.TypedChoiceField(
        label="I want samples to be isolated",
        coerce=lambda x: x == "True",
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect,
    )
    return_samples = forms.TypedChoiceField(
        label="I want samples to be returned after analysis",
        coerce=lambda x: x == "True",
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, genrequest, **kwargs):
        super().__init__(*args, **kwargs)
        self.genrequest = genrequest

        self.fields["name"].help_text = (
            "You can provide a descriptive name "
            + "for this order to help you find it later"
        )

        self.fields["species"].queryset = genrequest.species.all()
        self.fields["sample_types"].queryset = genrequest.sample_types.all()
        self.fields["markers"].queryset = Marker.objects.filter(
            species__genrequests__id=genrequest.id
        ).distinct()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.genrequest = self.genrequest
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    class Meta:
        model = AnalysisOrder
        fields = (
            "name",
            "needs_guid",
            # "species",
            # "sample_types",
            "notes",
            "tags",
            "isolate_samples",
            # "markers",
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
        self.genrequest = context["genrequest"]
        self.order_id = context["order_id"]
        self.fields["type"].queryset = self.genrequest.sample_types.all()
        self.fields["species"].queryset = self.genrequest.species.all()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.order_id = self.order_id
        obj.area = self.genrequest.area
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
