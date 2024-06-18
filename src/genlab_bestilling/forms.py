from django import forms
from django.db.utils import IntegrityError
from django.forms.models import BaseModelForm, construct_instance
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
    equipments = EquipmentOrderQuantityForm()

    def __init__(self, *args, order_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_id = order_id

    def retrieve_instance(self, data):
        if data := data.get("equipments"):
            try:
                return EquimentOrderQuantity.objects.get(id=data.get("id") or -1)
            except (AttributeError, EquimentOrderQuantity.DoesNotExist, ValueError):
                return EquimentOrderQuantity(
                    equipment_id=data.get("equipment"),
                    quantity=data.get("quantity"),
                )

    def construct_instance(self, instance=None):
        """
        Override method from:
        https://github.com/jrief/django-formset/blob/releases/1.4/formset/collection.py#L447
        """
        assert (  # noqa: S101
            self.is_valid()
        ), f"Can not construct instance with invalid collection {self.__class__} object"
        if self.has_many:
            for valid_holders in self.valid_holders:
                # first, handle holders which are forms
                for _name, holder in valid_holders.items():
                    if not isinstance(holder, BaseModelForm):
                        continue
                    if holder.marked_for_removal:
                        holder.instance.delete()
                        continue
                    construct_instance(holder, holder.instance)
                    if getattr(self, "related_field", None):
                        setattr(holder.instance, self.related_field, instance)

                    # NOTE: only added this line to inject the order id
                    holder.instance.order_id = self.order_id

                    try:
                        holder.save()
                    except (IntegrityError, ValueError) as error:
                        # some errors are caught only after attempting to save
                        holder._update_errors(error)

                # next, handle holders which are sub-collections
                for _name, holder in valid_holders.items():
                    if callable(getattr(holder, "construct_instance", None)):
                        holder.construct_instance(holder.instance)
        else:
            for name, holder in self.valid_holders.items():
                if callable(getattr(holder, "construct_instance", None)):
                    holder.construct_instance(instance)
                elif isinstance(holder, BaseModelForm):
                    opts = holder._meta
                    holder.cleaned_data = self.cleaned_data[name]
                    holder.instance = instance
                    construct_instance(holder, instance, opts.fields, opts.exclude)
                    try:
                        holder.save()
                    except IntegrityError as error:
                        holder._update_errors(error)


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
