from django.urls import path
from genlab_bestilling.autocomplete import (
    MarkerAutocomplete,
    SampleTypeAutocomplete,
    SpeciesAutocomplete,
)
from nina.autocomplete import ProjectAutocomplete

app_name = "autocomplete"
urlpatterns = [
    path("species/", SpeciesAutocomplete.as_view(), name="species"),
    path("sample-type/", SampleTypeAutocomplete.as_view(), name="sample-type"),
    path("project/", ProjectAutocomplete.as_view(), name="project"),
    path("marker/", MarkerAutocomplete.as_view(), name="marker"),
]
