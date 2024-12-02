import django_filters as filters

from ..models import AnalysisOrder, Sample


class AnalysisOrderFilter(filters.FilterSet):
    class Meta:
        model = AnalysisOrder
        fields = [
            "id",
            "status",
            "genrequest",
            "genrequest__project",
        ]


class SampleFilter(filters.FilterSet):
    class Meta:
        model = Sample
        fields = [
            "order",
            "guid",
            "name",
            "genlab_id",
            "species",
            "type",
            "year",
            "location",
            "pop_id",
            "type",
            "desired_extractions",
        ]
