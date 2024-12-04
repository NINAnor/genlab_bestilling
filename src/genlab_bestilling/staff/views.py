from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from ..models import AnalysisOrder, EquipmentOrder, ExtractionPlate, Order, Sample
from ..views import ActionView
from .filters import (
    AnalysisOrderFilter,
    ExtractionPlateFilter,
    OrderSampleFilter,
    SampleFilter,
)
from .tables import (
    AnalysisOrderTable,
    EquipmentOrderTable,
    OrderSampleTable,
    PlateTable,
    SampleTable,
)


class StaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    def get_template_names(self) -> list[str]:
        names = super().get_template_names()
        return [name.replace("genlab_bestilling", "staff") for name in names]

    def test_func(self):
        return self.request.user.is_genlab_staff()


class AnalysisOrderListView(StaffMixin, SingleTableMixin, FilterView):
    model = AnalysisOrder
    table_class = AnalysisOrderTable
    filterset_class = AnalysisOrderFilter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "genrequest",
                "polymorphic_ctype",
                "genrequest__project",
                "genrequest__area",
            )
            .prefetch_related("species", "sample_types", "genrequest__analysis_types")
        )


class ExtractionPlateListView(StaffMixin, SingleTableMixin, FilterView):
    model = ExtractionPlate
    table_class = PlateTable
    filterset_class = ExtractionPlateFilter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related()
            .prefetch_related("sample_positions")
            .annotate(samples_count=models.Count("sample_positions"))
        )


class EqupimentOrderListView(StaffMixin, SingleTableMixin, FilterView):
    model = EquipmentOrder
    table_class = EquipmentOrderTable
    filterset_class = AnalysisOrderFilter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "genrequest",
                "polymorphic_ctype",
                "genrequest__project",
                "genrequest__area",
            )
            .prefetch_related("species", "sample_types", "genrequest__analysis_types")
        )


class AnalysisOrderDetailView(StaffMixin, DetailView):
    model = AnalysisOrder


class EquipmentOrderDetailView(StaffMixin, DetailView):
    model = EquipmentOrder


class OrderSamplesListView(StaffMixin, SingleTableMixin, FilterView):
    table_pagination = False

    model = Sample
    table_class = OrderSampleTable
    filterset_class = OrderSampleFilter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("type", "location", "species")
            .prefetch_related("plate_positions")
            .filter(order=self.kwargs["pk"])
            .order_by("species__name", "year", "location__name", "name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["analysis"] = AnalysisOrder.objects.get(pk=self.kwargs.get("pk"))
        return context


class SamplesListView(StaffMixin, SingleTableMixin, FilterView):
    model = Sample
    table_class = SampleTable
    filterset_class = SampleFilter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("type", "location", "species", "order")
            .prefetch_related("plate_positions")
            .exclude(order__status=Order.OrderStatus.DRAFT)
            .order_by("species__name", "year", "location__name", "name")
        )


class ManaullyCheckedOrderActionView(SingleObjectMixin, ActionView):
    model = Order

    def get_queryset(self):
        return super().get_queryset().filter(status=Order.OrderStatus.CONFIRMED)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Any) -> HttpResponse:
        try:
            # TODO: check state transition
            self.object.order_manually_checked()
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _(
                    "The order was checked, GenLab IDs and "
                    + "extraction plates will be generated"
                ),
            )
        except Exception as e:
            messages.add_message(
                self.request,
                messages.ERROR,
                f'Error: {",".join(map(lambda error: str(error), e.detail))}',
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy(
            f"staff:order-{self.object.get_type()}-detail",
            kwargs={"pk": self.object.id},
        )

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())


class OrderToDraftActionView(SingleObjectMixin, ActionView):
    model = Order

    def get_queryset(self):
        return super().get_queryset().filter(status=Order.OrderStatus.CONFIRMED)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Any) -> HttpResponse:
        try:
            # TODO: check state transition
            self.object.to_draft()
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _("The order was converted back to a draft"),
            )
        except Exception as e:
            messages.add_message(
                self.request,
                messages.ERROR,
                f'Error: {",".join(map(lambda error: str(error), e.detail))}',
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy(f"staff:order-{self.object.get_type()}-list")

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())
