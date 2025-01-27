import django_filters as filters
from dal import autocomplete

from ..models import AnalysisOrder, ExtractionPlate, Sample, SampleMarkerAnalysis


class AnalysisOrderFilter(filters.FilterSet):
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters["genrequest__project"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:project"
        )
        self.filters["genrequest"].extra["widget"] = autocomplete.ModelSelect2(
            url="autocomplete:genrequest"
        )

    class Meta:
        model = AnalysisOrder
        fields = [
            "id",
            "status",
            "genrequest",
            "genrequest__project",
        ]


class OrderSampleFilter(filters.FilterSet):
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
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
            # "desired_extractions",
        ]


class SampleMarkerOrderFilter(filters.FilterSet):
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
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
    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
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
            # "order",
            # "order__status",
            # "order__genrequest__project",
            "guid",
            "name",
            "genlab_id",
            "species",
            "type",
            "year",
            "location",
            "pop_id",
            "type",
            # "desired_extractions",
            "plate_positions__plate",
        ]


class ExtractionPlateFilter(filters.FilterSet):
    class Meta:
        model = ExtractionPlate
        fields = [
            "id",
        ]
