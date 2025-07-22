import re
from collections.abc import Sequence
from typing import Any

import django_tables2 as tables
from django.db import models
from django.db.models.query import QuerySet
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


class StatusMixinTable(tables.Table):
    status = tables.Column(
        orderable=True,
        verbose_name="Status",
    )

    def order_status(
        self, queryset: QuerySet[Order], is_descending: bool
    ) -> tuple[QuerySet[Order], bool]:
        prefix = "-" if is_descending else ""
        sorted_by_status = queryset.annotate(
            status_order=models.Case(
                models.When(status=Order.OrderStatus.DELIVERED, then=0),
                models.When(status=Order.OrderStatus.DRAFT, then=1),
                models.When(status=Order.OrderStatus.PROCESSING, then=2),
                models.When(status=Order.OrderStatus.COMPLETED, then=3),
            )
        ).order_by(f"{prefix}status_order")

        return (sorted_by_status, True)

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
            "Draft": "Draft",
        }
        color_class = status_colors.get(value, "bg-gray-100 text-gray-800")
        status_text = status_text.get(value, "Unknown")
        return mark_safe(  # noqa: S308
            f'<span class="px-2 py-1 text-xs font-medium rounded-full text-nowrap {color_class}">{status_text}</span>'  # noqa: E501
        )


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


class OrderTable(StatusMixinTable):
    id = tables.Column(
        linkify=True,
        orderable=False,
        empty_values=(),
        verbose_name="Order ID",
    )

    def render_id(self, record: Any) -> str:
        return str(record)

    priority = tables.TemplateColumn(
        orderable=True,
        verbose_name="Priority",
        template_name="staff/components/priority_column.html",
    )

    area = tables.Column(
        accessor="genrequest__area__name",
        verbose_name="Area",
        orderable=True,
    )

    description = tables.Column(
        accessor="genrequest__name",
        verbose_name="Description",
        orderable=True,
    )

    responsible_staff = tables.ManyToManyColumn(
        accessor="responsible_staff",
        verbose_name="Assigned staff",
        orderable=False,
        transform=lambda x: x.first_name + " " + x.last_name,
    )

    class Meta:
        fields = [
            "priority",
            "id",
            "status",
            "area",
            "description",
            "total_samples",
            "responsible_staff",
        ]
        empty_text = "No Orders"
        order_by = ("-is_urgent",)


