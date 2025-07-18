from typing import Any

import django_filters as filters
from dal import autocomplete
from django import forms
from django.db.models import QuerySet
from django.http import HttpRequest
from django_filters import CharFilter

from genlab_bestilling.models import (
    AnalysisOrder,
    ExtractionOrder,
    ExtractionPlate,
    Order,
    Sample,
    SampleMarkerAnalysis,
)


class AnalysisOrderFilter(filters.FilterSet):
    class Meta:
        model = AnalysisOrder
        fields = ["id", "status", "genrequest__area"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters["id"].field.label = "Order ID"
        self.filters["id"].field.widget = forms.TextInput(
            attrs={
                "class": "bg-white border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700",  # noqa: E501
                "placeholder": "Enter Order ID",
            }
        )

        self.filters["status"].field.label = "Order Status"
        self.filters["status"].field.choices = Order.OrderStatus.choices
        self.filters["status"].field.widget = autocomplete.ListSelect2(
            url="autocomplete:order-status",
            attrs={
                "class": "w-full",
            },
        )

        self.filters["genrequest__area"].field.label = "Area"
        self.filters["genrequest__area"].field.widget = autocomplete.ModelSelect2(
            url="autocomplete:area",
            attrs={
                "class": "w-full",
            },
        )


class ExtractionOrderFilter(filters.FilterSet):
    class Meta:
        model = ExtractionOrder
        fields = ["id", "status", "genrequest__area", "sample_types"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters["id"].field.label = "Order ID"
        self.filters["id"].field.widget = forms.TextInput(
            attrs={
                "class": "bg-white border border-gray-300 rounded-lg py-2 px-4 w-full text-gray-700",  # noqa: E501
                "placeholder": "Enter Order ID",
            }
        )

        self.filters["status"].field.label = "Order Status"
        self.filters["status"].field.choices = Order.OrderStatus.choices
        self.filters["status"].field.widget = autocomplete.ListSelect2(
            url="autocomplete:order-status",
            attrs={
                "class": "w-full",
            },
        )

        self.filters["genrequest__area"].field.label = "Area"
        self.filters["genrequest__area"].field.widget = autocomplete.ModelSelect2(
            url="autocomplete:area",
            attrs={
                "class": "w-full",
            },
        )

        self.filters["sample_types"].field.label = "Sample types"
        self.filters["sample_types"].field.widget = autocomplete.ModelSelect2Multiple(
            url="autocomplete:sample-type",
            attrs={
                "class": "w-full",
            },
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
    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ) -> None:
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters["sample__species"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:species"
        )
        self.filters["sample__type"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:sample-type"
        )
        self.filters["sample__location"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:location"
        )
        self.filters["marker"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:marker"
        )
        self.filters["order"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:analysis-order"
        )

    class Meta:
        model = SampleMarkerAnalysis
        fields = [
            "order",
            "marker",
            "sample__guid",
            "sample__name",
            "sample__genlab_id",
            "sample__species",
            "sample__type",
            "sample__year",
            "sample__location",
            "sample__pop_id",
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
