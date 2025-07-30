from dal import autocomplete
from django.http import HttpRequest, JsonResponse

from .models import (
    AnalysisOrder,
    Area,
    EquipmentOrder,
    ExtractionOrder,
    Genrequest,
    IsolationMethod,
    Location,
    Marker,
    Order,
    SampleType,
    Species,
)


class AreaAutocomplete(autocomplete.Select2QuerySetView):
    model = Area


class StatusAutocomplete(autocomplete.Select2QuerySetView):
    class Params:
        q = "q"

    def get(self, request: "HttpRequest", *args, **kwargs) -> JsonResponse:
        term = request.GET.get(self.Params.q, "").lower()
        results = [
            {"id": choice[0], "text": choice[1]}
            for choice in Order.OrderStatus.choices
            if term in choice[1].lower()
        ]
        return JsonResponse({"results": results})


class SpeciesAutocomplete(autocomplete.Select2QuerySetView):
    model = Species


class SampleTypeAutocomplete(autocomplete.Select2QuerySetView):
    model = SampleType


class MarkerAutocomplete(autocomplete.Select2QuerySetView):
    model = Marker


class GenrequestAutocomplete(autocomplete.Select2QuerySetView):
    model = Genrequest


class LocationAutocomplete(autocomplete.Select2QuerySetView):
    model = Location


class OrderAutocomplete(autocomplete.Select2QuerySetView):
    model = Order


class EquipmentAutocomplete(autocomplete.Select2QuerySetView):
    model = EquipmentOrder


class AnalysisOrderAutocomplete(autocomplete.Select2QuerySetView):
    model = AnalysisOrder


class ExtractionOrderAutocomplete(autocomplete.Select2QuerySetView):
    model = ExtractionOrder


class IsolationMethodAutocomplete(autocomplete.Select2QuerySetView):
    model = IsolationMethod


class AnalysisMarkerAutocomplete(autocomplete.Select2QuerySetView):
    model = Marker
