from django.urls import path

from capps.users.autocomplete import StaffUserAutocomplete, UserAutocomplete
from genlab_bestilling.autocomplete import (
    AnalysisMarkerAutocomplete,
    AnalysisOrderAutocomplete,
    AreaAutocomplete,
    EquipmentAutocomplete,
    ExtractionOrderAutocomplete,
    GenrequestAutocomplete,
    IsolationMethodAutocomplete,
    LocationAutocomplete,
    MarkerAutocomplete,
    OrderAutocomplete,
    SampleTypeAutocomplete,
    SpeciesAutocomplete,
    StatusAutocomplete,
)
from nina.autocomplete import ProjectAutocomplete

app_name = "autocomplete"
urlpatterns = [
    path("area/", AreaAutocomplete.as_view(), name="area"),
    path("species/", SpeciesAutocomplete.as_view(), name="species"),
    path("sample-type/", SampleTypeAutocomplete.as_view(), name="sample-type"),
    path("order-status/", StatusAutocomplete.as_view(), name="order-status"),
    path("project/", ProjectAutocomplete.as_view(), name="project"),
    path("marker/", MarkerAutocomplete.as_view(), name="marker"),
    path("user/", UserAutocomplete.as_view(), name="user"),
    path("staff-user/", StaffUserAutocomplete.as_view(), name="staff-user"),
    path("genrequest/", GenrequestAutocomplete.as_view(), name="genrequest"),
    path("location/", LocationAutocomplete.as_view(), name="location"),
    path("order/", OrderAutocomplete.as_view(), name="order"),
    path("order/equipment/", EquipmentAutocomplete.as_view(), name="equipment-order"),
    path("order/analysis/", AnalysisOrderAutocomplete.as_view(), name="analysis-order"),
    path(
        "order/extraction/",
        ExtractionOrderAutocomplete.as_view(),
        name="extraction-order",
    ),
    path(
        "isolation-method/",
        IsolationMethodAutocomplete.as_view(),
        name="isolation-method",
    ),
    path(
        "analysis-marker/",
        AnalysisMarkerAutocomplete.as_view(),
        name="analysis-marker",
    ),
]
