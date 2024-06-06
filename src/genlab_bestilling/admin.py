from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    AnalysisOrder,
    AnalysisType,
    Area,
    EquimentOrderQuantity,
    EquipmentOrder,
    EquipmentType,
    Location,
    Marker,
    Order,
    Organization,
    Project,
    Sample,
    SampleType,
    Species,
)


@admin.register(Area)
class AreaAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(Marker)
class MarkerAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(Species)
class SpeciesAdmin(ModelAdmin):
    list_display = ["name", "area"]
    list_filter = ["area"]
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
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = [
        "name",
        "number",
        "verified",
        "samples_owner",
        "area",
        "analysis_timerange",
    ]
    search_fields = ["name"]

    autocomplete_fields = [
        "samples_owner",
        "area",
        "species",
        "sample_types",
        "analysis_types",
    ]


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = [
        "id",
        "project",
    ]
    search_fields = ["id", "project"]

    autocomplete_fields = [
        "project",
        "species",
        "sample_types",
    ]


class EquimentOrderQuantityInline(admin.TabularInline):
    model = EquimentOrderQuantity
    autocomplete_fields = ["equipment"]


@admin.register(EquipmentOrder)
class EquipmentOrderAdmin(ModelAdmin):
    list_display = [
        "id",
        "project",
    ]
    search_fields = ["id", "project"]

    autocomplete_fields = [
        "project",
        "species",
        "sample_types",
    ]

    inlines = [EquimentOrderQuantityInline]


class SampleInline(admin.StackedInline):
    model = Sample
    autocomplete_fields = ["species", "markers", "area", "location", "type"]


@admin.register(AnalysisOrder)
class AnalysisOrderAdmin(ModelAdmin):
    list_display = [
        "id",
        "project",
    ]
    search_fields = ["id", "project"]
    inlines = [SampleInline]
    autocomplete_fields = ["project", "species", "sample_types", "markers"]


@admin.register(Sample)
class SampleAdmin(ModelAdmin):
    list_display = [
        "order",
        "guid",
        "type",
        "species",
    ]
    search_fields = []
    readonly_fields = ["order"]

    autocomplete_fields = ["species", "markers", "area", "location", "type"]
