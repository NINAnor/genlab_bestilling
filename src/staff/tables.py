import datetime

import django_tables2 as tables
from django.utils.safestring import mark_safe

from genlab_bestilling.models import (
    AnalysisOrder,
    EquipmentOrder,
    ExtractionOrder,
    ExtractionPlate,
    Sample,
    SampleMarkerAnalysis,
)
from nina.models import Project


class ProjectTable(tables.Table):
    number = tables.Column(
        linkify=("staff:projects-detail", {"pk": tables.A("number")}),
        orderable=True,
        empty_values=(),
    )
    verified_at = tables.BooleanColumn()

    class Meta:
        model = Project
        fields = ("number", "name", "active", "verified_at")


class OrderTable(tables.Table):
    id = tables.Column(
        linkify=True,
        orderable=False,
        empty_values=(),
    )

    # Override as `tables.Column` to send a True/False value to the template
    is_urgent = tables.Column(orderable=True)
    recent = tables.Column(verbose_name="", orderable=True, empty_values=())

    class Meta:
        fields = [
            "name",
            "status",
            "genrequest",
            "genrequest__name",
            "genrequest__project",
            "genrequest__area",
            "genrequest__expected_total_samples",
            "genrequest__samples_owner",
            "created_at",
            "last_modified_at",
            "is_urgent",
        ]
        sequence = ("recent", "id")
        empty_text = "No Orders"
        order_by = ("-is_urgent",)

    def render_id(self, record):
        return str(record)

    def render_recent(self, record):
        created = record.created_at  # This should be a datetime.datetime object
        now = datetime.datetime.now(datetime.timezone.utc)

        if created >= now - datetime.timedelta(hours=24):
            return mark_safe(
                '<i class="fa-solid fa-bell text-yellow-500" title="New within 24h"></i>'
            )
        return ""


class AnalysisOrderTable(OrderTable):
    id = tables.Column(
        linkify=("staff:order-analysis-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    class Meta(OrderTable.Meta):
        model = AnalysisOrder
        fields = OrderTable.Meta.fields + ["return_samples"]


class ExtractionOrderTable(OrderTable):
    id = tables.Column(
        linkify=("staff:order-extraction-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    class Meta(OrderTable.Meta):
        model = ExtractionOrder
        fields = OrderTable.Meta.fields + [
            "species",
            "sample_types",
            "internal_status",
            "needs_guid",
            "return_samples",
            "pre_isolated",
        ]


class EquipmentOrderTable(OrderTable):
    id = tables.Column(
        linkify=("staff:order-equipment-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    class Meta(OrderTable.Meta):
        model = EquipmentOrder
        fields = OrderTable.Meta.fields + ["needs_guid", "sample_types"]


class SampleBaseTable(tables.Table):
    plate_positions = tables.Column(
        empty_values=(), orderable=False, verbose_name="Extraction position"
    )

    class Meta:
        model = Sample
        fields = [
            "genlab_id",
            "guid",
            "name",
            "species",
            "type",
            "year",
            "pop_id",
            "location",
            "notes",
            "plate_positions",
        ]
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"

    def render_plate_positions(self, value):
        if value:
            return ", ".join([str(v) for v in value.all()])

        return ""


class OrderExtractionSampleTable(SampleBaseTable):
    class Meta(SampleBaseTable.Meta):
        fields = SampleBaseTable.Meta.fields


class OrderAnalysisSampleTable(tables.Table):
    sample__plate_positions = tables.Column(
        empty_values=(), orderable=False, verbose_name="Extraction position"
    )

    class Meta:
        model = SampleMarkerAnalysis
        fields = ("marker",) + tuple(
            "sample__" + f for f in SampleBaseTable.Meta.fields
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}
        empty_text = "No Samples"

    def render_sample__plate_positions(self, value):
        if value:
            return ", ".join([str(v) for v in value.all()])

        return ""


class SampleTable(SampleBaseTable):
    genlab_id = tables.Column(
        linkify=("staff:samples-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    class Meta(SampleBaseTable.Meta):
        fields = SampleBaseTable.Meta.fields + [
            "order",
            "order__status",
            "order__genrequest__project",
        ]


class PlateTable(tables.Table):
    id = tables.Column(
        linkify=("staff:plates-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    class Meta:
        model = ExtractionPlate
        fields = (
            "id",
            "name",
            "created_at",
            "last_updated_at",
            "samples_count",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Plates"
