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
    Order,
    Sample,
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


def render_status_helper(status: Order.OrderStatus) -> str:
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

    classes = status_colors.get(status, "bg-gray-100 text-gray-800")
    text = status_text.get(status, "Unknown")

    return mark_safe(  # noqa: S308
        f'<span class="px-2 py-1 text-xs font-medium rounded-full text-nowrap {classes}">{text}</span>'  # noqa: E501
    )


class OrderStatusMixinTable(tables.Table):
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
        return render_status_helper(record.status)


class SampleStatusMixinTable(tables.Table):
    sample_status = tables.Column(
        verbose_name="Sample Status", empty_values=(), orderable=True
    )

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

    def order_sample_status(
        self, records: Sequence[Any], is_descending: bool
    ) -> tuple[list[Any], bool]:
        def get_status_value(record: Any) -> int:
            if isinstance(record.order, ExtractionOrder):
                if record.is_isolated:
                    return self.STATUS_PRIORITY["Isolated"]
                if record.is_plucked:
                    return self.STATUS_PRIORITY["Plucked"]
                if record.is_marked:
                    return self.STATUS_PRIORITY["Marked"]
                return self.STATUS_PRIORITY["Not started"]

            # fallback for other types of orders
            return self.STATUS_PRIORITY.get(
                getattr(record.order, "sample_status", ""), -1
            )

        sorted_records = sorted(records, key=get_status_value, reverse=is_descending)
        return (sorted_records, True)
