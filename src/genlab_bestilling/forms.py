from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from formset.renderers.tailwind import FormRenderer
from formset.utils import FormMixin
from formset.widgets import DualSortableSelector, Selectize, TextInput

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

    def __init__(self, *args, user=None, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if "project" in self.fields:
            self.fields[
                "project"
            ].queryset = Project.objects.filter_selectable().filter(
                memberships=user,
            )

            self.fields["project"].initial = project

        self.fields[
            "markers"
        ].help_text = "If you do not know which markers to use, add all"

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
        fields = [
            "project",
            "name",
            "area",
            "species",
            "samples_owner",
            "sample_types",
            "markers",
            "expected_total_samples",
            "expected_samples_delivery_date",
            "expected_analysis_delivery_date",
        ]
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
            "expected_analysis_delivery_date": DateInput(),
            "expected_samples_delivery_date": DateInput(),
        }


class GenrequestEditForm(GenrequestForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["area"].disabled = True

        self.fields["markers"].queryset = Marker.objects.filter(
            species__id__in=self.instance.species.all(),
        )

    class Meta(GenrequestForm.Meta):
        fields = [
            "area",
            "name",
            "species",
            "sample_types",
            "markers",
            "expected_samples_delivery_date",
            "expected_analysis_delivery_date",
            "expected_total_samples",
        ]


class EquipmentOrderForm(FormMixin, forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def __init__(self, *args, genrequest, **kwargs):
        super().__init__(*args, **kwargs)
        self.genrequest = genrequest

        self.fields["is_urgent"].label = "Check this box if the order is urgent"
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
            "is_urgent",
        )
        widgets = {
            # "species": DualSortableSelector(
            #     search_lookup="name_icontains",
            # ),
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

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data["equipment"] and not cleaned_data["buffer"]:
            raise ValidationError("Equipment and/or Buffer should be filled")

    class Meta:
        model = EquimentOrderQuantity
        fields = ("id", "equipment", "buffer", "buffer_quantity", "quantity")
        widgets = {
            "equipment": Selectize(search_lookup="name_icontains"),
            "buffer": Selectize(search_lookup="name_icontains"),
            "buffer_quantity": TextInput(
                attrs={
                    "df-show": ".buffer!=''",
                    "required": ".buffer!=''",
                }
            ),
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
                    buffer_id=data.get("buffer"),
                    buffer_quantity=data.get("buffer_quantity"),
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
        + " (but not stored in the new database)",
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
        self.fields["is_urgent"].label = "Check this box if the order is urgent"

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
            "is_urgent",
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
    use_all_samples = forms.TypedChoiceField(
        label="Analyze all samples in an extraction order",
        help_text="Select <<No>> if you want to select markers individually"  # noqa: S608
        + " for each sample, or search for DNA-extracts from the Biobank",
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
        self.fields["is_urgent"].label = "Check this box if the order is urgent"

        self.fields["markers"].queryset = Marker.objects.filter(
            genrequest__id=genrequest.id
        ).distinct()
        self.fields["markers"].required = True
        if "from_order" in self.fields:
            self.fields["from_order"].queryset = ExtractionOrder.objects.filter(
                genrequest_id=genrequest.id,
            ).exclude(status=Order.OrderStatus.DRAFT)
            self.fields["from_order"].help_text = (
                "If Yes: all samples will be included in the analysis, "
                + " choose the markers below."
                + " If No: choose markers below and continue"
                + " with the sample selection by pressing Submit"
            )

    def save(self, commit=True):
        if not commit:
            raise NotImplementedError("This form is always committed")
        with transaction.atomic():
            obj = super().save(commit=False)
            obj.genrequest = self.genrequest

            if not self.cleaned_data["use_all_samples"]:
                obj.from_order = None

            if obj.from_order and not obj.name and obj.from_order.name:
                obj.name = obj.from_order.name + " - Analysis"
            obj.save()
            self.save_m2m()
            obj.populate_from_order()
            return obj

    def clean(self):
        cleaned_data = super().clean()

        if "use_all_samples" in cleaned_data and "from_order" in cleaned_data:
            if cleaned_data["use_all_samples"] and not cleaned_data["from_order"]:
                raise ValidationError("An extraction order must be selected")

    field_order = [
        "name",
        "use_all_samples",
        "from_order",
        "markers",
        "notes",
        "tags",
    ]

    class Meta:
        model = AnalysisOrder
        fields = [
            "name",
            "from_order",
            "markers",
            "notes",
            "expected_delivery_date",
            "tags",
            "is_urgent",
        ]
        widgets = {
            "name": TextInput(
                attrs={"df-show": ".from_order==''||.use_all_samples=='False'"}
            ),
            "from_order": Selectize(
                search_lookup="id",
                attrs={
                    "df-show": ".use_all_samples=='True'",
                },
            ),
            "markers": DualSortableSelector(search_lookup="name_icontains"),
            "expected_delivery_date": DateInput(),
        }


class AnalysisOrderUpdateForm(AnalysisOrderForm):
    class Meta(AnalysisOrderForm.Meta):
        fields = [
            "name",
            "markers",
            # "from_order",
            "notes",
            "expected_delivery_date",
            "tags",
            "is_urgent",
        ]

    def __init__(self, *args, genrequest, **kwargs):
        super().__init__(*args, genrequest=genrequest, **kwargs)
        self.fields["is_urgent"].label = "Check this box if the order is urgent"
        if "use_all_samples" in self.fields:
            del self.fields["use_all_samples"]
