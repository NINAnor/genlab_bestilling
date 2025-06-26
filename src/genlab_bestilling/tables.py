from typing import Any

import django_tables2 as tables

from .models import (
    AnalysisOrder,
    EquipmentOrder,
    ExtractionOrder,
    Genrequest,
    Order,
    Sample,
)


class BaseOrderTable(tables.Table):
    id = tables.Column(linkify=True, orderable=False, empty_values=())

    class Meta:
        model = Order
        fields = [
            "name",
            "status",
            "created_at",
            "last_modified_at",
        ]
        sequence = [
            "id",
            "name",
            "status",
        ]
        empty_text = "No Orders"

    def render_id(self, record: Any) -> str:
        return str(record)


class OrderTable(BaseOrderTable):
    polymorphic_ctype = tables.Column(verbose_name="Type")

    class Meta:
        model = Order
        fields = [
            "name",
            "status",
            "polymorphic_ctype",
            "genrequest",
            "genrequest__project",
            "created_at",
            "last_modified_at",
        ]
        sequence = [
            "id",
            "name",
            "status",
            "polymorphic_ctype",
        ]
        empty_text = "No Orders"

    def render_polymorphic_ctype(self, value: Any) -> str:
        return value.name

    def render_id(self, record: Any) -> str:
        return str(record)


class GenrequestTable(tables.Table):
    project_id = tables.Column(linkify=True)

    class Meta:
        model = Genrequest
        fields = [
            "project_id",
            "name",
            "area",
            "species",
            "sample_types",
            "expected_total_samples",
            "expected_samples_delivery_date",
            "expected_analysis_delivery_date",
        ]

        empty_text = "No projects"

    def render_tags(self, record: Any) -> str:
        return ",".join(map(str, record.tags.all()))


class SampleTable(tables.Table):
    plate_positions = tables.Column(
        empty_values=(), orderable=False, verbose_name="Extraction position"
    )

    class Meta:
        model = Sample
        fields = [
            "guid",
            "name",
            "species",
            "type",
            "year",
            "pop_id",
            "location",
            "notes",
            "genlab_id",
            "plate_positions",
        ]
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"

    def render_plate_positions(self, value: Any) -> str:
        return ", ".join([str(v) for v in value.all()])


class AnalysisSampleTable(tables.Table):
    sample__location__name = tables.Column(verbose_name="Location")
    sample__type__name = tables.Column(verbose_name="Sample type")
    sample__species__name = tables.Column(verbose_name="Species")
    markers_names = tables.Column(verbose_name="Markers")

    class Meta:
        model = Sample
        fields = [
            "sample__genlab_id",
            "markers_names",
            "sample__guid",
            "sample__name",
            "sample__species__name",
            "sample__type__name",
            "sample__year",
            "sample__pop_id",
            "sample__location__name",
        ]
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"


class AnalysisOrderTable(BaseOrderTable):
    id = tables.Column(
        linkify=True,
        orderable=False,
        empty_values=(),
    )

    class Meta(BaseOrderTable.Meta):
        model = AnalysisOrder
        fields = BaseOrderTable.Meta.fields + [
            "genrequest",
            "genrequest__project",
            "return_samples",
        ]


class ExtractionOrderTable(BaseOrderTable):
    id = tables.Column(
        linkify=True,
        orderable=False,
        empty_values=(),
    )

    class Meta(BaseOrderTable.Meta):
        model = ExtractionOrder
        fields = BaseOrderTable.Meta.fields + [
            "species",
            "sample_types",
            "internal_status",
            "needs_guid",
            "return_samples",
            "pre_isolated",
            "genrequest",
            "genrequest__project",
        ]


class EquipmentOrderTable(BaseOrderTable):
    id = tables.Column(
        linkify=True,
        orderable=False,
        empty_values=(),
    )

    class Meta(BaseOrderTable.Meta):
        model = EquipmentOrder
        fields = BaseOrderTable.Meta.fields + ["needs_guid", "sample_types"]
