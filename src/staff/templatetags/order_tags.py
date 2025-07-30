import uuid
from collections import Counter

from django import template
from django.db import models
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from genlab_bestilling.models import (
    AnalysisOrder,
    AnalysisOrderResultsCommunication,
    Area,
    Order,
)
from staff.forms import ResponsibleStaffForm

from ..tables import (
    AssignedOrderTable,
    DraftOrderTable,
    NewSeenOrderTable,
    NewUnseenOrderTable,
    UrgentOrderTable,
    render_status_helper,
)

register = template.Library()


@register.inclusion_tag("staff/components/responsible_staff_multiselect.html")
def responsible_staff_multiselect(order: Order | None = None) -> dict:
    prefix = f"order_{order.id}" if order else f"new_{uuid.uuid4().hex[:8]}"

    # Add prefix to the form to avoid conflicts with other forms on the page
    form = ResponsibleStaffForm(order=order, prefix=prefix)
    return {
        "form": form,
        "order": order,
    }


def generate_order_links(orders: list) -> str:
    if not orders:
        return "-"
    return format_html_join(
        ", ",
        "<a href='{}'>{}</a>",
        ((order.get_absolute_staff_url(), str(order)) for order in orders),
    )


def render_boolean(value: bool) -> str:
    if value:
        return mark_safe('<i class="fa-solid fa-check text-green-500 fa-xl"></i>')
    return mark_safe('<i class="fa-solid fa-xmark text-red-500 fa-xl"></i>')


@register.inclusion_tag("staff/components/order_table.html", takes_context=True)
def urgent_orders_table(context: dict, area: Area | None = None) -> dict:
    urgent_orders = (
        Order.objects.filter(
            is_urgent=True,
        )
        .exclude(status__in=[Order.OrderStatus.DRAFT, Order.OrderStatus.COMPLETED])
        .select_related("genrequest")
        .annotate(
            priority=models.Case(
                models.When(is_urgent=True, then=Order.OrderPriority.URGENT),
                models.When(is_prioritized=True, then=Order.OrderPriority.PRIORITIZED),
                default=1,
            ),
            delivery_date=models.Case(
                models.When(
                    analysisorder__isnull=False,
                    then="analysisorder__expected_delivery_date",
                ),
                default=models.Value(None, output_field=models.DateField()),
            ),
        )
    )

    if area:
        urgent_orders = urgent_orders.filter(genrequest__area=area)

    urgent_orders = urgent_orders.order_by(
        models.Case(
            models.When(status=Order.OrderStatus.PROCESSING, then=0),
            models.When(status=Order.OrderStatus.DELIVERED, then=1),
            models.When(status=Order.OrderStatus.COMPLETED, then=2),
            default=3,
            output_field=models.IntegerField(),
        ),
        "-created_at",
    )

    return {
        "title": "Urgent orders",
        "table": UrgentOrderTable(urgent_orders),
        "count": urgent_orders.count(),
        "request": context.get("request"),
    }


@register.inclusion_tag("staff/components/order_table.html", takes_context=True)
def new_seen_orders_table(context: dict, area: Area | None = None) -> dict:
    new_orders = (
        Order.objects.filter(
            status__in=[Order.OrderStatus.DELIVERED, Order.OrderStatus.PROCESSING],
            is_seen=True,
            responsible_staff__isnull=True,
        )
        .exclude(is_urgent=True)
        .select_related("genrequest")
        .annotate(
            sample_count=models.Case(
                models.When(
                    extractionorder__isnull=False,
                    then=models.Count("extractionorder__samples", distinct=True),
                ),
                models.When(
                    analysisorder__isnull=False,
                    then=models.Count("analysisorder__samples", distinct=True),
                ),
                default=0,
            ),
            priority=models.Case(
                models.When(is_urgent=True, then=Order.OrderPriority.URGENT),
                models.When(is_prioritized=True, then=Order.OrderPriority.PRIORITIZED),
                default=1,
            ),
            delivery_date=models.Case(
                models.When(
                    analysisorder__isnull=False,
                    then="analysisorder__expected_delivery_date",
                ),
                default=models.Value(None, output_field=models.DateField()),
            ),
        )
    )

    if area:
        new_orders = new_orders.filter(genrequest__area=area)

    new_orders = new_orders.order_by("-priority", "-created_at")

    return {
        "title": "Unassigned orders",
        "table": NewSeenOrderTable(new_orders),
        "count": new_orders.count(),
        "request": context.get("request"),
    }


