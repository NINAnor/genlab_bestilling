from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from ..models import AnalysisOrder, EquipmentOrder, Order, Sample
from ..views import ActionView
from .filters import AnalysisOrderFilter, SampleFilter
from .tables import AnalysisOrderTable, EquipmentOrderTable, SampleTable


class StaffMixin(LoginRequiredMixin):
    def get_template_names(self) -> list[str]:
        names = super().get_template_names()
        return [name.replace("genlab_bestilling", "staff") for name in names]


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


class SamplesListView(StaffMixin, SingleTableMixin, FilterView):
    table_pagination = False

    model = Sample
    table_class = SampleTable
    filterset_class = SampleFilter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("type", "location", "species")
            .filter(order=self.kwargs["pk"])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["analysis"] = AnalysisOrder.objects.get(pk=self.kwargs.get("pk"))
        return context


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
