from typing import Any

import django_tables2 as tables
from django.utils.safestring import mark_safe

from genlab_bestilling.models import (
    AnalysisOrder,
    EquipmentOrder,
    ExtractionOrder,
    ExtractionPlate,
    Order,
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

    is_urgent = tables.Column(
        orderable=True,
        visible=True,
        verbose_name="",
    )

    status = tables.Column(
        verbose_name="Status",
        orderable=False,
    )

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
        sequence = ("is_urgent", "status", "id")
        empty_text = "No Orders"
        order_by = ("-is_urgent", "last_modified_at", "created_at")

    def render_id(self, record: Any) -> str:
        return str(record)

    def render_is_urgent(self, value: bool) -> str:
        html_exclaimation_mark = (
            "<i class='fa-solid fa-exclamation text-red-500 fa-2x' title='Urgent'></i>"
        )
        if value:
            return mark_safe(html_exclaimation_mark)  # noqa: S308
        else:
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

    def render_plate_positions(self, value: Any) -> str:
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

    def render_sample__plate_positions(self, value: Any) -> str:
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


class StatusMixinTable(tables.Table):
    status = tables.Column(
        orderable=False,
        verbose_name="Status",
    )

    def render_status(self, value: Order.OrderStatus, record: Order) -> str:
        status_colors = {
            "Processing": "bg-yellow-100 text-yellow-800",
            "Completed": "bg-green-100 text-green-800",
            "Delivered": "bg-red-100 text-red-800",
        }
        status_text = {
            "Processing": "Processing",
            "Completed": "Completed",
            "Delivered": "Not started",
        }
        color_class = status_colors.get(value, "bg-gray-100 text-gray-800")
        status_text = status_text.get(value, "Unknown")
        return mark_safe(  # noqa: S308
            f'<span class="px-2 py-1 text-xs font-medium rounded-full {color_class}">{status_text}</span>'  # noqa: E501
        )


class StaffIDMixinTable(tables.Table):
    id = tables.Column(
        orderable=False,
        empty_values=(),
    )

    def render_id(
        self, record: ExtractionOrder | AnalysisOrder | EquipmentOrder
    ) -> str:
        url = record.get_absolute_staff_url()

        return mark_safe(f'<a href="{url}">{record}</a>')  # noqa: S308


class UrgentOrderTable(StaffIDMixinTable, StatusMixinTable):
    description = tables.Column(
        accessor="genrequest__name",
        verbose_name="Description",
        orderable=False,
    )

    delivery_date = tables.Column(
        accessor="genrequest__expected_samples_delivery_date",
        verbose_name="Delivery date",
        orderable=False,
    )

    def render_delivery_date(self, value: Any) -> str:
        if value:
            return value.strftime("%d/%m/%Y")
        return "-"

    class Meta:
        model = Order
        fields = ["id", "description", "delivery_date", "status"]
        empty_text = "No urgent orders"
        template_name = "django_tables2/tailwind_inner.html"


class NewUnseenOrderTable(StaffIDMixinTable):
    seen = tables.TemplateColumn(
        orderable=False,
        verbose_name="Seen",
        template_name="staff/components/seen_column.html",
        empty_values=(),
    )

    description = tables.Column(
        accessor="genrequest__name",
        verbose_name="Description",
        orderable=False,
    )

    delivery_date = tables.Column(
        accessor="genrequest__expected_samples_delivery_date",
        verbose_name="Delivery date",
        orderable=False,
    )

    def render_delivery_date(self, value: Any) -> str:
        if value:
            return value.strftime("%d/%m/%Y")
        return "-"

    samples = tables.Column(
        accessor="sample_count",
        verbose_name="Samples",
        orderable=False,
    )

    def render_samples(self, value: int) -> str:
        if value > 0:
            return str(value)
        return "-"

    class Meta:
        model = Order
        fields = ["id", "description", "delivery_date", "samples", "seen"]
        empty_text = "No new unseen orders"
        template_name = "django_tables2/tailwind_inner.html"


class NewSeenOrderTable(StaffIDMixinTable):
    priority = tables.TemplateColumn(
        orderable=False,
        verbose_name="Priority",
        accessor="priority",
        template_name="staff/components/priority_column.html",
    )

    description = tables.Column(
        accessor="genrequest__name",
        verbose_name="Description",
        orderable=False,
    )

    delivery_date = tables.Column(
        accessor="genrequest__expected_samples_delivery_date",
        verbose_name="Delivery date",
        orderable=False,
    )

    def render_delivery_date(self, value: Any) -> str:
        if value:
            return value.strftime("%d/%m/%Y")
        return "-"

    samples = tables.Column(
        accessor="sample_count",
        verbose_name="Samples",
        orderable=False,
    )

    def render_samples(self, value: int) -> str:
        if value > 0:
            return str(value)
        return "-"

    class Meta:
        model = Order
        fields = ["priority", "id", "description", "delivery_date", "samples"]
        empty_text = "No new seen orders"
        template_name = "django_tables2/tailwind_inner.html"


class AssignedOrderTable(StatusMixinTable, StaffIDMixinTable):
    priority = tables.TemplateColumn(
        orderable=False,
        verbose_name="Priority",
        accessor="priority",
        template_name="staff/components/priority_column.html",
    )

    samples_completed = tables.Column(
        accessor="sample_count",
        verbose_name="Samples completed",
        orderable=False,
    )

    def render_samples_completed(self, value: int) -> str:
        if value > 0:
            return "- / " + str(value)
        return "-"

    class Meta:
        model = Order
        fields = ["priority", "id", "samples_completed", "status"]
        empty_text = "No assigned orders"
        template_name = "django_tables2/tailwind_inner.html"
