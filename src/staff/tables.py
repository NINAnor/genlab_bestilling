from datetime import datetime
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

    is_seen = tables.Column(
        orderable=False,
        visible=True,
        verbose_name="",
    )

    class Meta:
        fields = [
            "name",
            "status",
            "genrequest",
            "genrequest__name",
            "genrequest__project",
            "genrequest__area",
            "genrequest__samples_owner",
            "created_at",
            "last_modified_at",
            "is_urgent",
            "is_seen",
        ]
        sequence = ("is_seen", "is_urgent", "status", "id", "name")
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

    def render_is_seen(self, value: bool) -> str:
        if not value:
            return mark_safe(
                '<i class="fa-solid fa-bell text-yellow-500" '
                'title="New within 24h"></i>'
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

    sample_count = tables.Column(
        accessor="sample_count",
        verbose_name="Sample Count",
        orderable=False,
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
        sequence = OrderTable.Meta.sequence + ("sample_count",)

    def render_sample_count(self, record: Any) -> str:
        return record.sample_count or "0"


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

    is_prioritised = tables.TemplateColumn(
        template_name="staff/prioritise_flag.html",
        orderable=True,
        verbose_name="",
    )

    checked = tables.CheckBoxColumn(
        attrs={
            "th__input": {"type": "checkbox", "id": "select-all-checkbox"},
        },
        accessor="pk",
        orderable=False,
        empty_values=(),
    )

    name = tables.Column(order_by=("name_as_int", "name"))

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
        sequence = (
            "checked",
            "is_prioritised",
            "genlab_id",
            "guid",
            "name",
            "species",
            "type",
        )
        order_by = ("-is_prioritised", "species", "genlab_id", "name_as_int", "name")

        empty_text = "No Samples"

    def render_plate_positions(self, value: Any) -> str:
        if value:
            return ", ".join([str(v) for v in value.all()])

        return ""

    def render_checked(self, record: Any) -> str:
        return mark_safe(f'<input type="checkbox" name="checked" value="{record.id}">')  # noqa: S308


class SampleStatusTable(tables.Table):
    """
    This shows a checkbox in the header.
    To display text in the header alongside the checkbox
    override the header-property in the CheckBoxColumn class.
    """

    checked = tables.CheckBoxColumn(
        accessor="pk",
        orderable=False,
        attrs={
            "th__input": {
                "id": "select-all-checkbox",
            },
            "td__input": {
                "name": "checked",
            },
        },
        empty_values=(),
        verbose_name="Mark",
    )

    internal_note = tables.TemplateColumn(
        template_name="staff/note_input_column.html", orderable=False
    )

    marked = tables.BooleanColumn(
        verbose_name="Marked",
        orderable=True,
        yesno="✔,-",
        default=False,
        accessor="is_marked",
    )
    plucked = tables.BooleanColumn(
        verbose_name="Plucked",
        orderable=True,
        yesno="✔,-",
        default=False,
        accessor="is_plucked",
    )
    isolated = tables.BooleanColumn(
        verbose_name="Isolated",
        orderable=True,
        yesno="✔,-",
        default=False,
        accessor="is_isolated",
    )

    class Meta:
        model = Sample
        fields = [
            "checked",
            "genlab_id",
            "marked",
            "plucked",
            "isolated",
            "internal_note",
            "isolation_method",
            "type",
        ]
        sequence = [
            "checked",
            "genlab_id",
            "type",
            "marked",
            "plucked",
            "isolated",
            "internal_note",
            "isolation_method",
        ]
        order_by = ()

    def render_checked(self, record: Any) -> str:
        return mark_safe(  # noqa: S308
            f'<input type="checkbox" name="checked-{record.order.id}" value="{record.id}">'  # noqa: E501
        )


class OrderExtractionSampleTable(SampleBaseTable):
    class Meta(SampleBaseTable.Meta):
        exclude = ("pop_id", "location")


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
            f'<span class="px-2 py-1 text-xs font-medium rounded-full text-nowrap {color_class}">{status_text}</span>'  # noqa: E501
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
        verbose_name="Delivery date",
        orderable=False,
    )

    def render_delivery_date(self, value: datetime | None) -> str:
        if value:
            return value.strftime("%d/%m/%Y")
        return "-"

    class Meta:
        model = Order
        fields = ["priority", "id", "description", "delivery_date", "status"]
        empty_text = "No urgent orders"
        template_name = "django_tables2/tailwind_inner.html"


class NewUnseenOrderTable(StaffIDMixinTable):
    seen = tables.TemplateColumn(
        verbose_name="",
        orderable=False,
        empty_values=(),
        template_name="staff/components/seen_column.html",
    )

    description = tables.Column(
        accessor="genrequest__name",
        verbose_name="Description",
        orderable=False,
    )

    delivery_date = tables.Column(
        verbose_name="Delivery date",
        orderable=False,
    )

    def render_delivery_date(self, value: datetime | None) -> str:
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

    markers = tables.ManyToManyColumn(
        transform=lambda x: x.name,
    )

    class Meta:
        model = Order
        fields = ["id", "description", "delivery_date", "samples", "markers", "seen"]
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
        verbose_name="Delivery date",
        orderable=False,
    )

    def render_delivery_date(self, value: datetime | None) -> str:
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

    markers = tables.ManyToManyColumn(
        transform=lambda x: x.name,
    )

    class Meta:
        model = Order
        fields = [
            "priority",
            "id",
            "description",
            "delivery_date",
            "markers",
            "samples",
        ]
        empty_text = "No new seen orders"
        template_name = "django_tables2/tailwind_inner.html"


class AssignedOrderTable(StatusMixinTable, StaffIDMixinTable):
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

    samples_completed = tables.Column(
        accessor="sample_count",
        verbose_name="Samples isolated",
        orderable=False,
    )

    def render_samples_completed(self, value: int, record: Order) -> str:
        if value > 0:
            return str(record.isolated_sample_count) + " / " + str(value)
        return "-"

    class Meta:
        model = Order
        fields = ["priority", "id", "description", "samples_completed", "status"]
        empty_text = "No assigned orders"
        template_name = "django_tables2/tailwind_inner.html"


class DraftOrderTable(StaffIDMixinTable):
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
        verbose_name="Delivery date",
        orderable=False,
    )

    def render_delivery_date(self, value: datetime | None) -> str:
        if value:
            return value.strftime("%d/%m/%Y")
        return "-"

    samples = tables.Column(
        accessor="sample_count",
        verbose_name="Samples",
        orderable=False,
    )

    markers = tables.ManyToManyColumn(
        transform=lambda x: x.name,
        verbose_name="Markers",
        orderable=False,
    )

    class Meta:
        model = Order
        fields = [
            "priority",
            "id",
            "description",
            "delivery_date",
            "markers",
            "samples",
        ]
        empty_text = "No draft orders"
        template_name = "django_tables2/tailwind_inner.html"
