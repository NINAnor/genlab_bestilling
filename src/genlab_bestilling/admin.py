from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from unfold.contrib.filters import admin as unfold_filters

from .models import (
    AnalysisOrder,
    AnalysisOrderResultsCommunication,
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
    IsolationMethod,
    Location,
    LocationType,
    Marker,
    Order,
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
    M = Area
    search_help_text = "Search for area name"
    search_fields = [M.name.field.name]
    list_display = [M.name.field.name, M.location_mandatory.field.name]
    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        M.location_mandatory.field.name,
    ]
    list_filter_submit = True
    list_filter_sheet = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    M = Order
    list_display = [
        M.id.field.name,  # type: ignore[attr-defined]
        M.name.field.name,
        M.status.field.name,
        M.created_at.field.name,
    ]
    list_filter = [M.status.field.name]
    search_fields = [M.id.field.name, M.name.field.name]  # type: ignore[attr-defined]


@admin.register(LocationType)
class LocationTypeAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    M = Location

    search_help_text = "Search for location name, river ID or code"
    search_fields = [M.name.field.name, M.river_id.field.name, M.code.field.name]

    list_display = [M.name.field.name, M.river_id.field.name, M.code.field.name]

    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        (M.river_id.field.name, unfold_filters.FieldTextFilter),
        (M.code.field.name, unfold_filters.FieldTextFilter),
        (M.fylke.field.name, unfold_filters.FieldTextFilter),
        (M.types.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
    ]

    filter_horizontal = [M.types.field.name]
    list_filter_submit = True


@admin.register(Genrequest)
class GenrequestAdmin(ModelAdmin):
    M = Genrequest
    list_display = [
        M.name.field.name,
        M.project.field.name,
        M.samples_owner.field.name,
        M.area.field.name,
        M.expected_total_samples.field.name,
        M.expected_samples_delivery_date.field.name,
        M.expected_analysis_delivery_date.field.name,
        M.creator.field.name,
        M.last_modified_at.field.name,
        M.created_at.field.name,
    ]
    search_help_text = "Search for genrequest name or project name"
    search_fields = [M.name.field.name, "project__name"]

    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        (M.project.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.area.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.sample_types.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.markers.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.species.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.samples_owner.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.creator.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.expected_total_samples.field.name, unfold_filters.RangeNumericFilter),
        M.expected_samples_delivery_date.field.name,
        M.expected_analysis_delivery_date.field.name,
        M.last_modified_at.field.name,
        M.created_at.field.name,
    ]

    autocomplete_fields = [
        M.area.field.name,
        M.project.field.name,
        M.samples_owner.field.name,
        M.creator.field.name,
    ]
    filter_horizontal = [
        M.markers.field.name,
        M.sample_types.field.name,
        M.species.field.name,
    ]
    readonly_fields = [
        M.created_at.field.name,
        M.last_modified_at.field.name,
    ]
    list_filter_submit = True


@admin.register(Marker)
class MarkerAdmin(ModelAdmin):
    M = Marker
    list_display = [M.name.field.name, M.analysis_type.field.name]

    search_help_text = "Search for marker name"
    search_fields = [M.name.field.name]

    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        (M.analysis_type.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
    ]
    autocomplete_fields = [M.analysis_type.field.name]
    list_filter_submit = True
    list_filter_sheet = False


@admin.register(Species)
class SpeciesAdmin(ModelAdmin):
    M = Species
    list_display = [M.name.field.name, M.area.field.name, M.code.field.name]

    search_help_text = "Search for species name"
    search_fields = [M.name.field.name]

    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        (M.code.field.name, unfold_filters.FieldTextFilter),
        (M.area.field.name, unfold_filters.RelatedDropdownFilter),
    ]
    autocomplete_fields = [
        M.markers.field.name,
        M.area.field.name,
        M.location_type.field.name,
    ]
    list_filter_submit = True
    list_filter_sheet = False


@admin.register(SampleType)
class SampleTypeAdmin(ModelAdmin):
    M = SampleType
    search_help_text = "Search for sample type name"
    search_fields = [M.name.field.name]
    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        (M.areas.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
    ]
    autocomplete_fields = [M.areas.field.name]
    list_filter_submit = True
    list_filter_sheet = False


@admin.register(AnalysisType)
class AnalysisTypeAdmin(ModelAdmin):
    search_fields = ["name"]


@admin.register(EquipmentType)
class EquipmentTypeAdmin(ModelAdmin):
    M = EquipmentType
    list_display = [M.name.field.name, M.unit.field.name]

    search_help_text = "Search for equipment type name"
    search_fields = [M.name.field.name]

    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        (M.unit.field.name, unfold_filters.FieldTextFilter),
    ]
    list_filter_submit = True
    list_filter_sheet = False


@admin.register(EquipmentBuffer)
class EquipmentBufferAdmin(ModelAdmin):
    M = EquipmentBuffer
    list_display = [M.name.field.name, M.unit.field.name]

    search_help_text = "Search for equipment buffer name"
    search_fields = [M.name.field.name]

    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        (M.unit.field.name, unfold_filters.FieldTextFilter),
    ]
    list_filter_submit = True
    list_filter_sheet = False


