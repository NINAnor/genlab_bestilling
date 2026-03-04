from typing import Any

from dal import autocomplete
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django_filters import rest_framework as filters

from .models import (
    AnalysisOrder,
    EquipmentOrder,
    ExtractionOrder,
    Genrequest,
    Location,
    Marker,
    Order,
    Sample,
    SampleMarkerAnalysis,
    SampleType,
    Species,
)


class SampleFilter(filters.FilterSet):
    order__status__not = filters.CharFilter(method="filter_order_status_not")
    markers = filters.ModelMultipleChoiceFilter(
        method="filter_markers_in_list", queryset=Marker.objects.all()
    )
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Sample
        fields = {
            "order": ["exact"],
            "species": ["exact"],
            "order__status": ["exact"],
            "year": ["exact"],
            "type": ["exact"],
            "location": ["exact"],
            "name": ["istartswith"],
            "genlab_id": ["istartswith"],
            "guid": ["in"],
            "is_isolated": ["exact"],
            "is_invalid": ["exact"],
            "position": ["isnull"],
        }

    def filter_search(
        self,
        queryset: QuerySet,
        name: str,
        value: Any,
    ) -> QuerySet:
        if not value:
            return queryset
        return queryset.filter(Q(genlab_id__istartswith=value) | Q(guid__iexact=value))

    def filter_markers_in_list(
        self,
        queryset: QuerySet,
        name: str,
        value: Any,
    ) -> QuerySet:
        if value:
            return queryset.filter(species__markers__in=value)
        return queryset

    def filter_order_status_not(
        self,
        queryset: QuerySet,
        name: str,
        value: Any,
    ) -> QuerySet:
        if value:
            return queryset.exclude(order__status=value)
        return queryset


class BaseOrderFilter(filters.FilterSet):
    ext_order = filters.NumberFilter(field_name="ext_order", method="filter_ext_order")

    def filter_ext_order(self, queryset: QuerySet, name: str, value: Any) -> QuerySet:
        if value:
            return queryset.filter(extractionorder=value)
        return queryset


class SampleTypeFilter(BaseOrderFilter):
    class Meta:
        model = SampleType
        fields = {"name": ["icontains"]}


class SpeciesFilter(BaseOrderFilter):
    analysis_order = filters.NumberFilter(
        field_name="analysis_order", method="filter_analysis_order"
    )

    class Meta:
        model = Species
        fields = {"name": ["icontains"]}

    def filter_analysis_order(
        self,
        queryset: QuerySet,
        name: str,
        value: Any,
    ) -> QuerySet:
        if value:
            # Filter to species that have samples in this analysis order
            return queryset.filter(
                sample__samplemarkeranalysis__order_id=value
            ).distinct()
        return queryset


class MarkerFilter(BaseOrderFilter):
    analysis_order = filters.NumberFilter(
        field_name="analysis_order", method="filter_analysis_order"
    )
    analysis_type = filters.NumberFilter(field_name="analysis_type_id")

    class Meta:
        model = Marker
        fields = {"name": ["icontains", "istartswith"]}

    def filter_analysis_order(
        self,
        queryset: QuerySet,
        name: str,
        value: Any,
    ) -> QuerySet:
        if value:
            return queryset.filter(analysisorder=value)
        return queryset


class LocationFilter(filters.FilterSet):
    ext_order = filters.NumberFilter(field_name="ext_order", method="filter_ext_order")
    species = filters.NumberFilter(field_name="species", method="filter_species")
    search = filters.CharFilter(method="filter_search")

    def filter_search(self, queryset: QuerySet, name: str, value: Any) -> QuerySet:
        if value:
            return queryset.filter(
                Q(name__istartswith=value) | Q(river_id__istartswith=value)
            )
        return queryset

    def filter_ext_order(self, queryset: QuerySet, name: str, value: Any) -> QuerySet:
        if value:
            order = ExtractionOrder.objects.get(pk=value)
            if order.genrequest.area.location_mandatory:
                return queryset.exclude(types=None)
        return queryset

    def filter_species(self, queryset: QuerySet, name: str, value: Any) -> QuerySet:
        if value:
            return queryset.filter(Q(types__species=value))
        return queryset.filter(types=True)

    class Meta:
        model = Location
        fields = {"name": ["icontains"]}


class SampleMarkerOrderFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = SampleMarkerAnalysis
        fields = {
            "order": ["exact"],
            "marker": ["exact"],
            "sample__guid": ["exact", "in"],
            "sample__name": ["exact", "istartswith"],
            "sample__genlab_id": ["exact", "istartswith"],
            "sample__species": ["exact"],
            "sample__type": ["exact"],
            "sample__year": ["exact"],
            "sample__location": ["exact"],
            "sample__pop_id": ["exact"],
        }

    def filter_search(
        self,
        queryset: QuerySet,
        name: str,
        value: Any,
    ) -> QuerySet:
        if not value:
            return queryset
        return queryset.filter(
            Q(sample__genlab_id__istartswith=value) | Q(sample__guid__iexact=value)
        )


class OrderFilter(filters.FilterSet):
    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters["genrequest__project"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:project"
        )

    class Meta:
        model = Order
        fields = {
            "status": ["exact"],
            "name": ["istartswith"],
            "genrequest__project": ["exact"],
        }


class OrderEquipmentFilter(OrderFilter):
    class Meta:
        model = EquipmentOrder
        fields = {
            "status": ["exact"],
            "name": ["istartswith"],
            "genrequest__project": ["exact"],
            "needs_guid": ["exact"],
        }


class OrderExtractionFilter(OrderFilter):
    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters["species"].extra["widget"] = autocomplete.ModelSelect2Multiple(
            url="autocomplete:species"
        )
        self.filters["sample_types"].extra["widget"] = (
            autocomplete.ModelSelect2Multiple(url="autocomplete:sample-type")
        )

    class Meta:
        model = ExtractionOrder
        fields = {
            "status": ["exact"],
            "name": ["istartswith"],
            "genrequest__project": ["exact"],
            "species": ["exact"],
            "sample_types": ["exact"],
            "needs_guid": ["exact"],
            "pre_isolated": ["exact"],
            "return_samples": ["exact"],
        }


class OrderAnalysisFilter(OrderFilter):
    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters["markers"].extra["widget"] = autocomplete.ModelSelect2Multiple(
            url="autocomplete:marker"
        )

    class Meta:
        model = AnalysisOrder
        fields = {
            "status": ["exact"],
            "name": ["istartswith"],
            "markers": ["exact"],
            "genrequest__project": ["exact"],
        }


class GenrequestFilter(filters.FilterSet):
    def __init__(
        self,
        data: dict[str, Any] | None = None,
        queryset: QuerySet | None = None,
        *,
        request: HttpRequest | None = None,
        prefix: str | None = None,
    ):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters["project"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:project"
        )
        self.filters["area"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:area"
        )
        self.filters["species"].extra["widget"] = autocomplete.ModelSelect2Multiple(
            url="autocomplete:species"
        )
        self.filters["sample_types"].extra["widget"] = (
            autocomplete.ModelSelect2Multiple(url="autocomplete:sample-type")
        )

    class Meta:
        model = Genrequest
        fields = {
            "project": ["exact"],
            "name": ["istartswith"],
            "area": ["exact"],
            "species": ["exact"],
            "sample_types": ["exact"],
        }
