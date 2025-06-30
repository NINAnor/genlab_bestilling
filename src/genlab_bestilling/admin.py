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
    search_fields = ["name", "project__name"]
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
class EquipmentOrderAdmin(ModelAdmin):
    EO = EquipmentOrder
    list_filter_submit = True

    list_display = [
        EO.name.field.name,
        EO.genrequest.field.name,
        EO.status.field.name,
        EO.is_urgent.field.name,
        EO.needs_guid.field.name,
        EO.contact_person.field.name,
        EO.contact_email.field.name,
        EO.confirmed_at.field.name,
        EO.last_modified_at.field.name,
        EO.created_at.field.name,
    ]
    filter_horizontal = [
        EO.sample_types.field.name,
    ]

    search_help_text = "Search for equipment name or id"
    search_fields = [
        EO.name.field.name,
        EO.id.field.name,
    ]
    list_filter = [
        (EO.sample_types.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (EO.genrequest.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        EO.status.field.name,
        EO.is_urgent.field.name,
        (EO.contact_person.field.name, unfold_filters.FieldTextFilter),
        (EO.contact_email.field.name, unfold_filters.FieldTextFilter),
        EO.needs_guid.field.name,
        EO.confirmed_at.field.name,
        EO.last_modified_at.field.name,
        EO.created_at.field.name,
    ]


@admin.register(ExtractionOrder)
class ExtractionOrderAdmin(ModelAdmin):
    EO = ExtractionOrder
    list_filter_submit = True

    list_display = [
        EO.name.field.name,
        EO.genrequest.field.name,
        EO.status.field.name,
        EO.internal_status.field.name,
        EO.needs_guid.field.name,
        EO.return_samples.field.name,
        EO.pre_isolated.field.name,
        EO.confirmed_at.field.name,
        EO.last_modified_at.field.name,
        EO.created_at.field.name,
    ]
    filter_horizontal = [
        EO.species.field.name,
        EO.sample_types.field.name,
    ]

    search_help_text = "Search for extraction name or id"
    search_fields = [
        EO.name.field.name,
        EO.id.field.name,
    ]
    list_filter = [
        (EO.species.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (EO.sample_types.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (EO.genrequest.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        EO.status.field.name,
        EO.internal_status.field.name,
        EO.needs_guid.field.name,
        EO.return_samples.field.name,
        EO.pre_isolated.field.name,
        EO.confirmed_at.field.name,
        EO.last_modified_at.field.name,
        EO.created_at.field.name,
    ]


@admin.register(AnalysisOrder)
class AnalysisOrderAdmin(ModelAdmin):
    AO = AnalysisOrder
    list_filter_submit = True

    list_display = [
        AO.name.field.name,
        AO.genrequest.field.name,
        AO.status.field.name,
        AO.from_order.field.name,
        AO.expected_delivery_date.field.name,
        AO.confirmed_at.field.name,
        AO.last_modified_at.field.name,
        AO.created_at.field.name,
    ]
    filter_horizontal = [
        AO.markers.field.name,
    ]

    search_help_text = "Search for analysis name"
    search_fields = [
        AO.name.field.name,
    ]
    list_filter = [
        (AO.samples.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (AO.markers.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (AO.genrequest.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (AO.from_order.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        AO.status.field.name,
        AO.expected_delivery_date.field.name,
        AO.confirmed_at.field.name,
        AO.last_modified_at.field.name,
        AO.created_at.field.name,
    ]


@admin.register(SampleMarkerAnalysis)
class SampleMarkerAnalysisAdmin(ModelAdmin): ...


@admin.register(Sample)
class SampleAdmin(ModelAdmin):
    list_display = [
        "__str__",
        Sample.name.field.name,
        Sample.genlab_id.field.name,
        Sample.guid.field.name,
        "fish_id",
        Sample.order.field.name,
        Sample.type.field.name,
        Sample.species.field.name,
        Sample.year.field.name,
        Sample.notes.field.name,
        Sample.pop_id.field.name,
        Sample.location.field.name,
        Sample.volume.field.name,
        Sample.parent.field.name,
    ]
    search_help_text = "Search for sample name, genlab ID, GUID or id"
    search_fields = [
        Sample.name.field.name,
        Sample.guid.field.name,
        Sample.genlab_id.field.name,
        Sample.id.field.name,
    ]
    list_filter = [
        (Sample.name.field.name, unfold_filters.FieldTextFilter),
        (Sample.guid.field.name, unfold_filters.FieldTextFilter),
        (Sample.genlab_id.field.name, unfold_filters.FieldTextFilter),
        (Sample.year.field.name, unfold_filters.SingleNumericFilter),
        (Sample.order.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
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
