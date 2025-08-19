from typing import Any

import django_filters as filters
from dal import autocomplete
from django import forms
from django.db.models import QuerySet
from django.http import HttpRequest
from django_filters import CharFilter, ChoiceFilter

from capps.users.models import User
from genlab_bestilling.models import (
    AnalysisOrder,
    AnalysisPlate,
    Area,
    EquipmentOrder,
    ExtractionOrder,
    ExtractionPlate,
    IsolationMethod,
    Marker,
    Sample,
    SampleMarkerAnalysis,
    SampleType,
    Species,
)
from nina.models import Project
from staff.mixins import HideStatusesByDefaultMixin

CUSTOM_ORDER_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("confirmed", "Not started"),
    ("processing", "Processing"),
    ("completed", "Completed"),
]


class StaticModelSelect2Multiple(autocomplete.ModelSelect2Multiple):
    def __init__(self, static_choices: list[tuple], *args: Any, **kwargs: Any) -> None:
        self.static_choices = static_choices or []
        super().__init__(*args, **kwargs)

    def filter_queryset(
        self, request: HttpRequest, term: str, queryset: QuerySet
    ) -> list:
        # Override to use static choices instead of queryset
        if term:
            return [
                choice
                for choice in self.static_choices
                if term.lower() in choice[1].lower()
            ]
        return self.static_choices

    def get_queryset(self) -> QuerySet:
        # Return empty queryset since we're using static data
        return self.model.objects.none()


class AnalysisOrderFilter(HideStatusesByDefaultMixin, filters.FilterSet):
    id = filters.CharFilter(
        field_name="id",
        label="Order ID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Order ID",
            }
        ),
    )

    status = filters.MultipleChoiceFilter(
        field_name="status",
        label="Status",
        choices=CUSTOM_ORDER_STATUS_CHOICES,
        widget=StaticModelSelect2Multiple(
            static_choices=CUSTOM_ORDER_STATUS_CHOICES,
            attrs={
                "data-placeholder": "Filter by status",
            },
        ),
    )

    genrequest__area = filters.ModelChoiceFilter(
        field_name="genrequest__area",
        label="Area",
        queryset=Area.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="autocomplete:area",
            attrs={"class": "w-full", "data-placeholder": "Filter by area"},
        ),
    )

    responsible_staff = filters.ModelMultipleChoiceFilter(
        field_name="responsible_staff",
        label="Assigned Staff",
        queryset=User.objects.filter(groups__name="genlab"),
        widget=autocomplete.ModelSelect2Multiple(
            url="autocomplete:staff-user",
            attrs={"class": "w-full", "data-placeholder": "Filter by staff"},
        ),
    )

    genrequest__species = filters.ModelChoiceFilter(
        field_name="genrequest__species",
        label="Species",
        queryset=Species.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="autocomplete:species",
            attrs={"class": "w-full", "data-placeholder": "Filter by species"},
        ),
    )

    markers = filters.ModelMultipleChoiceFilter(
        field_name="markers",
        label="Markers",
        queryset=Marker.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="autocomplete:analysis-marker",
            attrs={"class": "w-full", "data-placeholder": "Filter by markers"},
        ),
    )

    @property
    def qs(self) -> QuerySet:
        queryset = super().qs
        return self.exclude_hidden_statuses(queryset, self.data)

    class Meta:
        model = AnalysisOrder
        fields = (
            "id",
            "status",
            "genrequest__area",
            "responsible_staff",
            "genrequest__species",
            "markers",
        )


class EquipmentOrderFilter(HideStatusesByDefaultMixin, filters.FilterSet):
    id = filters.CharFilter(
        field_name="id",
        label="Order ID",
        widget=forms.TextInput(
            attrs={
                "class": "bg-white border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700",  # noqa: E501
                "placeholder": "Enter Order ID",
            }
        ),
    )

    status = filters.MultipleChoiceFilter(
        field_name="status",
        label="Status",
        choices=CUSTOM_ORDER_STATUS_CHOICES,
        widget=StaticModelSelect2Multiple(
            static_choices=CUSTOM_ORDER_STATUS_CHOICES,
            attrs={
                "data-placeholder": "Filter by status",
                "class": "border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700",  # noqa: E501
            },
        ),
    )

    genrequest__area = filters.ModelChoiceFilter(
        field_name="genrequest__area",
        label="Area",
        queryset=Area.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="autocomplete:area",
            attrs={"class": "w-full", "data-placeholder": "Filter by area"},
        ),
    )

    responsible_staff = filters.ModelMultipleChoiceFilter(
        field_name="responsible_staff",
        label="Assigned Staff",
        queryset=User.objects.filter(groups__name="genlab"),
        widget=autocomplete.ModelSelect2Multiple(
            url="autocomplete:staff-user",
            attrs={"class": "w-full", "data-placeholder": "Filter by staff"},
        ),
    )

    @property
    def qs(self) -> QuerySet:
        queryset = super().qs
        return self.exclude_hidden_statuses(queryset, self.data)

    class Meta:
        model = EquipmentOrder
        fields = (
            "id",
            "status",
            "genrequest__area",
            "responsible_staff",
        )


