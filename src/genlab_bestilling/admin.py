from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import (
    RelatedDropdownFilter,
)

from .models import (
    AnalysisType,
    Area,
    EquipmentType,
    Genrequest,
    Location,
    LocationType,
    Marker,
    Organization,
    SampleType,
    Species,
)


@admin.register(Area)
class AreaAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(LocationType)
class LocationTypeAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(Marker)
class MarkerAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(Species)
class SpeciesAdmin(ModelAdmin):
    list_display = ["name", "area"]
    list_filter = [("area", RelatedDropdownFilter)]
    list_filter_submit = True

    search_fields = ["name"]

    autocomplete_fields = ["markers", "area"]


@admin.register(SampleType)
class SampleTypeAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(AnalysisType)
class AnalysisTypeAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(EquipmentType)
class EquipmentTypeAdmin(ModelAdmin):
    list_display = ["name", "unit"]
    list_filter = ["unit"]
    search_fields = ["name"]


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ["name", "type", "river_id", "code"]
    search_fields = ["name", "river_id", "code"]
    list_filter = [("type", RelatedDropdownFilter)]
    list_filter_submit = True


@admin.register(Genrequest)
class GenrequestAdmin(ModelAdmin):
    list_display = [
        "project",
        "name",
        "samples_owner",
        # "sample_types",
        "area",
    ]
    search_fields = ["name"]
    list_filter_submit = True

    list_filter = [
        ("project", RelatedDropdownFilter),
        ("area", RelatedDropdownFilter),
        ("sample_types", RelatedDropdownFilter),
        ("markers", RelatedDropdownFilter),
        ("species", RelatedDropdownFilter),
        ("samples_owner", RelatedDropdownFilter),
        ("creator", RelatedDropdownFilter),
    ]

    autocomplete_fields = [
        "samples_owner",
        "area",
        "project",
        "species",
        "sample_types",
        "markers",
    ]
