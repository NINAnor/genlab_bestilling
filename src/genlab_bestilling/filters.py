from django_filters import rest_framework as filters

from .models import Location, Marker, Sample, SampleType, Species


class SampleFilter(filters.FilterSet):
    class Meta:
        model = Sample
        fields = ["order", "species"]


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
    class Meta:
        model = Marker
        fields = {"name": ["icontains"]}


class LocationFilter(filters.FilterSet):
    class Meta:
        model = Location
        fields = {"name": ["icontains"]}
