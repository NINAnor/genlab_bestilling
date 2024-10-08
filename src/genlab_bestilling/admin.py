from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    RelatedDropdownFilter,
)

from .models import (
    AnalysisOrder,
    AnalysisType,
    Area,
    EquimentOrderQuantity,
    EquipmentOrder,
    EquipmentType,
    Genrequest,
    Location,
    LocationType,
    Marker,
    Organization,
    Sample,
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
        "analysis_timerange",
    ]
    search_fields = ["name"]
    list_filter_submit = True

    list_filter = [
        ("project", RelatedDropdownFilter),
        ("area", RelatedDropdownFilter),
        ("sample_types", RelatedDropdownFilter),
        ("analysis_types", RelatedDropdownFilter),
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
        "analysis_types",
    ]


class EquimentOrderQuantityInline(TabularInline):
    model = EquimentOrderQuantity
    hide_title = True
    autocomplete_fields = ["equipment"]


@admin.register(EquipmentOrder)
class EquipmentOrderAdmin(ModelAdmin):
    list_display = [
        "id",
        "name",
        "genrequest",
        "status",
    ]
    search_fields = ["id", "name", "genrequest__id"]
    autocomplete_fields = ["genrequest", "species", "sample_types"]
    list_filter = [
        ("genrequest", RelatedDropdownFilter),
        "status",
        ("species", RelatedDropdownFilter),
    ]
    list_filter_submit = True

    inlines = [EquimentOrderQuantityInline]


class SampleInline(TabularInline):
    model = Sample
    tab = True
    autocomplete_fields = ["species", "location", "type"]
    hide_title = True


@admin.register(AnalysisOrder)
class AnalysisOrderAdmin(ModelAdmin):
    list_display = [
        "id",
        "name",
        "genrequest",
        "status",
        "isolate_samples",
        "return_samples",
    ]
    search_fields = ["id", "name", "genrequest__id"]
    inlines = [SampleInline]
    autocomplete_fields = ["genrequest", "species", "sample_types", "markers"]
    list_filter = [
        ("genrequest", RelatedDropdownFilter),
        "status",
        "isolate_samples",
        "return_samples",
        ("species", RelatedDropdownFilter),
    ]
    list_filter_submit = True


@admin.register(Sample)
class SampleAdmin(ModelAdmin):
    list_display = [
        "order",
        "name",
        "guid",
        "type",
        "species",
        "pop_id",
        "location",
        "year",
    ]
    search_fields = ["name", "guid", "order__id", "id"]
    readonly_fields = ["order"]
    list_filter = [
        ("order", RelatedDropdownFilter),
        ("type", RelatedDropdownFilter),
        ("species", RelatedDropdownFilter),
        ("location", RelatedDropdownFilter),
    ]
    list_filter_submit = True

    autocomplete_fields = ["species", "location", "type"]