@admin.register(EquimentOrderQuantity)
class EquimentOrderQuantityAdmin(ModelAdmin):
    M = EquimentOrderQuantity
    list_display = [
        M.id.field.name,
        M.equipment.field.name,
        M.order.field.name,
        M.buffer.field.name,
        M.buffer_quantity.field.name,
        M.quantity.field.name,
    ]
    search_help_text = "Search for id"
    search_fields = [
        M.id.field.name,
    ]
    list_filter = [
        (M.id.field.name, unfold_filters.SingleNumericFilter),
        (M.equipment.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.order.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.buffer.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.buffer_quantity.field.name, unfold_filters.RangeNumericFilter),
        (M.quantity.field.name, unfold_filters.RangeNumericFilter),
    ]
    autocomplete_fields = [
        M.equipment.field.name,
        M.order.field.name,
        M.buffer.field.name,
    ]
    list_filter_sheet = False
    list_filter_submit = True


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
        EO.id.field.name,  # type: ignore[attr-defined]
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
        EO.id.field.name,  # type: ignore[attr-defined]
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


@admin.register(AnalysisOrderResultsCommunication)
class AnalysisOrderResultsCommunicationAdmin(ModelAdmin):
    M = AnalysisOrderResultsCommunication
    list_display = [
        M.id.field.name,
        M.analysis_order.field.name,
        M.contact_email_results.field.name,
    ]
    search_help_text = "Search for id or contact person name/email"
    search_fields = [
        M.id.field.name,
        M.contact_email_results.field.name,
    ]
    list_filter = [
        (M.id.field.name, unfold_filters.SingleNumericFilter),
        (M.analysis_order.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.contact_email_results.field.name, unfold_filters.FieldTextFilter),
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
class SampleMarkerAnalysisAdmin(ModelAdmin):
    SMA = SampleMarkerAnalysis

    search_help_text = "Search for id or transaction UUID"
    search_fields = [
        SMA.id.field.name,
        SMA.transaction.field.name,
    ]
    list_display = [
        SMA.id.field.name,
        SMA.sample.field.name,
        SMA.order.field.name,
        SMA.marker.field.name,
        SMA.transaction.field.name,
    ]
    list_filter = [
        (SMA.id.field.name, unfold_filters.SingleNumericFilter),
        (SMA.sample.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (SMA.order.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (SMA.marker.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (SMA.transaction.field.name, unfold_filters.FieldTextFilter),
    ]
    autocomplete_fields = [
        SMA.sample.field.name,
        SMA.order.field.name,
        SMA.marker.field.name,
    ]
    list_filter_sheet = False
    list_filter_submit = True


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
        (Sample.id.field.name, unfold_filters.SingleNumericFilter),
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
class ExtractPlatePositionAdmin(ModelAdmin):
    """
    plate = models.ForeignKey(
    sample = models.ForeignKey(
    position = models.IntegerField()
    extracted_at = models.DateTimeField(auto_now=True)
    notes = models.CharField(null=True, blank=True)

    """

    M = ExtractPlatePosition
    list_display = [
        "__str__",
        M.plate.field.name,
        M.sample.field.name,
        M.position.field.name,
        M.extracted_at.field.name,
    ]

    search_help_text = "Search for id"
    search_fields = [M.id.field.name]
    list_filter = [
        (M.id.field.name, unfold_filters.SingleNumericFilter),
        (M.plate.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.sample.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.position.field.name, unfold_filters.SingleNumericFilter),
        M.extracted_at.field.name,
    ]

    list_filter_submit = True
    list_filter_sheet = False


@admin.register(ExtractionPlate)
class ExtractionPlateAdmin(ModelAdmin):
    M = ExtractionPlate
    list_display = [
        "__str__",
        M.name.field.name,
        M.last_modified_at.field.name,
        M.created_at.field.name,
    ]

    search_help_text = "Search for id or name"
    search_fields = [M.id.field.name, M.name.field.name]
    list_filter = [
        (M.id.field.name, unfold_filters.SingleNumericFilter),
        (M.name.field.name, unfold_filters.FieldTextFilter),
        M.last_modified_at.field.name,
        M.created_at.field.name,
    ]

    list_filter_submit = True
    list_filter_sheet = False


@admin.register(AnalysisResult)
class AnalysisResultAdmin(ModelAdmin):
    M = AnalysisResult
    list_display = [
        M.name.field.name,
        M.marker.field.name,
        M.order.field.name,
        M.analysis_date.field.name,
        M.last_modified_at.field.name,
        M.created_at.field.name,
    ]

    search_help_text = "Search for analysis result name"
    search_fields = [M.name.field.name]
    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        (M.marker.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        (M.order.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
        M.analysis_date.field.name,
        M.last_modified_at.field.name,
        M.created_at.field.name,
    ]
    autocomplete_fields = [M.marker.field.name, M.order.field.name]
    list_filter_submit = True
    list_filter_sheet = False
    filter_horizontal = [M.samples.field.name]
    readonly_fields = [
        M.analysis_date.field.name,
        M.last_modified_at.field.name,
        M.created_at.field.name,
    ]


@admin.register(IsolationMethod)
class IsolationMethodAdmin(ModelAdmin):
    M = IsolationMethod

    list_display = [
        M.name.field.name,
        "get_sample_types",
    ]

    search_help_text = "Search for isolation method name"
    search_fields = [M.name.field.name]
    list_filter = [
        (M.name.field.name, unfold_filters.FieldTextFilter),
        (M.sample_types.field.name, unfold_filters.AutocompleteSelectMultipleFilter),
    ]
    autocomplete_fields = [M.sample_types.field.name]
    filter_horizontal = [M.sample_types.field.name]
    list_filter_submit = True
    list_filter_sheet = False

    def get_queryset(self, request: HttpRequest) -> QuerySet[IsolationMethod]:
        return super().get_queryset(request).prefetch_related("sample_types")

    def get_sample_types(self, obj: IsolationMethod) -> str:
        return ", ".join([sample_type.name for sample_type in obj.sample_types.all()])
