from dataclasses import dataclass
from datetime import datetime
from typing import Any

import django_tables2 as tables
from django.db.models import IntegerField
from django.db.models.functions import Cast
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

from .mixins import StaffIDMixinTable, StatusMixinTable, render_status_helper


@dataclass
class CombinedOrder:
    extraction_order: ExtractionOrder
    analysis_order: AnalysisOrder | None = None
    priority: Order.OrderPriority = Order.OrderPriority.NORMAL
    assigned_staff: list[str] | None = None

    def status(self) -> Order.OrderStatus:
        """Returns the lowest status of the extraction and analysis orders."""
        order = Order.STATUS_ORDER
        if self.analysis_order:
            return min(
                self.extraction_order.status,
                self.analysis_order.status,
                key=order.index,
            )

        return self.extraction_order.status


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
    priority = tables.Column(
        orderable=False,
        verbose_name="Priority",
        accessor="priority",
    )

    def render_priority(self, value: Order.OrderPriority) -> str:
        if value == Order.OrderPriority.URGENT:
            return mark_safe(
                '<i class="fa-solid fa-exclamation fa-lg text-red-500" title="Urgent"></i>'  # noqa: E501
            )
        return ""

    def get_extraction_link(record: CombinedOrder) -> str | None:
        return record.extraction_order.get_absolute_staff_url()

    ext_id = tables.Column(
        linkify=get_extraction_link,
        orderable=False,
        empty_values=(),
        verbose_name="EXT ID",
        accessor="extraction_order",
    )

    def render_ext_id(self, record: CombinedOrder) -> str:
        return str(record.extraction_order)

    def get_analysis_link(record: CombinedOrder) -> str | None:
        if record.analysis_order is not None:
            return record.analysis_order.get_absolute_staff_url()
        return None

    anl_id = tables.Column(
        linkify=get_analysis_link,
        orderable=False,
        empty_values=(),
        verbose_name="ANL ID",
        accessor="analysis_order",
    )

    def render_anl_id(self, record: CombinedOrder) -> str:
        if record.analysis_order:
            return str(record.analysis_order)
        return "-"

    ext_status = tables.Column(
        accessor="extraction_order__status",
        verbose_name="EXT status",
        orderable=False,
    )

    def render_ext_status(self, value: Order.OrderStatus, record: CombinedOrder) -> str:
        return render_status_helper(value)

    anl_status = tables.Column(
        verbose_name="ANL status",
        orderable=False,
        accessor="analysis_order__status",
        empty_values=(),
    )

    def render_anl_status(self, value: Order.OrderStatus, record: CombinedOrder) -> str:
        if record.analysis_order:
            return render_status_helper(value)
        return "-"

    area = tables.Column(
        accessor="extraction_order__genrequest__area__name",
        verbose_name="Area",
        orderable=False,
    )

    description = tables.Column(
        accessor="extraction_order__genrequest__name",
        verbose_name="Description",
        orderable=False,
    )

    total_samples_extraction = tables.Column(
        accessor="extraction_order__sample_count",
        verbose_name="Total samples EXT",
        orderable=False,
    )

    total_samples_analysis = tables.Column(
        accessor="analysis_order__sample_count",
        verbose_name="Total samples ANL",
        orderable=False,
    )

    samples_isolated = tables.Column(
        accessor="extraction_order__sample_isolated_count",
        verbose_name="Samples isolated",
        orderable=False,
    )

    markers = tables.ManyToManyColumn(
        accessor="extraction_order__genrequest__markers",
        transform=lambda x: x.name,
    )

    assigned_staff = tables.Column(
        accessor="assigned_staff",
        verbose_name="Assigned staff",
        orderable=False,
        empty_values=(),
    )

    def render_assigned_staff(self, value: list[str] | None) -> str:
        if value:
            return ", ".join(value)
        return "-"

    delivery_date = tables.Column(
        accessor="analysis_order__expected_delivery_date",
        verbose_name="Delivery date",
        orderable=False,
        empty_values=(),
    )

    def render_delivery_date(self, value: datetime) -> str:
        if value:
            return value.strftime("%d/%m/%Y")
        return "-"

    class Meta:
        fields = [
            "priority",
            "ext_id",
            "anl_id",
            "ext_status",
            "anl_status",
            "area",
            "description",
            "total_samples_extraction",
            "total_samples_analysis",
            "samples_isolated",
            "markers",
            "assigned_staff",
            "delivery_date",
        ]
        empty_text = "No Orders"


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

    name = tables.Column(order_by=("name_as_int",))

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
        order_by = (
            "-is_prioritised",
            "species",
            "genlab_id",
            "name_as_int",
        )

        empty_text = "No Samples"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if hasattr(self.data, "data"):
            self.data.data = self.data.data.annotate(
                name_as_int=Cast("name", output_field=IntegerField())
            )

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
    )
    plucked = tables.BooleanColumn(
        verbose_name="Plucked",
        orderable=True,
        yesno="✔,-",
        default=False,
    )
    isolated = tables.BooleanColumn(
        verbose_name="Isolated",
        orderable=True,
        yesno="✔,-",
        default=False,
    )

    class Meta:
        model = Sample
        fields = [
            "checked",
            "genlab_id",
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