@register.inclusion_tag("staff/components/order_table.html", takes_context=True)
def new_unseen_orders_table(context: dict, area: Area | None = None) -> dict:
    new_orders = (
        Order.objects.filter(status=Order.OrderStatus.DELIVERED, is_seen=False)
        .exclude(is_urgent=True)
        .select_related("genrequest")
        .annotate(
            sample_count=models.Case(
                models.When(
                    extractionorder__isnull=False,
                    then=models.Count("extractionorder__samples", distinct=True),
                ),
                models.When(
                    analysisorder__isnull=False,
                    then=models.Count("analysisorder__samples", distinct=True),
                ),
                default=0,
            ),
            delivery_date=models.Case(
                models.When(
                    analysisorder__isnull=False,
                    then="analysisorder__expected_delivery_date",
                ),
                default=models.Value(None, output_field=models.DateField()),
            ),
        )
    )

    if area:
        new_orders = new_orders.filter(genrequest__area=area)

    new_orders = new_orders.order_by("-created_at")

    return {
        "title": "New orders",
        "table": NewUnseenOrderTable(new_orders),
        "count": new_orders.count(),
        "request": context.get("request"),
    }


@register.inclusion_tag("staff/components/order_table.html", takes_context=True)
def assigned_orders_table(context: dict) -> dict:
    user = context.get("user")

    assigned_orders = (
        Order.objects.filter(
            status__in=[
                Order.OrderStatus.PROCESSING,
                Order.OrderStatus.DELIVERED,
            ],
            responsible_staff=user,
            is_seen=True,
        )
        .select_related("genrequest")
        .annotate(
            isolated_sample_count=models.Case(
                models.When(
                    extractionorder__isnull=False,
                    then=models.Count(
                        "extractionorder__samples",
                        filter=models.Q(extractionorder__samples__is_isolated=True),
                        distinct=True,
                    ),
                )
            ),
            sample_count=models.Case(
                models.When(
                    extractionorder__isnull=False,
                    then=models.Count("extractionorder__samples", distinct=True),
                ),
                default=0,
            ),
            priority=models.Case(
                models.When(is_urgent=True, then=Order.OrderPriority.URGENT),
                models.When(is_prioritized=True, then=Order.OrderPriority.PRIORITIZED),
                default=1,
            ),
        )
        .order_by(
            "-priority",
            models.Case(
                models.When(status=Order.OrderStatus.PROCESSING, then=0),
                models.When(status=Order.OrderStatus.DELIVERED, then=1),
                models.When(status=Order.OrderStatus.COMPLETED, then=2),
                default=3,
                output_field=models.IntegerField(),
            ),
            "-created_at",
        )
    )

    return {
        "title": "My orders",
        "table": AssignedOrderTable(assigned_orders),
        "count": assigned_orders.count(),
        "request": context.get("request"),
    }


@register.inclusion_tag("staff/components/order_table.html", takes_context=True)
def draft_orders_table(context: dict, area: Area) -> dict:
    draft_orders = (
        Order.objects.filter(status=Order.OrderStatus.DRAFT)
        .select_related("genrequest")
        .annotate(
            sample_count=models.Count("extractionorder__samples", distinct=True),
            priority=models.Case(
                models.When(is_urgent=True, then=Order.OrderPriority.URGENT),
                default=1,
            ),
            delivery_date=models.Case(
                models.When(
                    analysisorder__isnull=False,
                    then="analysisorder__expected_delivery_date",
                ),
                default=models.Value(None, output_field=models.DateField()),
            ),
        )
        .order_by("-priority", "-created_at")
    )

    if area:
        draft_orders = draft_orders.filter(genrequest__area=area)

    return {
        "title": "Draft orders",
        "table": DraftOrderTable(draft_orders),
        "count": draft_orders.count(),
        "request": context.get("request"),
    }


