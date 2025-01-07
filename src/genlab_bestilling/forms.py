from collections.abc import Mapping
from typing import Any

from django import forms
from django.db import transaction

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
    ExtractionOrder,
    Genrequest,
    Marker,
    Order,
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
            "expected_samples_delivery_date",
            "expected_analysis_delivery_date",
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
        }


class GenrequestEditForm(GenrequestForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["area"].disabled = True

        self.fields["markers"].queryset = Marker.objects.filter(
            species__id__in=self.instance.species.all(),
        )

    class Meta(GenrequestForm.Meta):
        fields = (
            "area",
            "name",
            "species",
            "sample_types",
            "markers",
            "expected_samples_delivery_date",
            "expected_analysis_delivery_date",
            "expected_total_samples",
            "tags",
        )


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


class ExtractionOrderForm(FormMixin, forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    needs_guid = forms.TypedChoiceField(
        label="I need to generate GUID",
        help_text="Choose yes if your samples don't have already a GUID, "
        + "the system will generate a new GUID",
        coerce=lambda x: x == "True",
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect,
    )
    pre_isolated = forms.TypedChoiceField(
        label="The samples I'm delivering are already isolated"
        + " and don't require to be stored",
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
        # self.fields["markers"].queryset = Marker.objects.filter(
        #     species__genrequests__id=genrequest.id
        # ).distinct()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.genrequest = self.genrequest
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    class Meta:
        model = ExtractionOrder
        fields = (
            "name",
            "needs_guid",
            "species",
            "sample_types",
            "notes",
            "tags",
            "pre_isolated",
            "return_samples",
        )
        widgets = {
            "species": DualSortableSelector(
                search_lookup="name_icontains",
            ),
            "sample_types": DualSortableSelector(search_lookup="name_icontains"),
            # "markers": DualSortableSelector(search_lookup="name_icontains"),
        }


class AnalysisOrderForm(FormMixin, forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")
    customize_markers = forms.TypedChoiceField(
        label="Choose which markers should be run for each sample",
        help_text="By default for each species all the applicable markers will be used",
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

        self.fields["markers"].queryset = Marker.objects.filter(
            genrequest__id=genrequest.id
        ).distinct()
        self.fields["markers"].required = True
        if "from_order" in self.fields:
            self.fields["from_order"].queryset = ExtractionOrder.objects.filter(
                genrequest_id=genrequest.id,
                status=Order.OrderStatus.CONFIRMED,
            )
            self.fields["from_order"].help_text = (
                "All the samples will be included in this analysis,"
                + " for each sample the appropriate markers"
                + " among the selected will be applied. "
                "Samples that don't have an applicable marker will not included"
            )
            self.fields["from_order"].required = True

    def save(self, commit=True):
        if not commit:
            raise NotImplementedError("This form is always committed")
        with transaction.atomic():
            obj = super().save(commit=False)
            obj.genrequest = self.genrequest
            obj.save()
            self.save_m2m()
            obj.populate_from_order()
            return obj

    class Meta:
        model = AnalysisOrder
        fields = (
            "name",
            "markers",
            "customize_markers",
            "from_order",
            "notes",
            "tags",
        )
        widgets = {
            "from_order": Selectize(
                search_lookup="id", attrs={"df-show": ".customize_markers=='False'"}
            ),
            "markers": DualSortableSelector(search_lookup="name_icontains"),
        }


class AnalysisOrderUpdateForm(AnalysisOrderForm):
    class Meta(AnalysisOrderForm.Meta):
        fields = (
            "name",
            "markers",
            # "customize_markers",
            # "from_order",
            "notes",
            "tags",
        )

    def __init__(self, *args, genrequest, **kwargs):
        super().__init__(*args, genrequest=genrequest, **kwargs)
        del self.fields["customize_markers"]


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
