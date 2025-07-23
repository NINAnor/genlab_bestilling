from typing import Any

import django_filters as filters
from dal import autocomplete
from django import forms
from django.db.models import QuerySet
from django.http import HttpRequest
from django_filters import BooleanFilter, CharFilter, ChoiceFilter

from genlab_bestilling.models import (
    AnalysisOrder,
    ExtractionOrder,
    ExtractionPlate,
    Order,
    Sample,
    SampleMarkerAnalysis,
)


class AnalysisOrderFilter(filters.FilterSet):
    status = ChoiceFilter(
        field_name="status",
        label="Status",
        choices=Order.OrderStatus.choices,
        widget=forms.Select(
            attrs={
                "class": "bg-white border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700"  # noqa: E501
            },
        ),
        empty_label="",
    )

    class Meta:
        model = AnalysisOrder
        fields = [
            "id",
            "status",
            "genrequest__area",
            "responsible_staff",
            "genrequest",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters["id"].field.label = "Order ID"
        self.filters["id"].field.widget = forms.TextInput(
            attrs={
                "class": "bg-white border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700",  # noqa: E501
                "placeholder": "Enter Order ID",
            }
        )

        self.filters["genrequest__area"].field.label = "Area"
        self.filters["genrequest__area"].field.widget = autocomplete.ModelSelect2(
            url="autocomplete:area",
            attrs={
                "class": "w-full",
            },
        )

        self.filters["responsible_staff"].field.label = "Assigned Staff"
        self.filters[
            "responsible_staff"
        ].field.widget = autocomplete.ModelSelect2Multiple(
            url="autocomplete:staff-user",
            attrs={
                "class": "w-full",
            },
        )


class ExtractionOrderFilter(filters.FilterSet):
    status = ChoiceFilter(
        field_name="status",
        label="Status",
        choices=Order.OrderStatus.choices,
        widget=forms.Select(
            attrs={
                "class": "bg-white border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700"  # noqa: E501
            },
        ),
        empty_label="",
    )

    class Meta:
        model = ExtractionOrder
        fields = [
            "id",
            "status",
            "genrequest__area",
            "responsible_staff",
            "genrequest",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters["id"].field.label = "Order ID"
        self.filters["id"].field.widget = forms.TextInput(
            attrs={
                "class": "bg-white border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700",  # noqa: E501
                "placeholder": "Enter Order ID",
            }
        )

        self.filters["genrequest__area"].field.label = "Area"
        self.filters["genrequest__area"].field.widget = autocomplete.ModelSelect2(
            url="autocomplete:area",
            attrs={
                "class": "w-full",
            },
        )

        self.filters["responsible_staff"].field.label = "Assigned Staff"
        self.filters[
            "responsible_staff"
        ].field.widget = autocomplete.ModelSelect2Multiple(
            url="autocomplete:staff-user",
            attrs={"class": "select2-adjusted"},
        )


class OrderSampleFilter(filters.FilterSet):
    genlab_id = CharFilter(
        label="GenlabID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Type here",
            }
        ),
    )

    name = CharFilter(
        label="Name",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Type here",
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
            url="autocomplete:species"
        )
        self.filters["type"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:sample-type"
        )

    class Meta:
        model = Sample
        fields = [
            "genlab_id",
            "name",
            "species",
            "type",
        ]


class SampleMarkerOrderFilter(filters.FilterSet):
    sample__genlab_id = CharFilter(
        label="GenlabID",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Type here",
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

        self.filters["sample__type"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:sample-type"
        )

        self.filters["sample__isolation_method"].field.label = "Isolation method"
        self.filters[
            "sample__isolation_method"
        ].field.widget = autocomplete.ModelSelect2(
            url="autocomplete:isolation-method",
            attrs={
                "class": "w-full",
            },
        )

        self.filters["sample__extractions"].field.label = "Qiagen ID"
        self.filters["sample__extractions"].field.widget = forms.TextInput(
            attrs={
                "class": "bg-white border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700",  # noqa: E501
                "placeholder": "Enter Quiagen ID",
            }
        )

    class Meta:
        model = SampleMarkerAnalysis
        fields = [
            "sample__genlab_id",
            "sample__type",
            "sample__extractions",
            "sample__isolation_method",
            # "PCR",
            # "fluidigm",
            # "output",
        ]


class SampleFilter(filters.FilterSet):
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
            url="autocomplete:species"
        )
        self.filters["type"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:sample-type"
        )
        self.filters["location"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:location"
        )

    class Meta:
        model = Sample
        fields = [
            "name",
            "genlab_id",
            "species",
            "type",
            "year",
            "location",
            "pop_id",
            "type",
        ]


class ExtractionPlateFilter(filters.FilterSet):
    class Meta:
        model = ExtractionPlate
        fields = [
            "id",
        ]


class SampleLabFilter(filters.FilterSet):
    is_marked = BooleanFilter(
        label="Marked",
        method="filter_boolean",
        widget=forms.Select(
            choices=(
                ("", "---------"),
                ("true", "Yes"),
                ("false", "No"),
            ),
            attrs={
                "class": "w-full border border-gray-300 rounded-lg py-2 px-4 text-gray-700",  # noqa: E501
            },
        ),
    )

    is_plucked = BooleanFilter(
        label="Plucked",
        method="filter_boolean",
        widget=forms.Select(
            choices=(
                ("", "---------"),
                ("true", "Yes"),
                ("false", "No"),
            ),
            attrs={
                "class": "w-full border border-gray-300 rounded-lg py-2 px-4 text-gray-700",  # noqa: E501
            },
        ),
    )

    is_isolated = BooleanFilter(
        label="Isolated",
        method="filter_boolean",
        widget=forms.Select(
            choices=(
                ("", "---------"),
                ("true", "Yes"),
                ("false", "No"),
            ),
            attrs={
                "class": "w-full border border-gray-300 rounded-lg py-2 px-4 text-gray-700",  # noqa: E501
            },
        ),
    )

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

        self.filters["isolation_method"].field.label = "Isolation method"
        self.filters["isolation_method"].field.widget = autocomplete.ModelSelect2(
            url="autocomplete:isolation-method",
            attrs={
                "class": "w-full",
            },
        )

        self.filters["extractions"].field.label = "Qiagen ID"
        self.filters["extractions"].field.widget = forms.TextInput(
            attrs={
                "class": "bg-white border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700",  # noqa: E501
                "placeholder": "Enter Quiagen ID",
            }
        )

    class Meta:
        model = Sample
        fields = [
            "genlab_id_min",
            "genlab_id_max",
            "is_marked",
            "is_plucked",
            "is_isolated",
            "extractions",
            "isolation_method",
            # "fluidigm",
            # "output",
        ]

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