class AnalysisOrderTable(OrderTable):
    id = tables.Column(
        linkify=("staff:order-analysis-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    markers = tables.ManyToManyColumn(
        accessor="markers",
        verbose_name="Markers",
        orderable=False,
        transform=lambda x: x.name,
    )

    expected_delivery_date = tables.DateColumn(
        accessor="expected_delivery_date",
        verbose_name="Deadline",
        format="d/m/Y",
        orderable=True,
        empty_values=(),
    )

    class Meta(OrderTable.Meta):
        model = AnalysisOrder
        fields = OrderTable.Meta.fields + ["markers", "expected_delivery_date"]
        sequence = (
            "priority",
            "id",
            "status",
            "area",
            "description",
            "total_samples",
            "markers",
            "responsible_staff",
            "expected_delivery_date",
        )


class ExtractionOrderTable(OrderTable):
    id = tables.Column(
        linkify=("staff:order-extraction-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    def render_total_samples(self, record: ExtractionOrder) -> str:
        return record.total_samples or "0"

    def render_total_samples_isolated(self, record: ExtractionOrder) -> str:
        return record.total_samples_isolated or "0"

    confirmed_at = tables.DateColumn(
        accessor="confirmed_at",
        verbose_name="Confirmed at",
        format="d/m/Y",
        orderable=True,
        empty_values=(),
    )

    class Meta(OrderTable.Meta):
        model = ExtractionOrder
        fields = OrderTable.Meta.fields + [
            "total_samples_isolated",
            "confirmed_at",
        ]
        sequence = (
            "priority",
            "id",
            "status",
            "area",
            "description",
            "total_samples",
            "total_samples_isolated",
            "responsible_staff",
            "confirmed_at",
        )


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

    name = tables.Column()

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
        order_by = ("-is_prioritised", "species", "genlab_id")

        empty_text = "No Samples"

    def render_plate_positions(self, value: Any) -> str:
        if value:
            return ", ".join([str(v) for v in value.all()])

        return ""

    def render_checked(self, record: Any) -> str:
        return mark_safe(f'<input type="checkbox" name="checked" value="{record.id}">')  # noqa: S308

    def order_name(
        self, records: Sequence[Any], is_descending: bool
    ) -> tuple[list[Any], bool]:
        def natural_sort_key(record: Any) -> list[str]:
            name = record.name or ""
            parts = re.findall(r"\d+|\D+", name)
            key = []
            for part in parts:
                if part.isdigit():
                    # Pad numbers with zeros for proper string compare, e.g., '000012' > '000001'  # noqa: E501
                    key.append(f"{int(part):010d}")
                else:
                    key.append(part.lower())
            return key

        sorted_records = sorted(records, key=natural_sort_key, reverse=is_descending)
        return (sorted_records, True)


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
        order_by = ("genlab_id",)

    def render_checked(self, record: Any) -> str:
        return mark_safe(  # noqa: S308
            f'<input type="checkbox" name="checked-{record.order.id}" value="{record.id}">'  # noqa: E501
        )


class OrderExtractionSampleTable(SampleBaseTable):
    class Meta(SampleBaseTable.Meta):
        exclude = ("pop_id", "guid", "plate_positions")


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


class StatusMixinTableSamples(tables.Table):
    sample_status = tables.Column(
        verbose_name="Sample Status", empty_values=(), orderable=True
    )

    order__status = tables.Column(
        verbose_name="Order Status", empty_values=(), orderable=True
    )

    def render_order__status(self, record: Order) -> str:
        return render_status_helper(record)


def render_boolean(value: bool) -> str:
    if value:
        return mark_safe('<i class="fa-solid fa-check text-green-500 fa-xl"></i>')
    return mark_safe('<i class="fa-solid fa-xmark text-red-500 fa-xl"></i>')


def generate_order_links(orders: list) -> str:
    if not orders:
        return "-"
    links = [
        f'<a href="{order.get_absolute_staff_url()}">{order}</a>' for order in orders
    ]
    return mark_safe(", ".join(links))  # noqa: S308


def render_status_helper(record: Order) -> str:
    status_colors = {
        Order.OrderStatus.PROCESSING: "bg-yellow-100 text-yellow-800",
        Order.OrderStatus.COMPLETED: "bg-green-100 text-green-800",
        Order.OrderStatus.DELIVERED: "bg-red-100 text-red-800",
    }
    status_text = {
        Order.OrderStatus.PROCESSING: "Processing",
        Order.OrderStatus.COMPLETED: "Completed",
        Order.OrderStatus.DELIVERED: "Not started",
        Order.OrderStatus.DRAFT: "Draft",
    }
    color_class = status_colors.get(record.status, "bg-gray-100 text-gray-800")
    status_text = status_text.get(record.status, "Unknown")
    return mark_safe(  # noqa: S308
        f'<span class="px-2 py-1 text-xs font-medium rounded-full text-nowrap {color_class}">{status_text}</span>'  # noqa: E501
    )


class StatusMixinTable(tables.Table):
    status = tables.Column(
        orderable=False,
        verbose_name="Status",
    )

    def render_status(self, record: Order) -> str:
        return render_status_helper(record)

    def render_sample_status(self, value: Any, record: Sample) -> str:
        order = record.order

        # Determine status label
        if isinstance(order, ExtractionOrder):
            if record.is_isolated:
                status = "Isolated"
            elif record.is_plucked:
                status = "Plucked"
            elif record.is_marked:
                status = "Marked"
            else:
                status = "Not started"
        else:
            status = getattr(order, "sample_status", "Unknown")

        # Define color map
        status_colors = {
            "Marked": "bg-orange-100 text-orange-800",
            "Plucked": "bg-yellow-100 text-yellow-800",
            "Isolated": "bg-green-100 text-green-800",
            "Not started": "bg-red-100 text-red-800",
            "Unknown": "bg-gray-100 text-gray-800",
        }

        # Use computed status, not value
        color_class = status_colors.get(status, "bg-gray-100 text-gray-800")

        return mark_safe(  # noqa: S308
            f'<span class="px-2 py-1 text-xs font-medium rounded-full whitespace-nowrap {color_class}">{status}</span>'  # noqa: E501
        )


class SampleTable(SampleBaseTable, StatusMixinTableSamples):
    STATUS_PRIORITY = {
        "Not started": 0,
        "Marked": 1,
        "Plucked": 2,
        "Isolated": 3,
    }

    genlab_id = tables.Column(
        linkify=("staff:samples-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    sample_status = tables.Column(
        verbose_name="Sample Status", empty_values=(), orderable=True
    )

    order__status = tables.Column(
        verbose_name="Order Status", empty_values=(), orderable=True
    )

    class Meta(SampleBaseTable.Meta):
        fields = SampleBaseTable.Meta.fields + [
            "order",
            "order__status",
            "order__genrequest__project",
            "order__responsible_staff",
        ]
        sequence = SampleBaseTable.Meta.sequence + (
            "sample_status",
            "order",
            "order__status",
            "order__responsible_staff",
            "notes",
        )
        exclude = ("guid", "plate_positions", "checked", "is_prioritised")

    def order_sample_status(
        self, records: Sequence[Any], is_descending: bool
    ) -> tuple[list[Any], bool]:
        def get_status_value(record: Any) -> int:
            if isinstance(record.order, ExtractionOrder):
                if record.is_isolated:
                    return self.STATUS_PRIORITY["Isolated"]
                elif record.is_plucked:
                    return self.STATUS_PRIORITY["Plucked"]
                elif record.is_marked:
                    return self.STATUS_PRIORITY["Marked"]
                else:
                    return self.STATUS_PRIORITY["Not started"]
            else:
                # fallback for other types of orders
                return self.STATUS_PRIORITY.get(
                    getattr(record.order, "sample_status", ""), -1
                )

        sorted_records = sorted(records, key=get_status_value, reverse=is_descending)
        return (sorted_records, True)


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
        template_name="staff/components/priority_column.html",
    )

    description = tables.Column(
        accessor="genrequest__name",
        verbose_name="Description",
        orderable=False,
    )

    delivery_date = tables.DateColumn(
        verbose_name="Deadline",
        orderable=False,
        format="d/m/Y",
        empty_values=(),
    )

    class Meta:
        model = Order
        fields = ["priority", "id", "description", "delivery_date", "status"]
        empty_text = "No urgent orders"
        template_name = "django_tables2/tailwind_inner.html"


class NewUnseenOrderTable(StaffIDMixinTable):
    sticky_header = True

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

    delivery_date = tables.DateColumn(
        verbose_name="Deadline",
        orderable=False,
        format="d/m/Y",
        empty_values=(),
    )

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
    sticky_header = True

    priority = tables.TemplateColumn(
        orderable=False,
        verbose_name="Priority",
        template_name="staff/components/priority_column.html",
    )

    description = tables.Column(
        accessor="genrequest__name",
        verbose_name="Description",
        orderable=False,
    )

    delivery_date = tables.DateColumn(
        verbose_name="Deadline",
        orderable=False,
        format="d/m/Y",
        empty_values=(),
    )

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
    sticky_header = True

    priority = tables.TemplateColumn(
        orderable=False,
        verbose_name="Priority",
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
    sticky_header = True

    priority = tables.TemplateColumn(
        orderable=False,
        verbose_name="Priority",
        template_name="staff/components/priority_column.html",
    )

    description = tables.Column(
        accessor="genrequest__name",
        verbose_name="Description",
        orderable=False,
    )

    delivery_date = tables.DateColumn(
        verbose_name="Deadline",
        orderable=False,
        format="d/m/Y",
        empty_values=(),
    )

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