class ExtractionOrderFilter(HideStatusesByDefaultMixin, filters.FilterSet):
    id = CharFilter(
        field_name="id",
        label="Order ID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Order ID",
            }
        ),
    )

    status = filters.MultipleChoiceFilter(
        field_name="status",
        label="Status",
        choices=CUSTOM_ORDER_STATUS_CHOICES,
        widget=StaticModelSelect2Multiple(
            static_choices=CUSTOM_ORDER_STATUS_CHOICES,
            attrs={
                "data-placeholder": "Filter by status",
                "class": "border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700",  # noqa: E501
            },
        ),
    )

    genrequest__area = filters.ModelChoiceFilter(
        field_name="genrequest__area",
        label="Area",
        queryset=Area.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="autocomplete:area",
            attrs={"class": "w-full", "data-placeholder": "Filter by area"},
        ),
    )

    responsible_staff = filters.ModelMultipleChoiceFilter(
        field_name="responsible_staff",
        label="Assigned Staff",
        queryset=User.objects.filter(groups__name="genlab"),
        widget=autocomplete.ModelSelect2Multiple(
            url="autocomplete:staff-user",
            attrs={"class": "select2-adjusted", "data-placeholder": "Filter by staff"},
        ),
    )

    genrequest__species = filters.ModelChoiceFilter(
        field_name="genrequest__species",
        label="Species",
        queryset=Species.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="autocomplete:species",
            attrs={"class": "w-full", "data-placeholder": "Filter by species"},
        ),
    )

    @property
    def qs(self) -> QuerySet:
        queryset = super().qs
        return self.exclude_hidden_statuses(queryset, self.data)

    class Meta:
        model = ExtractionOrder
        fields = (
            "id",
            "status",
            "genrequest__area",
            "responsible_staff",
            "genrequest__species",
        )


class OrderSampleFilter(filters.FilterSet):
    genlab_id = CharFilter(
        label="GenlabID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Genlab ID",
            }
        ),
    )

    name = CharFilter(
        label="Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter name",
            }
        ),
    )

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters["species"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:species",
            attrs={"data-placeholder": "Filter by species"},
        )
        self.filters["type"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:sample-type",
            attrs={"data-placeholder": "Filter by sample type"},
        )

    class Meta:
        model = Sample
        fields = (
            "genlab_id",
            "name",
            "species",
            "type",
        )


class SampleMarkerOrderFilter(filters.FilterSet):
    sample__genlab_id = CharFilter(
        label="GenlabID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Type here",
            }
        ),
    )

    sample__isolation_method = filters.ModelMultipleChoiceFilter(
        field_name="sample__isolation_method",
        queryset=IsolationMethod.objects.all(),
        label="Isolation method",
        widget=autocomplete.ModelSelect2Multiple(
            url="autocomplete:isolation-method",
            attrs={"class": "w-full", "data-placeholder": "Filter by isolation method"},
        ),
    )

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)

        self.filters["sample__type"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:sample-type",
            attrs={"data-placeholder": "Filter by sample type"},
        )

    class Meta:
        model = SampleMarkerAnalysis
        fields = (
            "sample__genlab_id",
            "sample__type",
            "sample__isolation_method",
            # "PCR",
            # "fluidigm",
            # "output",
        )


class SampleStatusWidget(forms.Select):
    def __init__(self, attrs: dict[str, Any] | None = None):
        choices = (
            ("", "Status"),
            ("marked", "Marked"),
            ("plucked", "Plucked"),
            ("isolated", "Isolated"),
        )
        super().__init__(choices=choices, attrs=attrs)


