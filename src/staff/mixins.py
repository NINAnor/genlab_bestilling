import django_tables2 as tables
from django.utils.safestring import mark_safe

from genlab_bestilling.models import (
    AnalysisOrder,
    EquipmentOrder,
    ExtractionOrder,
    Order,
)


def render_status_helper(value: Order.OrderStatus) -> str:
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
    color_class = status_colors.get(value, "bg-gray-100 text-gray-800")
    status_text = status_text.get(value, "Unknown")
    return mark_safe(  # noqa: S308
        f'<span class="px-2 py-1 text-xs font-medium text-nowrap rounded-full {color_class}">{status_text}</span>'  # noqa: E501
    )


class StatusMixinTable(tables.Table):
    status = tables.Column(
        orderable=False,
        verbose_name="Status",
    )

    def render_status(self, value: Order.OrderStatus, record: Order) -> str:
        return render_status_helper(record.status)


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
