from dal import autocomplete

from .models import Marker, SampleType, Species


class SpeciesAutocomplete(autocomplete.Select2QuerySetView):
    model = Species


class SampleTypeAutocomplete(autocomplete.Select2QuerySetView):
    model = SampleType


class MarkerAutocomplete(autocomplete.Select2QuerySetView):
    model = Marker
