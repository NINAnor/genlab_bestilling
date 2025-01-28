from dal import autocomplete
from django_filters import rest_framework as filters

from .models import (
    AnalysisOrder,
    EquipmentOrder,
    ExtractionOrder,
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
        }

    def filter_markers_in_list(self, queryset, name, value):
        if value:
            return queryset.filter(species__markers__in=value)
        return queryset

    def filter_order_status_not(self, queryset, name, value):
        if value:
            return queryset.exclude(order__status=value)
        return queryset


class BaseOrderFilter(filters.FilterSet):
    ext_order = filters.NumberFilter(field_name="ext_order", method="filter_ext_order")

    def filter_ext_order(self, queryset, name, value):
        if value:
            return queryset.filter(extractionorder=value)
        return queryset


class SampleTypeFilter(BaseOrderFilter):
    class Meta:
        model = SampleType
        fields = {"name": ["icontains"]}


class SpeciesFilter(BaseOrderFilter):
    class Meta:
        model = Species
        fields = {"name": ["icontains"]}


class MarkerFilter(BaseOrderFilter):
    analysis_order = filters.NumberFilter(
        field_name="analysis_order", method="filter_analysis_order"
    )

    class Meta:
        model = Marker
        fields = {"name": ["icontains", "istartswith"]}

    def filter_analysis_order(self, queryset, name, value):
        if value:
            return queryset.filter(analysisorder=value)
        return queryset


class LocationFilter(filters.FilterSet):
    class Meta:
        model = Location
        fields = {"name": ["icontains"]}


class SampleMarkerOrderFilter(filters.FilterSet):
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


class OrderFilter(filters.FilterSet):
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
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
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
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
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
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
