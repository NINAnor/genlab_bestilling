from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters import admin as unfold_filters

from .models import (
    AnalysisOrder,
    AnalysisResult,
    AnalysisType,
    Area,
    EquimentOrderQuantity,
    EquipmentBuffer,
    EquipmentOrder,
    EquipmentType,
    ExtractionOrder,
    ExtractionPlate,
    ExtractPlatePosition,
    Genrequest,
    Location,
    LocationType,
    Marker,
    Organization,
    Sample,
    SampleMarkerAnalysis,
    SampleType,
    Species,
)


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Area)
class AreaAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(LocationType)
class LocationTypeAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ["name", "river_id", "code"]
    search_fields = ["name", "river_id", "code"]
    list_filter = [("types", unfold_filters.RelatedDropdownFilter)]
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
        ("project", unfold_filters.RelatedDropdownFilter),
        ("area", unfold_filters.RelatedDropdownFilter),
        ("sample_types", unfold_filters.RelatedDropdownFilter),
        ("markers", unfold_filters.RelatedDropdownFilter),
        ("species", unfold_filters.RelatedDropdownFilter),
        ("samples_owner", unfold_filters.RelatedDropdownFilter),
        ("creator", unfold_filters.RelatedDropdownFilter),
    ]

    autocomplete_fields = [
        "samples_owner",
        "area",
        "project",
        "species",
        "sample_types",
        "markers",
    ]


@admin.register(Marker)
class MarkerAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(Species)
class SpeciesAdmin(ModelAdmin):
    list_display = ["name", "area"]
    list_filter = [("area", unfold_filters.RelatedDropdownFilter)]
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


@admin.register(EquipmentBuffer)
class EquipmentBufferAdmin(ModelAdmin):
    list_display = ["name", "unit"]
    list_filter = ["unit"]
    search_fields = ["name"]


@admin.register(EquimentOrderQuantity)
class EquimentOrderQuantityAdmin(ModelAdmin): ...


@admin.register(EquipmentOrder)
class EquipmentOrderAdmin(ModelAdmin): ...


@admin.register(ExtractionOrder)
class ExtractionOrderAdmin(ModelAdmin): ...


@admin.register(AnalysisOrder)
class AnalysisOrderAdmin(ModelAdmin): ...


@admin.register(SampleMarkerAnalysis)
class SampleMarkerAnalysisAdmin(ModelAdmin): ...


@admin.register(Sample)
class SampleAdmin(ModelAdmin):
    list_display = [
        Sample.order.field.name,
        Sample.guid.field.name,
        Sample.name.field.name,
        Sample.type.field.name,
        Sample.species.field.name,
        Sample.year.field.name,
        Sample.notes.field.name,
        Sample.pop_id.field.name,
        Sample.location.field.name,
        Sample.volume.field.name,
        Sample.genlab_id.field.name,
        Sample.parent.field.name,
    ]
    search_fields = [
        Sample.name.field.name,
        Sample.guid.field.name,
        Sample.genlab_id.field.name,
    ]
    list_filter = [
        (Sample.name.field.name, unfold_filters.FieldTextFilter),
        (Sample.guid.field.name, unfold_filters.FieldTextFilter),
        (Sample.genlab_id.field.name, unfold_filters.FieldTextFilter),
        (Sample.year.field.name, unfold_filters.SingleNumericFilter),
        (Sample.species.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (Sample.type.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
    ]
    list_filter_submit = True
    list_filter_sheet = False


@admin.register(ExtractPlatePosition)
class ExtractPlatePositionAdmin(ModelAdmin): ...


@admin.register(ExtractionPlate)
class ExtractionPlateAdmin(ModelAdmin): ...


@admin.register(AnalysisResult)
class AnalysisResultAdmin(ModelAdmin): ...
