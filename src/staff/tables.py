import re
from collections.abc import Sequence
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

from .mixins import (
    OrderStatusMixinTable,
    PriorityMixinTable,
    SampleStatusMixinTable,
    StaffIDMixinTable,
    render_status_helper,
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
        fields = ["number", "name", "active", "verified_at"]


class OrderTable(OrderStatusMixinTable, PriorityMixinTable):
    id = tables.Column(
        linkify=True,
        orderable=False,
        empty_values=(),
        verbose_name="Order ID",
    )

    def render_id(self, record: Order) -> str:
        return str(record)

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

    species = tables.ManyToManyColumn(
        verbose_name="Species",
    )

    responsible_staff = tables.ManyToManyColumn(
        accessor="responsible_staff",
        verbose_name="Assigned staff",
        orderable=False,
    )

    class Meta:
        fields = [
            "priority",
            "id",
            "status",
            "area",
            "description",
            "species",
            "total_samples",
            "responsible_staff",
        ]
        empty_text = "No Orders"
        order_by = ["-priority", "status"]


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
        sequence = [
            "priority",
            "id",
            "status",
            "area",
            "description",
            "species",
            "total_samples",
            "markers",
            "responsible_staff",
            "expected_delivery_date",
        ]


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
        sequence = [
            "priority",
            "id",
            "status",
            "area",
            "description",
            "species",
            "total_samples",
            "total_samples_isolated",
            "responsible_staff",
            "confirmed_at",
        ]


class EquipmentOrderTable(tables.Table):
    id = tables.Column(
        linkify=("staff:order-equipment-detail", {"pk": tables.A("id")}),
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

    class Meta(OrderTable.Meta):
        model = EquipmentOrder
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
            "needs_guid",
            "sample_types",
        ]
        sequence = ["is_seen", "is_urgent", "status", "id", "name"]
        empty_text = "No Orders"
        order_by = ["-is_urgent", "last_modified_at", "created_at"]

    def render_id(self, record: Any) -> str:
        return str(record)

    def render_is_urgent(self, value: bool) -> str:
        html_exclaimation_mark = (
            "<i class='fa-solid fa-exclamation text-red-500 fa-2x' title='Urgent'></i>"
        )
        if value:
            return mark_safe(html_exclaimation_mark)  # noqa: S308
        return ""

    def render_is_seen(self, value: bool) -> str:
        if not value:
            return mark_safe(
                '<i class="fa-solid fa-bell text-yellow-500" '
                'title="New within 24h"></i>'
            )
        return ""


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
        sequence = [
            "checked",
            "is_prioritised",
            "genlab_id",
            "guid",
            "name",
            "species",
            "type",
        ]
        order_by = ["-is_prioritised", "species", "genlab_id"]

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
        template_name="staff/note_input_column.html",
        orderable=False,
        attrs={
            "td": {
                "class": "relative",
            },
        },
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
        order_by = ["genlab_id"]

    def render_checked(self, record: Any) -> str:
        return mark_safe(  # noqa: S308
            f'<input type="checkbox" name="checked-{record.order.id}" value="{record.id}">'  # noqa: E501
        )


class OrderExtractionSampleTable(SampleBaseTable):
    class Meta(SampleBaseTable.Meta):
        exclude = ["pop_id", "guid", "plate_positions"]


class OrderAnalysisSampleTable(tables.Table):
    checked = tables.CheckBoxColumn(
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

    has_pcr = tables.BooleanColumn(
        verbose_name="Has PCR",
        orderable=True,
        yesno="✔,-",
        default=False,
        accessor="has_pcr",
    )

    is_analysed = tables.BooleanColumn(
        verbose_name="Analysed",
        orderable=True,
        yesno="✔,-",
        default=False,
        accessor="is_analysed",
    )
    is_outputted = tables.BooleanColumn(
        verbose_name="Is Outputted",
        orderable=True,
        yesno="✔,-",
        default=False,
        accessor="is_outputted",
    )

    class Meta:
        model = SampleMarkerAnalysis
        fields = [
            "checked",
            "sample__genlab_id",
            "sample__type",
            "marker",
            "has_pcr",
            "is_analysed",
            "is_outputted",
            "sample__internal_note",
            "sample__order",
        ]
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}
        empty_text = "No Samples"

    def render_checked(self, record: SampleMarkerAnalysis) -> str:
        return mark_safe(  # noqa: S308
            f'<input type="checkbox" name="checked-analysis-{record.order.id}" value="{record.id}">'  # noqa: E501
        )


class PlateTable(tables.Table):
    id = tables.Column(
        linkify=("staff:plates-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    class Meta:
        model = ExtractionPlate
        fields = [
            "id",
            "name",
            "created_at",
            "last_updated_at",
            "samples_count",
        ]
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Plates"


class StatusMixinTableSamples(tables.Table):
    sample_status = tables.Column(
        verbose_name="Sample Status", empty_values=(), orderable=True
    )

    order__status = tables.Column(
        verbose_name="Order Status", empty_values=(), orderable=True
    )

    def render_order__status(self, record: Sample) -> str:
        if record.order and record.order.status:
            return render_status_helper(record.order.status)
        return "-"


class SampleTable(SampleBaseTable, StatusMixinTableSamples, SampleStatusMixinTable):
    STATUS_PRIORITY = {
        "Not started": 0,
        "Marked": 1,
        "Plucked": 2,
        "Isolated": 3,
    }

    genlab_id = tables.Column(
        linkify=("staff:samples-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(None,),
        verbose_name="Genlab ID",
    )

    guid = tables.Column(verbose_name="GUID")

    order__status = tables.Column(
        verbose_name="Order Status", empty_values=(), orderable=True
    )

    def get_order_id_link(record: Sample) -> str:
        if record.order:
            return record.order.get_absolute_staff_url()
        return ""

    order__id = tables.Column(
        linkify=get_order_id_link,
        verbose_name="Order ID",
    )

    def render_order__id(self, value: int, record: Sample) -> str:
        return str(record.order)

    class Meta(SampleBaseTable.Meta):
        fields = SampleBaseTable.Meta.fields + [
            "order__id",
            "order__status",
            "order__genrequest__project",
        ]
        sequence = SampleBaseTable.Meta.sequence + [
            "sample_status",
            "order__id",
            "order__status",
            "notes",
        ]
        exclude = ["plate_positions", "checked", "is_prioritised"]


class UrgentOrderTable(StaffIDMixinTable, OrderStatusMixinTable):
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


class AssignedOrderTable(OrderStatusMixinTable, StaffIDMixinTable):
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

    description = tables.Column(
        accessor="genrequest__name",
        verbose_name="Description",
        orderable=False,
    )

    contact_person = tables.Column(
        accessor="contact_person",
        verbose_name="Contact Person",
        orderable=False,
    )

    contact_email = tables.Column(
        accessor="contact_email",
        verbose_name="Contact Email",
        orderable=False,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "description",
            "contact_person",
            "contact_email",
        ]
        empty_text = "No draft orders"
        template_name = "django_tables2/tailwind_inner.html"