@register.inclusion_tag("../templates/components/order-detail.html")
def extraction_order_detail_table(order: Order) -> dict:
    fields = {
        "Order ID": order.id,
        "Genetic Project": order.genrequest,
        "Species": ", ".join(str(s) for s in order.species.all()),
        "Status": render_status_helper(order.status),
        "Name": order.name,
        "Notes": "-" if order.notes == "" else order.notes,
        "Confirmed at": order.confirmed_at.strftime("%d.%m.%Y")
        if order.confirmed_at
        else "Not confirmed",
    }
    return {"fields": fields, "header": "Order"}


@register.inclusion_tag("../templates/components/order-detail.html")
def extraction_order_samples_detail_table(order: Order, analysis_orders: list) -> dict:
    sample_types = dict(Counter(order.samples.values_list("type__name", flat=True)))

    fields = {
        "Delivered samples": order.samples.count(),
        "Sample types": ", ".join(f"{t} ({c})" for t, c in sample_types.items()),
        "Return samples": render_boolean(order.return_samples),
        "Needs GUID": render_boolean(order.needs_guid),
        "Are samples already isolated?": render_boolean(order.pre_isolated),
        "Connected to analysis orders": generate_order_links(analysis_orders),
    }
    return {
        "fields": fields,
        "header": "Samples",
    }


@register.inclusion_tag("../templates/components/order-detail.html")
def analysis_order_detail_table(order: Order) -> dict:
    fields = {
        "Order ID": order.id,
        "Genetic Project": order.genrequest,
        "Status": render_status_helper(order.status),
        "Name": order.name,
        "Notes": "-" if order.notes == "" else order.notes,
        "Confirmed at": order.confirmed_at.strftime("%d.%m.%Y")
        if order.confirmed_at
        else "Not confirmed",
        "Deadline": order.expected_delivery_date.strftime("%d.%m.%Y")
        if order.expected_delivery_date
        else "Not specified",
    }
    return {"fields": fields, "header": "Order"}


@register.inclusion_tag("../templates/components/order-detail.html")
def analysis_order_samples_detail_table(order: Order, extraction_orders: dict) -> dict:
    extraction_order_links = format_html_join(
        "<br>",
        "{} ({})",
        (
            (
                generate_order_links([extraction_order]),
                f"{count} sample{'s' if count > 1 else ''}",
            )
            for extraction_order, count in extraction_orders.items()
        ),
    )

    fields = {
        "Number of samples": order.samples.count(),
        "Markers": ", ".join(marker.name for marker in order.markers.all())
        if order.markers.exists()
        else "No markers",
        "Samples from extraction order": extraction_order_links or "-",
    }

    return {
        "fields": fields,
        "header": "Samples",
    }


@register.inclusion_tag("../templates/components/order-detail.html")
def contact_detail_table(order: Order) -> dict:
    # Default values
    result_contacts_html = "—"

    # Only fetch contacts if it's an AnalysisOrder instance
    if isinstance(order, AnalysisOrder):
        result_contacts = (
            AnalysisOrderResultsCommunication.objects.filter(analysis_order=order)
            .values_list("contact_person_results", "contact_email_results")
            .distinct()
        )
        if result_contacts:
            result_contacts_html = format_html_join(
                "\n",
                '<div>{} — <a href="mailto:{}" class="text-primary underline !text-primary">{}</a></div>',  # noqa: E501
                [(name, email, email) for name, email in result_contacts],
            )

    fields = {
        "Samples owner of genetic project": order.genrequest.samples_owner,
        "Responsible genetic researcher": order.contact_person,
        "Responsible genetic researcher email": order.contact_email,
        "Contact name and email for analysis results": result_contacts_html,
    }

    return {
        "fields": fields,
        "header": "Contact",
    }
