from django_filters import rest_framework as filters

from .models import Location, Marker, Sample, SampleMarkerAnalysis, SampleType, Species


class SampleFilter(filters.FilterSet):
    class Meta:
        model = Sample
        fields = ["order", "species", "order__status"]


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
