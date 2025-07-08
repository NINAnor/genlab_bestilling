from django import template
from django.db import models

from genlab_bestilling.models import Area, Order

from ..tables import (
    AssignedOrderTable,
    NewSeenOrderTable,
    NewUnseenOrderTable,
    UrgentOrderTable,
)

register = template.Library()


@register.inclusion_tag("staff/components/order_table.html", takes_context=True)
def urgent_orders_table(context: dict, area: Area | None = None) -> dict:
    urgent_orders = (
        Order.objects.filter(
            is_urgent=True,
        )
        .exclude(status=Order.OrderStatus.DRAFT)
        .select_related("genrequest")
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
        Order.objects.filter(status=Order.OrderStatus.DELIVERED, is_seen=True)
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
        )
    )

    if area:
        new_orders = new_orders.filter(genrequest__area=area)

    new_orders = new_orders.order_by("-priority", "-created_at")

    return {
        "title": "New seen orders",
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
            )
        )
    )

    if area:
        new_orders = new_orders.filter(genrequest__area=area)

    new_orders = new_orders.order_by("-created_at")

    return {
        "title": "New unseen orders",
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
                Order.OrderStatus.COMPLETED,
            ],
            responsible_staff=user,
        )
        .select_related("genrequest")
        .annotate(
            sample_count=models.Count("extractionorder__samples", distinct=True),
            priority=models.Case(
                models.When(is_urgent=True, then=Order.OrderPriority.URGENT),
                models.When(is_prioritized=True, then=Order.OrderPriority.PRIORITIZED),
                default=1,
            ),
        )
        .order_by(
            models.Case(
                models.When(status=Order.OrderStatus.PROCESSING, then=0),
                models.When(status=Order.OrderStatus.DELIVERED, then=1),
                models.When(status=Order.OrderStatus.COMPLETED, then=2),
                default=3,
                output_field=models.IntegerField(),
            ),
            "-priority",
            "-created_at",
        )
    )

    return {
        "title": "My orders",
        "table": AssignedOrderTable(assigned_orders),
        "count": assigned_orders.count(),
        "request": context.get("request"),
    }
