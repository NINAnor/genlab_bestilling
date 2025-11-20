from typing import Any

import django_tables2 as tables
from django.db.models import QuerySet
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from genlab_bestilling.models import (
    AnalysisOrder,
    AnalysisPlate,
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
    verified_at = tables.TemplateColumn(
        template_name="staff/components/project_verified_column.html",
        verbose_name="Verified",
        orderable=True,
        empty_values=(),
    )

    toggle_active = tables.TemplateColumn(
        template_name="staff/components/activation_toggle_column.html",
        verbose_name="Actions",
        orderable=True,
        empty_values=(),
    )

    class Meta:
        model = Project
        fields = ("number", "name", "verified_at")
        sequence = ("number", "name", "toggle_active", "verified_at")
        order_by = ("-verified_at",)


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
        fields = (
            "priority",
            "id",
            "status",
            "area",
            "description",
            "species",
            "total_samples",
            "responsible_staff",
        )
        empty_text = "No Orders"
        order_by = ("-priority", "status")


class AnalysisOrderTable(OrderTable):
    id = tables.Column(
        linkify=("staff:order-analysis-detail", {"pk": tables.A("id")}),
        orderable=True,
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

    species = tables.Column(
        verbose_name="Species",
        accessor="samples",
        orderable=False,
        empty_values=(),
    )

    class Meta(OrderTable.Meta):
        model = AnalysisOrder
        fields = OrderTable.Meta.fields + ("markers", "expected_delivery_date")  # type: ignore[assignment]
        sequence = (
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
        )

    def render_species(self, value: Any) -> str:
        return ", ".join(
            sorted({sample.species.name for sample in value.all() if sample.species})
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
        fields = OrderTable.Meta.fields + (
            "total_samples_isolated",
            "confirmed_at",
        )  # type: ignore[assignment]
        sequence = (
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
        )


class EquipmentOrderTable(OrderTable):
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
        fields = (
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
        )  # type: ignore[assignment]
        sequence = ("is_seen", "is_urgent", "status", "id", "name")
        empty_text = "No Orders"
        order_by = ("-is_urgent", "last_modified_at", "created_at")  # type: ignore[assignment]

    def render_id(self, record: Any) -> str:
        return str(record)

    def render_is_urgent(self, value: bool) -> str:
        if value:
            icon_url = static("images/exclaimation_mark.svg")
            html = f"<img src='{icon_url}' alt='Urgent' title='Urgent' class='w-5 h-5 inline' />"  # noqa: E501
            return mark_safe(html)  # noqa: S308
        return ""

    def render_is_seen(self, value: bool) -> str:
        if not value:
            return mark_safe(
                '<i class="fa-solid fa-bell text-yellow-500" title="New within 24h"></i>'  # noqa: E501
            )
        return ""


class SampleBaseTable(tables.Table):
    checked = tables.CheckBoxColumn(
        attrs={
            "th__input": {"type": "checkbox", "id": "select-all-checkbox"},
        },
        accessor="pk",
        orderable=False,
        empty_values=(),
    )

    genlab_id = tables.Column(
        orderable=False,
        empty_values=(None,),
        verbose_name="Genlab ID",
    )

    name = tables.Column()

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
            "notes",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}
        sequence = (
            "checked",
            "genlab_id",
            "guid",
            "name",
            "species",
            "type",
        )
        order_by = ("species", "genlab_id")

        empty_text = "No Samples"

    def render_checked(self, record: Any) -> str:
        return format_html(
            '<input type="checkbox" name="checked" value="{}">', record.id
        )

    def order_name(
        self, queryset: QuerySet[Sample], is_descending: bool
    ) -> tuple[QuerySet[Sample], bool]:
        prefix = "-" if is_descending else ""
        queryset = queryset.order_by(f"{prefix}name_as_int", "name")
        return (queryset, True)

    def render_genlab_id(self, value: Any, record: Any) -> Any:
        from_url = reverse(
            "staff:order-extraction-samples", kwargs={"pk": record.order.pk}
        )
        url = reverse("staff:samples-detail", kwargs={"pk": record.id})
        return format_html('<a href="{}?from={}">{}</a>', url, from_url, value)


def get_plate_url(record: Sample) -> str:
    if hasattr(record, "position") and record.position.plate:
        return reverse(
            "staff:extraction-plates-detail",
            kwargs={"pk": record.position.plate.pk},
        )
    return ""


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

    genlab_id = tables.Column(
        orderable=True,
        empty_values=(None,),
        verbose_name="Genlab ID",
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
    invalid = tables.BooleanColumn(
        verbose_name="Invalid",
        orderable=True,
        yesno="✔,-",
        default=False,
        accessor="is_invalid",
    )

    position = tables.Column(
        verbose_name="Position",
        orderable=False,
        accessor="position",
        empty_values=(),
        linkify=get_plate_url,
    )

    def render_position(self, value: Any, record: Any) -> str:
        if value:
            return str(value)
        return ""

    class Meta:
        model = Sample
        fields = (
            "checked",
            "genlab_id",
            "marked",
            "plucked",
            "isolated",
            "invalid",
            "internal_note",
            "isolation_method",
            "position",
            "type",
        )
        sequence = (
            "checked",
            "genlab_id",
            "type",
            "marked",
            "plucked",
            "isolated",
            "invalid",
            "internal_note",
            "isolation_method",
            "position",
        )
        order_by = ("genlab_id",)

    def render_checked(self, record: Any) -> str:
        return format_html(
            '<input type="checkbox" name="checked-{}" value="{}">',
            record.order.id,
            record.id,
        )

    def render_genlab_id(self, value: Any, record: Any) -> Any:
        from_url = reverse(
            "staff:order-extraction-samples-lab", kwargs={"pk": record.order.pk}
        )
        url = reverse("staff:samples-detail", kwargs={"pk": record.id})
        return format_html('<a href="{}?from={}">{}</a>', url, from_url, value)


class OrderExtractionSampleTable(SampleBaseTable):
    class Meta(SampleBaseTable.Meta):
        exclude = (
            # "pop_id",
            "guid",
        )


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
        verbose_name="PCR",
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
        verbose_name="Output",
        orderable=True,
        yesno="✔,-",
        default=False,
        accessor="is_outputted",
    )
    is_invalid = tables.BooleanColumn(
        verbose_name="Not Analysed",
        orderable=True,
        yesno="✔,-",
        default=False,
        accessor="is_invalid",
    )

    sample__internal_note = tables.TemplateColumn(
        template_name="staff/note_input_column.html",
        orderable=False,
        attrs={
            "td": {
                "class": "relative",
            },
        },
    )

    sample__status = tables.Column(
        accessor="sample__status",
        verbose_name="Sample status",
        orderable=False,
    )

    class Meta:
        model = SampleMarkerAnalysis
        fields = (
            "checked",
            "sample__genlab_id",
            "sample__type",
            "marker",
            "sample__status",
            "has_pcr",
            "is_analysed",
            "is_outputted",
            "is_invalid",
            "sample__internal_note",
            "sample__order",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}
        empty_text = "No Samples"
        order_by = ("marker",)

    def render_checked(self, record: SampleMarkerAnalysis) -> str:
        return format_html(
            '<input type="checkbox" name="checked-analysis-{}" value="{}">',
            record.order.id,
            record.id,
        )


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

    position__plate = tables.Column(
        linkify=(
            "staff:extraction-plates-detail",
            {"pk": tables.A("position__plate_id")},
        ),
        verbose_name="Plate",
    )

    def render_order__id(self, value: int, record: Sample) -> str:
        return str(record.order)

    markers = tables.ManyToManyColumn(
        accessor="markers",
        verbose_name="Markers",
        orderable=False,
    )

    class Meta(SampleBaseTable.Meta):
        fields = SampleBaseTable.Meta.fields + (
            "order__id",
            "order__status",
            "order__genrequest__project",
            "position__plate",
        )  # type: ignore[assignment]
        sequence = SampleBaseTable.Meta.sequence + (
            "sample_status",
            "markers",
            "order__id",
            "order__status",
            "notes",
            "position__plate",
        )  # type: ignore[assignment]
        exclude = ("checked", "is_prioritised")


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

    status = tables.Column(
        orderable=False,
    )

    assigned_staff = tables.TemplateColumn(
        template_name="staff/components/responsible_staff_column.html",
        verbose_name="Assigned staff",
        orderable=False,
        empty_values=(),
    )

    class Meta:
        model = Order
        fields = (
            "priority",
            "id",
            "description",
            "delivery_date",
            "status",
            "assigned_staff",
        )
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
        fields = ("id", "description", "delivery_date", "samples", "markers", "seen")
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

    assigned_staff = tables.TemplateColumn(
        template_name="staff/components/responsible_staff_column.html",
        verbose_name="Assigned staff",
        orderable=False,
        empty_values=(),
    )

    class Meta:
        model = Order
        fields = (
            "priority",
            "id",
            "description",
            "delivery_date",
            "markers",
            "samples",
            "assigned_staff",
        )
        empty_text = "No new seen orders"
        template_name = "django_tables2/tailwind_inner.html"


class AssignedOrderTable(OrderStatusMixinTable, PriorityMixinTable, StaffIDMixinTable):
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

    status = tables.Column(
        orderable=False,
    )

    class Meta:
        model = Order
        fields = ("priority", "id", "description", "samples_completed", "status")
        empty_text = "No assigned orders"
        order_by = ["-priority", "status"]
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
        verbose_name="Genetic researcher",
        orderable=False,
    )

    contact_email = tables.Column(
        accessor="contact_email",
        verbose_name="Genetic researcher email",
        orderable=False,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "description",
            "contact_person",
            "contact_email",
        )
        empty_text = "No draft orders"
        template_name = "django_tables2/tailwind_inner.html"


class ExtractionPlateTable(tables.Table):
    qiagen_id = tables.Column(
        linkify=("staff:extraction-plates-detail", {"pk": tables.A("pk")}),
        verbose_name="Qiagen ID",
        orderable=True,
    )

    freezer_id = tables.Column(
        verbose_name="Freezer ID",
        orderable=True,
        empty_values=(),
    )

    shelf_id = tables.Column(
        verbose_name="Shelf ID",
        orderable=True,
        empty_values=(),
    )

    created_at = tables.DateTimeColumn(
        verbose_name="Created",
        format="Y-m-d H:i",
        orderable=True,
    )

    sample_count = tables.Column(
        verbose_name="Samples",
        orderable=False,
        empty_values=(),
    )

    actions = tables.TemplateColumn(
        template_name="staff/components/extraction_plate_actions.html",
        verbose_name="Actions",
        orderable=False,
        empty_values=(),
    )

    def render_sample_count(self, record: ExtractionPlate) -> int:
        return record.positions.filter(sample_raw__isnull=False).count()

    class Meta:
        model = ExtractionPlate
        fields = ["qiagen_id", "freezer_id", "shelf_id", "created_at", "sample_count"]
        empty_text = "No extraction plates found"
        template_name = "django_tables2/tailwind_inner.html"


class AnalysisPlateTable(tables.Table):
    name = tables.Column(
        linkify=("staff:analysis-plates-detail", {"pk": tables.A("pk")}),
        verbose_name="Name",
        orderable=True,
        empty_values=(),
    )

    analysis_date = tables.DateTimeColumn(
        verbose_name="Analysis Date",
        format="Y-m-d H:i",
        orderable=True,
        empty_values=(),
    )

    created_at = tables.DateTimeColumn(
        verbose_name="Created",
        format="Y-m-d H:i",
        orderable=True,
    )

    sample_count = tables.Column(
        verbose_name="Samples",
        orderable=False,
        empty_values=(),
    )

    result_file = tables.Column(
        verbose_name="Result File",
        orderable=False,
        empty_values=(),
    )

    actions = tables.TemplateColumn(
        template_name="staff/components/analysis_plate_actions.html",
        verbose_name="Actions",
        orderable=False,
        empty_values=(),
    )

    def render_sample_count(self, record: AnalysisPlate) -> int:
        return record.positions.filter(sample_marker__isnull=False).count()

    def render_name(self, value: str | None, record: AnalysisPlate) -> str:
        return value or f"Plate {record.id}"

    def render_result_file(self, value: str | None) -> str:
        if value:
            return (
                f'<a href="{value}" class="text-blue-600 hover:underline">'
                '<i class="fas fa-download"></i> Download</a>'
            )
        return '<span class="text-gray-500">No file</span>'

    class Meta:
        model = AnalysisPlate
        fields = [
            "id",
            "name",
            "analysis_date",
            "created_at",
            "sample_count",
            "result_file",
        ]
        empty_text = "No analysis plates found"
        template_name = "django_tables2/tailwind_inner.html"
