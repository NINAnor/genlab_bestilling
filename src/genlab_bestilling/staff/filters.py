import django_filters as filters

from ..models import AnalysisOrder, ExtractionPlate, Sample


class AnalysisOrderFilter(filters.FilterSet):
    class Meta:
        model = AnalysisOrder
        fields = [
            "id",
            "status",
            "genrequest",
            "genrequest__project",
        ]


class OrderSampleFilter(filters.FilterSet):
    class Meta:
        model = Sample
        fields = [
            # "order",
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


class SampleFilter(filters.FilterSet):
    class Meta:
        model = Sample
        fields = [
            "order",
            "order__status",
            "order__genrequest__project",
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
            "plate_positions__plate",
        ]


class ExtractionPlateFilter(filters.FilterSet):
    class Meta:
        model = ExtractionPlate
        fields = [
            "id",
        ]
