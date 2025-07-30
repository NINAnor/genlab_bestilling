from typing import Any

import django_tables2 as tables
from django.db.models import Case, IntegerField, Value, When
from django.db.models.query import QuerySet
from django.http import QueryDict
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import View

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

        return format_html('<a href="{}" class="underline">{}</a>', url, str(record))


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

    return format_html(
        '<span class="px-2 py-1 text-xs font-medium rounded-full text-nowrap {}">{}</span>',  # noqa: E501
        classes,
        text,
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
            status_order=Case(
                When(status=Order.OrderStatus.DELIVERED, then=0),
                When(status=Order.OrderStatus.DRAFT, then=1),
                When(status=Order.OrderStatus.PROCESSING, then=2),
                When(status=Order.OrderStatus.COMPLETED, then=3),
                default=Value(4),
                output_field=IntegerField(),
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
        status = "Unknown"

        if order:
            if record.is_isolated:
                status = "Isolated"
            elif record.is_plucked:
                status = "Plucked"
            elif record.is_marked:
                status = "Marked"
            else:
                status = "Not started"

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

        return format_html(
            '<span class="px-2 py-1 text-xs font-medium rounded-full whitespace-nowrap {}">{}</span>',  # noqa: E501
            color_class,
            status,
        )

    def order_sample_status(
        self, queryset: QuerySet[Sample], is_descending: bool
    ) -> tuple[QuerySet[Sample], bool]:
        prefix = "-" if is_descending else ""
        status_order = Case(
            When(is_isolated=True, then=Value(3)),
            When(is_plucked=True, then=Value(2)),
            When(is_marked=True, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
        annotated_queryset = queryset.annotate(sample_status_order=status_order)
        sorted_queryset = annotated_queryset.order_by(f"{prefix}sample_status_order")
        return (sorted_queryset, True)


class PriorityMixinTable(tables.Table):
    priority = tables.TemplateColumn(
        orderable=True,
        verbose_name="Priority",
        template_name="staff/components/priority_column.html",
    )

    def order_priority(
        self, queryset: QuerySet[Order], is_descending: bool
    ) -> tuple[QuerySet[Order], bool]:
        prefix = "-" if is_descending else ""
        queryset = queryset.annotate(
            priority_order=Case(
                When(is_urgent=True, then=2),
                When(is_prioritized=True, then=1),
                default=0,
                output_field=IntegerField(),
            )
        )
        sorted_by_priority = queryset.order_by(f"{prefix}priority_order")

        return (sorted_by_priority, True)


class SafeRedirectMixin(View):
    """Mixin to provide safe redirection after a successful form submission.
    This mixin checks for a 'next' parameter in the request and validates it
    to ensure it is a safe URL before redirecting. If no valid 'next' URL is found,
    it falls back to a method that must be implemented in the view to define
    a default redirect URL.
    """

    next_param = "next"

    def get_fallback_url(self) -> str:
        msg = "You must override get_fallback_url()"
        raise NotImplementedError(msg)

    def get_next_url_from_request(self) -> str | None:
        """
        Safely extract the next URL from POST and GET data.
        Returns a stripped string if present and non-empty, else None.
        """
        next_url = self.request.POST.get(self.next_param)
        if not next_url:
            next_url = self.request.GET.get(self.next_param)
        if isinstance(next_url, str):
            next_url = next_url.strip()
            if next_url:
                return next_url
        return None

    def has_next_url(self, next_url: str | None = None) -> bool:
        """
        Check if a valid and safe next URL is present in the request.
        Optionally accepts a next_url to avoid duplicate extraction.
        """
        if next_url is None:
            next_url = self.get_next_url_from_request()
        if not next_url:
            return False
        return url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        )

    def get_next_url(self) -> str:
        """
        Return a safe next URL if available, otherwise fallback URL.
        """
        next_url = self.get_next_url_from_request()
        if next_url and self.has_next_url(next_url):
            return next_url
        return self.get_fallback_url()


class HideStatusesByDefaultMixin:
    HIDDEN_STATUSES = [Order.OrderStatus.DRAFT, Order.OrderStatus.COMPLETED]

    # Hide statuses by default unless user specifically selects them
    def exclude_hidden_statuses(self, queryset: QuerySet, data: QueryDict) -> QuerySet:
        selected_statuses = data.getlist("status")
        if not selected_statuses:  # No statuses selected by user
            return queryset.exclude(status__in=self.HIDDEN_STATUSES)

        return queryset
