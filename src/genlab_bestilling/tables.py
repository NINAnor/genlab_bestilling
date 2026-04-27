from typing import Any

import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

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
        fields = (
            "name",
            "status",
            "created_at",
            "last_modified_at",
        )
        sequence = (
            "id",
            "name",
            "status",
        )
        empty_text = "No Orders"

    def render_id(self, record: Any) -> str:
        return str(record)


class OrderTable(BaseOrderTable):
    polymorphic_ctype = tables.Column(verbose_name="Type")
    genrequest = tables.Column(linkify=True)

    class Meta:
        model = Order
        fields = (
            "name",
            "status",
            "polymorphic_ctype",
            "genrequest",
            "genrequest__project",
            "created_at",
            "last_modified_at",
        )
        sequence = (
            "id",
            "name",
            "status",
            "polymorphic_ctype",
        )
        empty_text = "No Orders"

    def render_polymorphic_ctype(self, value: Any) -> str:
        return value.name

    def render_id(self, record: Any) -> str:
        return str(record)


class GenrequestTable(tables.Table):
    id = tables.Column(linkify=True, orderable=False, empty_values=())
    project_id = tables.Column(linkify=True)
    is_archived = tables.Column(verbose_name="Status", orderable=False)

    class Meta:
        model = Genrequest
        fields = (
            "project_id",
            "name",
            "is_archived",
            "area",
            "species",
            "sample_types",
            "expected_total_samples",
            "expected_samples_delivery_date",
            "expected_analysis_delivery_date",
        )
        sequence = (
            "id",
            "project_id",
            "name",
            "is_archived",
        )

        empty_text = "No projects"

    def render_id(self, record: Any) -> str:
        return record.display_id()

    def render_is_archived(self, value: bool) -> str:
        if value:
            return "Archived"
        return "Active"

    def render_tags(self, record: Any) -> str:
        return ",".join(map(str, record.tags.all()))


class SampleTable(tables.Table):
    class Meta:
        model = Sample
        fields = (
            "guid",
            "name",
            "species",
            "type",
            "year",
            "pop_id",
            "location",
            "notes",
            "genlab_id",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"


class MySampleTable(tables.Table):
    """Sample table for My orders > Samples page."""

    genlab_id = tables.Column(
        verbose_name="Genlab ID",
        orderable=True,
        empty_values=(None,),
    )

    guid = tables.Column(verbose_name="GUID")

    order__id = tables.Column(
        verbose_name="Order ID",
        empty_values=(),
    )

    order__genrequest = tables.Column(
        verbose_name="Genetic Request",
    )

    order__genrequest__project = tables.Column(
        verbose_name="Project",
    )

    order__status = tables.Column(
        verbose_name="Order Status",
        orderable=True,
    )

    class Meta:
        model = Sample
        fields = (
            "genlab_id",
            "guid",
            "name",
            "species",
            "type",
            "year",
            "pop_id",
            "location",
            "order__id",
            "order__genrequest",
            "order__genrequest__project",
            "order__status",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}
        sequence = (
            "genlab_id",
            "guid",
            "name",
            "species",
            "type",
            "year",
            "pop_id",
            "location",
            "order__id",
            "order__genrequest",
            "order__genrequest__project",
            "order__status",
        )
        empty_text = "No Samples"

    def render_genlab_id(self, value: str, record: Sample) -> str:
        if value and record.order:
            url = reverse(
                "genrequest-extraction-samples",
                kwargs={
                    "genrequest_id": record.order.genrequest_id,
                    "pk": record.order.pk,
                },
            )
            return format_html('<a href="{}">{}</a>', url, value)
        return value or "-"

    def render_order__id(self, value: int, record: Sample) -> str:
        if record.order:
            url = reverse(
                "genrequest-extraction-detail",
                kwargs={
                    "genrequest_id": record.order.genrequest_id,
                    "pk": record.order.pk,
                },
            )
            return format_html('<a href="{}">{}</a>', url, record.order)
        return "-"

    def render_order__genrequest(self, value: str, record: Sample) -> str:
        if record.order and record.order.genrequest:
            genrequest = record.order.genrequest
            url = reverse("genrequest-detail", kwargs={"pk": genrequest.pk})
            return format_html('<a href="{}">{}</a>', url, genrequest)
        return "-"

    def render_order__genrequest__project(self, value: str, record: Sample) -> str:
        if record.order and record.order.genrequest and record.order.genrequest.project:
            project = record.order.genrequest.project
            url = reverse("nina:project-detail", kwargs={"pk": project.pk})
            return format_html('<a href="{}">{}</a>', url, project)
        return "-"


class AnalysisSampleTable(tables.Table):
    sample__location__name = tables.Column(verbose_name="Location")
    sample__type__name = tables.Column(verbose_name="Sample type")
    sample__species__name = tables.Column(verbose_name="Species")
    markers_names = tables.Column(verbose_name="Markers")

    class Meta:
        model = Sample
        fields = (
            "sample__genlab_id",
            "markers_names",
            "sample__guid",
            "sample__name",
            "sample__species__name",
            "sample__type__name",
            "sample__year",
            "sample__pop_id",
            "sample__location__name",
        )
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
        fields = BaseOrderTable.Meta.fields + (
            "genrequest",
            "genrequest__project",
            "return_samples",
        )  # type: ignore[assignment]


class ExtractionOrderTable(BaseOrderTable):
    id = tables.Column(
        linkify=True,
        orderable=False,
        empty_values=(),
    )

    class Meta(BaseOrderTable.Meta):
        model = ExtractionOrder
        fields = BaseOrderTable.Meta.fields + (
            "species",
            "sample_types",
            "internal_status",
            "needs_guid",
            "return_samples",
            "pre_isolated",
            "genrequest",
            "genrequest__project",
        )  # type: ignore[assignment]


class EquipmentOrderTable(BaseOrderTable):
    id = tables.Column(
        linkify=True,
        orderable=False,
        empty_values=(),
    )

    class Meta(BaseOrderTable.Meta):
        model = EquipmentOrder
        fields = BaseOrderTable.Meta.fields + ("needs_guid", "sample_types")  # type: ignore[assignment]
