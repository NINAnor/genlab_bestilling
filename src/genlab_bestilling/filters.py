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
        return queryset.filter(species__markers__in=value)

    def filter_order_status_not(self, queryset, name, value):
        return queryset.exclude(order__status=value)


class BaseOrderFilter(filters.FilterSet):
    ext_order = filters.NumberFilter(field_name="ext_order", method="filter_ext_order")

    def filter_ext_order(self, queryset, name, value):
        return queryset.filter(extractionorder=value)


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
        return queryset.filter(analysisorder=value)


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
    class Meta:
        model = Order
        fields = ("status", "name")


class OrderEquipmentFilter(OrderFilter):
    class Meta:
        model = EquipmentOrder
        fields = ("status", "name", "needs_guid")


class OrderExtractionFilter(OrderFilter):
    class Meta:
        model = ExtractionOrder
        fields = (
            "status",
            "name",
            "species",
            "sample_types",
            "needs_guid",
            "pre_isolated",
            "return_samples",
        )


class OrderAnalysisFilter(OrderFilter):
    class Meta:
        model = AnalysisOrder
        fields = ("status", "name")