def filter_sample_status(
    filter_set: Any, queryset: QuerySet, name: Any, value: str
) -> QuerySet:
    if value == "marked":
        # Only marked, not plucked or isolated
        return queryset.filter(is_marked=True, is_plucked=False, is_isolated=False)
    if value == "plucked":
        # Plucked but not isolated
        return queryset.filter(is_plucked=True, is_isolated=False)
    if value == "isolated":
        # All isolated samples, regardless of others
        return queryset.filter(is_isolated=True)
    return queryset


class SampleFilter(filters.FilterSet):
    filter_sample_status = filter_sample_status

    sample_status = filters.CharFilter(
        label="Sample Status",
        method="filter_sample_status",
        widget=SampleStatusWidget,
    )
    name = CharFilter(
        label="Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter name",
            }
        ),
    )
    genlab_id = CharFilter(
        label="Genlab ID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Genlab ID",
            }
        ),
    )
    year = CharFilter(
        label="Year",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter year",
            }
        ),
    )
    pop_id = CharFilter(
        label="Pop ID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Pop ID",
            }
        ),
    )

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters["species"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:species",
            attrs={"data-placeholder": "Filter by species"},
        )
        self.filters["type"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:sample-type",
            attrs={"data-placeholder": "Filter by sample type"},
        )
        self.filters["location"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:location",
            attrs={"data-placeholder": "Filter by location"},
        )

    class Meta:
        model = Sample
        fields = (
            "name",
            "genlab_id",
            "species",
            "type",
            "year",
            "location",
            "pop_id",
            "sample_status",
        )


# class ExtractionPlateFilter(filters.FilterSet):
#     class Meta:
#         model = ExtractionPlate
#         fields = ("id",)


class SampleLabFilter(filters.FilterSet):
    filter_sample_status = filter_sample_status

    genlab_id_min = ChoiceFilter(
        label="Genlab ID (From)",
        method="filter_genlab_id_range",
        empty_label="Select lower bound",
    )

    genlab_id_max = ChoiceFilter(
        label="Genlab ID (To)",
        method="filter_genlab_id_range",
        empty_label="Select upper bound",
    )

    sample_status = filters.CharFilter(
        label="Sample Status",
        method="filter_sample_status",
        widget=SampleStatusWidget,
    )

    isolation_method = filters.ModelMultipleChoiceFilter(
        field_name="isolation_method",
        queryset=IsolationMethod.objects.all(),
        label="Isolation method",
        widget=autocomplete.ModelSelect2Multiple(
            url="autocomplete:isolation-method",
            attrs={"class": "w-full", "data-placeholder": "Filter by isolation method"},
        ),
    )

    type = filters.ModelMultipleChoiceFilter(
        field_name="type",
        queryset=SampleType.objects.all(),
        label="Sample type",
        widget=autocomplete.ModelSelect2Multiple(
            url="autocomplete:sample-type",
            attrs={"class": "w-full", "data-placeholder": "Filter by sample type"},
        ),
    )

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)

        # Get all unique genlab IDs from current queryset, ordered
        genlab_ids = (
            queryset.values_list("genlab_id", flat=True)
            .distinct()
            .order_by("genlab_id")
            if queryset is not None
            else []
        )

        genlab_choices = [(gid, gid) for gid in genlab_ids]

        self.filters["genlab_id_min"].field.choices = genlab_choices
        self.filters["genlab_id_min"].field.widget.attrs.update(
            {"class": "w-full border border-gray-300 rounded-lg py-2 px-4"}
        )

        self.filters["genlab_id_max"].field.choices = genlab_choices
        self.filters["genlab_id_max"].field.widget.attrs.update(
            {"class": "w-full border border-gray-300 rounded-lg py-2 px-4"}
        )

    class Meta:
        model = Sample
        fields = (
            "genlab_id_min",
            "genlab_id_max",
            "sample_status",
            "isolation_method",
            # "fluidigm",
            # "output",
        )

    def filter_genlab_id_range(
        self, queryset: QuerySet, name: str, value: Any
    ) -> QuerySet:
        # This method is a placeholder; we apply the range in 'filter_queryset'
        # Don't remove it as it is needed for the filter to work correctly
        return queryset

    def filter_boolean(self, queryset: QuerySet, name: str, value: Any) -> QuerySet:
        val = self.data.get(name)
        if str(val) == "true":
            return queryset.filter(**{name: True})
        if str(val) == "false":
            return queryset.filter(**{name: False})

        return queryset

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        queryset = super().filter_queryset(queryset)

        genlab_min = self.data.get("genlab_id_min")
        genlab_max = self.data.get("genlab_id_max")

        if genlab_min:
            queryset = queryset.filter(genlab_id__gte=genlab_min)

        if genlab_max:
            queryset = queryset.filter(genlab_id__lte=genlab_max)

        return queryset


