from dal import autocomplete

from .models import (
    AnalysisOrder,
    EquipmentOrder,
    ExtractionOrder,
    Genrequest,
    Location,
    Marker,
    Order,
    SampleType,
    Species,
)


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
