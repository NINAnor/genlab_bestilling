from django_filters import rest_framework as filters

from .models import Marker, Sample, SampleType, Species


class SampleFilter(filters.FilterSet):
    class Meta:
        model = Sample
        fields = ["order", "species"]


class BaseOrderFilter(filters.FilterSet):
    order = filters.NumberFilter(field_name="order", method="filter_order")

    def filter_order(self, queryset, name, value):
        print(value, name)
        return queryset.filter(orders__id=value)


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