class ProjectFilter(filters.FilterSet):
    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        if not data or not any(data.values()):
            data = {"active": "True"}

        super().__init__(data, queryset, request=request, prefix=prefix)

    number = CharFilter(
        field_name="number",
        lookup_expr="startswith",
        label="Project number starts with",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter project number",
            }
        ),
    )

    name = CharFilter(
        field_name="name",
        lookup_expr="istartswith",
        label="Project name starts with",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter project name",
            }
        ),
    )

    verified_at = filters.ChoiceFilter(
        field_name="verified_at",
        label="Verified",
        choices=[
            ("True", "Yes"),
            ("False", "No"),
        ],
        method="filter_verified_at",
        widget=forms.Select(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    active = filters.ChoiceFilter(
        field_name="active",
        label="Active",
        choices=[
            ("True", "Yes"),
            ("False", "No"),
        ],
        widget=forms.Select(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    def filter_verified_at(self, queryset: QuerySet, name: str, value: Any) -> QuerySet:
        return queryset.filter(verified_at__isnull=(value == "False"))

    class Meta:
        model = Project
        fields = ()


class ExtractionPlateFilter(filters.FilterSet):
    qiagen_id = CharFilter(
        field_name="qiagen_id",
        lookup_expr="icontains",
        label="Qiagen ID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Qiagen ID",
            }
        ),
    )

    freezer_id = CharFilter(
        field_name="freezer_id",
        lookup_expr="istartswith",
        label="Freezer ID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Freezer ID",
            }
        ),
    )

    shelf_id = CharFilter(
        field_name="shelf_id",
        lookup_expr="istartswith",
        label="Shelf ID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter Shelf ID",
            }
        ),
    )

    positions__sample_raw__genlab_id = CharFilter(
        field_name="positions__sample_raw__genlab_id",
        lookup_expr="istartswith",
        label="Sample Genlab ID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Sample Genlab ID starts with",
            }
        ),
    )

    positions__sample_raw__name = CharFilter(
        field_name="positions__sample_raw__name",
        lookup_expr="istartswith",
        label="Sample Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Sample name starts with",
            }
        ),
    )

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters["positions__sample_raw__species"].extra["widget"] = (
            autocomplete.ModelSelect2(
                url="autocomplete:species",
                attrs={"data-placeholder": "Filter by species"},
            )
        )
        self.filters["positions__sample_raw__type"].extra["widget"] = (
            autocomplete.ModelSelect2(
                url="autocomplete:sample-type",
                attrs={"data-placeholder": "Filter by sample type"},
            )
        )
        self.filters["positions__sample_raw__order"].extra["widget"] = (
            autocomplete.ModelSelect2(
                url="autocomplete:extraction-order",
                attrs={"data-placeholder": "Filter by extraction order"},
            )
        )
        self.filters["positions__sample_raw__species"].label = "Sample Species"
        self.filters["positions__sample_raw__type"].label = "Sample Type"
        self.filters["positions__sample_raw__order"].label = "Sample Order"

    class Meta:
        model = ExtractionPlate
        fields = [
            "qiagen_id",
            "freezer_id",
            "shelf_id",
            "positions__sample_raw__genlab_id",
            "positions__sample_raw__name",
            "positions__sample_raw__species",
            "positions__sample_raw__type",
            "positions__sample_raw__order",
        ]


class AnalysisPlateFilter(filters.FilterSet):
    name = CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label="Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Enter plate name",
            }
        ),
    )

    analysis_date = filters.DateFromToRangeFilter(
        field_name="analysis_date",
        label="Analysis Date",
        widget=filters.widgets.RangeWidget(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    class Meta:
        model = AnalysisPlate
        fields = ["id", "name", "analysis_date"]
