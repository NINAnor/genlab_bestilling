from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.db.models import Case, Count, IntegerField, QuerySet, Value, When
from django.db.models.functions import Cast
from django.forms import Form
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, TemplateView, View
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from genlab_bestilling.models import (
    AnalysisOrder,
    Area,
    EquipmentOrder,
    ExtractionOrder,
    ExtractionPlate,
    Genrequest,
    IsolationMethod,
    Order,
    Sample,
    SampleIsolationMethod,
    SampleMarkerAnalysis,
)
from nina.models import Project
from shared.sentry import report_errors
from shared.views import ActionView

from .filters import (
    AnalysisOrderFilter,
    ExtractionOrderFilter,
    ExtractionPlateFilter,
    OrderSampleFilter,
    SampleFilter,
    SampleLabFilter,
    SampleMarkerOrderFilter,
)
from .forms import ExtractionPlateForm, OrderStaffForm
from .tables import (
    AnalysisOrderTable,
    EquipmentOrderTable,
    ExtractionOrderTable,
    OrderAnalysisSampleTable,
    OrderExtractionSampleTable,
    PlateTable,
    ProjectTable,
    SampleStatusTable,
    SampleTable,
)


class StaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    def get_template_names(self) -> list[str]:
        names = super().get_template_names()  # type: ignore[misc]
        return [
            name.replace("genlab_bestilling", "staff").replace("nina", "staff")
            for name in names
        ]

    def test_func(self) -> bool:
        return self.request.user.is_superuser or self.request.user.is_genlab_staff()  # type: ignore[attr-defined]


class DashboardView(StaffMixin, TemplateView):
    template_name = "staff/dashboard.html"

    def get_area_from_query(self) -> Area | None:
        area_id = self.request.GET.get("area")
        if area_id:
            try:
                return Area.objects.get(pk=area_id)
            except Area.DoesNotExist:
                return None
        return None

    def get_areas(self) -> QuerySet[Area]:
        return Area.objects.all().order_by("name")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["now"] = now()
        context["areas"] = self.get_areas()
        context["area"] = self.get_area_from_query()

        return context


class AnalysisOrderListView(StaffMixin, SingleTableMixin, FilterView):
    model = AnalysisOrder
    table_class = AnalysisOrderTable
    filterset_class = AnalysisOrderFilter

    def get_queryset(self) -> QuerySet[AnalysisOrder]:
        return (
            super()
            .get_queryset()
            .select_related(
                "genrequest",
                "polymorphic_ctype",
                "genrequest__samples_owner",
                "genrequest__project",
                "genrequest__area",
            )
            .annotate(total_samples=Count("samples"))
        )


class ExtractionOrderListView(StaffMixin, SingleTableMixin, FilterView):
    model = ExtractionOrder
    table_class = ExtractionOrderTable
    filterset_class = ExtractionOrderFilter

    def get_queryset(self) -> QuerySet[ExtractionOrder]:
        return (
            super()
            .get_queryset()
            .select_related(
                "genrequest",
                "genrequest__samples_owner",
                "polymorphic_ctype",
                "genrequest__project",
                "genrequest__area",
            )
            .prefetch_related("species", "sample_types")
            .annotate(
                total_samples=Count("samples"),
                total_samples_isolated=models.Count(
                    "samples", filter=models.Q(samples__is_isolated=True)
                ),
            )
        )


class ExtractionPlateListView(StaffMixin, SingleTableMixin, FilterView):
    model = ExtractionPlate
    table_class = PlateTable
    filterset_class = ExtractionPlateFilter

    def get_queryset(self) -> QuerySet[ExtractionPlate]:
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

    def get_queryset(self) -> QuerySet[EquipmentOrder]:
        return (
            super()
            .get_queryset()
            .select_related(
                "genrequest",
                "polymorphic_ctype",
                "genrequest__samples_owner",
                "genrequest__project",
                "genrequest__area",
            )
            .prefetch_related("sample_types")
        )


class AnalysisOrderDetailView(StaffMixin, DetailView):
    model = AnalysisOrder

    # Retrieves extraction orders associated with the samples in the analysis order
    def get_extraction_orders_for_samples(
        self, samples: QuerySet[Sample]
    ) -> QuerySet[ExtractionOrder]:
        return ExtractionOrder.objects.filter(samples__in=samples).distinct()

    # Retrieves the sample counts for each extraction order
    # This is used to display the number of samples from each extraction order
    # that are part of the analysis order
    def get_extraction_order_sample_counts(
        self,
        extraction_orders: QuerySet[ExtractionOrder],
        samples: QuerySet[Sample],
    ) -> dict[ExtractionOrder, int]:
        sample_ids = samples.values_list("id", flat=True)
        return {
            eo: eo.samples.filter(id__in=sample_ids).count() for eo in extraction_orders
        }

    # Checks if the extraction order has multiple analysis orders
    # This is used to determine which type of link to show in the template
    def extraction_has_multiple_analysis_orders(
        self, extraction_orders: QuerySet[ExtractionOrder]
    ) -> bool:
        if len(extraction_orders) == 1:
            extraction_order = get_object_or_404(
                ExtractionOrder, pk=extraction_orders.first()
            )
            analysis_orders = extraction_order.analysis_orders.all()
            return analysis_orders.count() > 1
        return False

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        analysis_order = self.object
        samples = analysis_order.samples.all()
        extraction_orders = self.get_extraction_orders_for_samples(samples)
        extraction_order_sample_counts = self.get_extraction_order_sample_counts(
            extraction_orders, samples
        )

        context["extraction_order_sample_counts"] = extraction_order_sample_counts
        context["extraction_orders"] = extraction_orders
        context["extraction_has_multiple_analysis_orders"] = (
            self.extraction_has_multiple_analysis_orders(extraction_orders)
        )

        return context


class EquipmentOrderDetailView(StaffMixin, DetailView):
    model = EquipmentOrder


class MarkAsSeenView(StaffMixin, DetailView):
    model = Order

    def get_object(self) -> Order:
        return Order.objects.get(pk=self.kwargs["pk"])

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        try:
            order = self.get_object()
            order.toggle_seen()

            messages.success(request, _("Order is marked as seen"))
        except Exception as e:
            report_errors(e)
            messages.error(request, f"Error: {str(e)}")

        return_to = request.POST.get("return_to")
        return HttpResponseRedirect(self.get_return_url(return_to))

    def get_return_url(self, return_to: str | None) -> str:
        if return_to == "dashboard":
            return reverse("staff:dashboard")
        return self.get_object().get_absolute_staff_url()


class ExtractionOrderDetailView(StaffMixin, DetailView):
    model = ExtractionOrder

    def get_analysis_orders_for_samples(
        self, samples: QuerySet[Sample]
    ) -> QuerySet[AnalysisOrder]:
        """
        Retrieves analysis orders associated with the samples in the extraction order.
        """
        return AnalysisOrder.objects.filter(samples__in=samples).distinct()

    def analysis_has_multiple_extraction_orders(
        self, *, analysis_orders: QuerySet[AnalysisOrder]
    ) -> bool:
        """
        Checks if the analysis orders have multiple extraction orders.
        This is used to determine which type of link to show in the template.
        """
        if analysis_orders.count() != 1:
            return False

        analysis_order = analysis_orders.first()

        extraction_order_ids = analysis_order.samples.values_list(  # type: ignore[union-attr] # We have already checked for existance.
            "order_id", flat=True
        ).distinct()
        return extraction_order_ids.count() > 1

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        extraction_order = self.object
        samples = extraction_order.samples.all()
        analysis_orders = self.get_analysis_orders_for_samples(samples=samples)
        context["analysis_orders"] = analysis_orders
        context["analysis_has_multiple_extraction_orders"] = (
            self.analysis_has_multiple_extraction_orders(
                analysis_orders=analysis_orders
            )
        )
        return context


class OrderExtractionSamplesListView(StaffMixin, SingleTableMixin, FilterView):
    table_pagination = False

    model = Sample
    table_class = OrderExtractionSampleTable
    filterset_class = OrderSampleFilter

    def get_queryset(self) -> QuerySet[Sample]:
        queryset = (
            super()
            .get_queryset()
            .select_related("type", "location", "species")
            .prefetch_related("plate_positions")
            .filter(order=self.kwargs["pk"])
        )

        # added to sort based on type (int/str)
        return queryset.annotate(
            name_as_int=Case(
                When(
                    name__regex=r"^\d+$",
                    then=Cast("name", IntegerField()),
                ),
                default=Value(None),
                output_field=IntegerField(),
            )
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        order = ExtractionOrder.objects.get(pk=self.kwargs.get("pk"))
        context["order"] = order
        total_samples = order.samples.count()
        filled_count = order.filled_genlab_count
        context["progress_percent"] = (
            (float(filled_count) / float(total_samples)) * 100
            if total_samples > 0
            else 0
        )
        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        sample_id = request.POST.get("sample_id")

        if sample_id:
            sample = get_object_or_404(Sample, pk=sample_id)
            sample.is_prioritised = not sample.is_prioritised
            sample.save()

        next_url = request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts=request.get_host()
        ):
            return redirect(next_url)

        return self.get(
            request, *args, **kwargs
        )  # Re-render the view with updated data


class OrderAnalysisSamplesListView(StaffMixin, SingleTableMixin, FilterView):
    table_pagination = False

    model = SampleMarkerAnalysis
    table_class = OrderAnalysisSampleTable
    filterset_class = SampleMarkerOrderFilter

    def get_queryset(self) -> QuerySet[SampleMarkerAnalysis]:
        return (
            super()
            .get_queryset()
            .select_related(
                "sample__type", "sample__location", "sample__species", "marker"
            )
            .filter(order=self.kwargs["pk"])
            .prefetch_related("sample__plate_positions")
            .order_by(
                "sample__species__name",
                "sample__year",
                "sample__location__name",
                "sample__name",
            )
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["order"] = AnalysisOrder.objects.get(pk=self.kwargs.get("pk"))
        return context


class SamplesListView(StaffMixin, SingleTableMixin, FilterView):
    table_pagination = False

    model = Sample
    table_class = SampleTable
    filterset_class = SampleFilter

    def get_queryset(self) -> QuerySet[Sample]:
        return (
            super()
            .get_queryset()
            .select_related(
                "type",
                "location",
                "species",
                "order",
                "order__genrequest",
                "order__genrequest__project",
            )
            .prefetch_related(
                "plate_positions",
                "order__responsible_staff",
            )
            .exclude(order__status=Order.OrderStatus.DRAFT)
            .order_by("species__name", "year", "location__name", "name")
        )


class SampleDetailView(StaffMixin, DetailView):
    model = Sample


class SampleLabView(StaffMixin, SingleTableMixin, TemplateView):
    MARKED = "marked"
    PLUCKED = "plucked"
    ISOLATED = "isolated"
    VALID_STATUSES = [MARKED, PLUCKED, ISOLATED]

    disable_pagination = False
    template_name = "staff/sample_lab.html"
    table_class = SampleStatusTable
    filterset_class = SampleLabFilter

    def get_order(self) -> ExtractionOrder:
        if not hasattr(self, "_order"):
            self._order = get_object_or_404(ExtractionOrder, pk=self.kwargs["pk"])
        return self._order

    def get_table_data(self) -> QuerySet[Sample]:
        order = self.get_order()
        samples = Sample.objects.filter(order=order, genlab_id__isnull=False)

        for sample in samples:
            sample.selected_isolation_method = (
                sample.isolation_method.first()
                if sample.isolation_method.exists()
                else None
            )

        return samples

    def get_isolation_methods(self) -> QuerySet[IsolationMethod, str]:
        order = self.get_order()
        samples = Sample.objects.filter(order=order)
        species_ids = samples.values_list("species_id", flat=True).distinct()

        return (
            IsolationMethod.objects.filter(species_id__in=species_ids)
            .values_list("name", flat=True)
            .distinct()
        )

    def get_base_fields(self) -> list[str]:
        return self.VALID_STATUSES

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        order = self.get_order()
        samples = self.get_table_data()

        # Instantiate the filter with the current GET parameters
        filterset = self.filterset_class(self.request.GET, queryset=samples)
        table = self.table_class(filterset.qs, request=self.request)

        context.update(
            {
                "order": order,
                "statuses": self.get_base_fields(),
                "isolation_methods": self.get_isolation_methods(),
                "filter": filterset,
                "table": table,
            }
        )
        return context

    def get_success_url(self) -> str:
        return reverse(
            "staff:order-extraction-samples-lab", kwargs={"pk": self.get_order().pk}
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        status_name = request.POST.get("status")
        selected_ids = request.POST.getlist(f"checked-{self.get_order().pk}")
        isolation_method = request.POST.get("isolation_method")

        if not selected_ids:
            messages.error(request, "No samples selected.")
            return HttpResponseRedirect(self.get_success_url())

        order = self.get_order()

        # Get the selected samples
        samples = Sample.objects.filter(id__in=selected_ids)

        if status_name:
            self.assign_status_to_samples(samples, status_name, request)
            if status_name == self.ISOLATED:
                # Cannot use "samples" here
                # because we need to check all samples in the order
                self.check_all_isolated(Sample.objects.filter(order=order))
        if isolation_method:
            self.update_isolation_methods(samples, isolation_method, request)
        return HttpResponseRedirect(self.get_success_url())

    def statuses_with_lower_or_equal_priority(self, status_name: str) -> list[str]:
        index = self.VALID_STATUSES.index(status_name)
        return self.VALID_STATUSES[: index + 1]

    def assign_status_to_samples(
        self,
        samples: QuerySet,
        status_name: str,
        request: HttpRequest,
    ) -> None:
        if status_name not in self.VALID_STATUSES:
            messages.error(request, f"Status '{status_name}' is not valid.")
            return

        statuses_to_turn_on = self.statuses_with_lower_or_equal_priority(status_name)
        field_name = f"is_{status_name}"

        samples_to_turn_off_ids = list(
            samples.filter(**{field_name: True}).values_list("id", flat=True)
        )
        samples_to_turn_on_ids = list(
            samples.filter(**{field_name: False}).values_list("id", flat=True)
        )

        Sample.objects.filter(id__in=samples_to_turn_off_ids).update(
            **{field_name: False}
        )

        update_dict = {f"is_{status}": True for status in statuses_to_turn_on}
        Sample.objects.filter(id__in=samples_to_turn_on_ids).update(**update_dict)

        messages.success(request, "Samples updated successfully")

    # Checks if all samples in the order are isolated
    # If they are, it updates the order status to completed
    def check_all_isolated(self, samples: QuerySet) -> None:
        if not samples.filter(is_isolated=False).exists():
            self.get_order().to_next_status()
            messages.success(
                self.request,
                "All samples are isolated. The order status is updated to completed.",
            )
        elif self.get_order().status == Order.OrderStatus.COMPLETED:
            self.get_order().to_processing()
            messages.success(
                self.request,
                "Not all samples are isolated. The order status is updated to processing.",  # noqa: E501
            )

    def update_isolation_methods(
        self, samples: QuerySet, isolation_method: str, request: HttpRequest
    ) -> None:
        selected_isolation_method = IsolationMethod.objects.filter(
            name=isolation_method
        ).first()

        try:
            im = IsolationMethod.objects.filter(
                name=selected_isolation_method.name
            ).first()
        except IsolationMethod.DoesNotExist:
            messages.error(
                request,
                f"Isolation method '{selected_isolation_method.name}' not found.",
            )
            return

        for sample in samples:
            # Remove any existing methods for this sample
            SampleIsolationMethod.objects.filter(sample=sample).delete()

            # Add the new one
            SampleIsolationMethod.objects.create(sample=sample, isolation_method=im)
        messages.success(
            request,
            f"{samples.count()} samples updated with isolation method '{isolation_method}'.",  # noqa: E501
        )


class UpdateInternalNote(StaffMixin, ActionView):
    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        sample_id = request.POST.get("sample_id")
        field_name = request.POST.get("field_name")
        field_value = request.POST.get("field_value")

        if not sample_id or not field_name or field_value is None:
            return JsonResponse({"error": "Invalid input"}, status=400)

        try:
            sample = Sample.objects.get(id=sample_id)

            if field_name == "internal_note-input":
                sample.internal_note = field_value
                sample.save()

            return JsonResponse({"success": True})
        except Sample.DoesNotExist:
            return JsonResponse({"error": "Sample not found"}, status=404)


class StaffEditView(StaffMixin, SingleObjectMixin, TemplateView):
    form_class = OrderStaffForm
    template_name = "staff/order_staff_edit.html"

    def get_queryset(self) -> QuerySet[Order] | QuerySet[Genrequest]:
        model_type = self._get_model_type()
        if model_type == "genrequest":
            return Genrequest.objects.all()
        return Order.objects.all()

    def _get_model_type(self) -> str:
        """Returns model type based on request data."""
        return self.kwargs["model_type"]

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        form = self.form_class(request.POST, order=self.object)

        if form.is_valid():
            responsible_staff = form.cleaned_data.get("responsible_staff", [])
            self.object.responsible_staff.set(responsible_staff)

            messages.add_message(
                request,
                messages.SUCCESS,
                "Staff assignment updated successfully",
            )
            model_type = self._get_model_type()
            return HttpResponseRedirect(self.get_success_url(model_type))

        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["object"] = self.object
        context["form"] = self.form_class(order=self.object)
        context["model_type"] = self._get_model_type()

        return context

    def get_success_url(self, model_type: str | None) -> str:
        if model_type == "genrequest":
            return reverse(
                "genrequest-detail",
                kwargs={"pk": self.object.id},
            )

        return reverse_lazy(
            f"staff:order-{model_type}-detail",
            kwargs={"pk": self.object.pk},
        )


class OrderToDraftActionView(SingleObjectMixin, ActionView):
    model = Order

    def get_queryset(self) -> QuerySet[Order]:
        return super().get_queryset()

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object: Order = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            # TODO: check state transition
            self.object.to_draft()
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _("The order was converted back to a draft"),
            )
        except Exception as e:
            report_errors(e)
            messages.add_message(
                self.request,
                messages.ERROR,
                f"Error: {str(e)}",
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy(f"staff:order-{self.object.get_type()}-list")

    def form_invalid(self, form: Form) -> HttpResponse:
        return HttpResponseRedirect(self.get_success_url())


class OrderToNextStatusActionView(SingleObjectMixin, ActionView):
    model = Order

    def get_queryset(self) -> QuerySet[Order]:
        return Order.objects.all()

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            # TODO: check state transition
            self.object.to_next_status()
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _(f"The order status changed to {self.object.get_status_display()}"),
            )
        except Exception as e:
            report_errors(e)
            messages.add_message(
                self.request,
                messages.ERROR,
                f"Error: {str(e)}",
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy(
            f"staff:order-{self.object.get_type()}-detail",
            kwargs={"pk": self.object.pk},
        )

    def form_invalid(self, form: Form) -> HttpResponse:
        return HttpResponseRedirect(self.get_success_url())


class GenerateGenlabIDsView(SingleObjectMixin, StaffMixin, View):
    model = ExtractionOrder

    def get_object(self) -> ExtractionOrder:
        return ExtractionOrder.objects.get(pk=self.kwargs["pk"])

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()

        # getlist automatically reads the values in the order presented in the table
        selected_ids = request.POST.getlist("checked")

        if not selected_ids:
            messages.error(request, "No samples were selected.")
            return HttpResponseRedirect(self.get_return_url())

        try:
            self.object.order_selected_checked(selected_samples=selected_ids)
            messages.add_message(
                request,
                messages.SUCCESS,
                _(f"Genlab IDs generated for {len(selected_ids)} samples."),
            )
        except Exception as e:
            report_errors(e)
            messages.add_message(
                request,
                messages.ERROR,
                f"Error: {str(e)}",
            )

        return HttpResponseRedirect(self.get_return_url())

    def get_return_url(self) -> str:
        return reverse_lazy(
            "staff:order-extraction-samples", kwargs={"pk": self.object.pk}
        )


class ExtractionPlateCreateView(StaffMixin, CreateView):
    model = ExtractionPlate
    form_class = ExtractionPlateForm

    def get_success_url(self) -> str:
        return reverse_lazy("staff:plates-list")


class ExtractionPlateDetailView(StaffMixin, DetailView):
    model = ExtractionPlate


class SampleReplicaActionView(SingleObjectMixin, ActionView):
    model = Sample

    def get_queryset(self) -> QuerySet[Sample]:
        return (
            super()
            .get_queryset()
            .select_related("order")
            .filter(order__status=Order.OrderStatus.DELIVERED)
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponse:
        try:
            # TODO: check state transition
            self.object = self.object.create_replica()
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _("The sample was replicated"),
            )
        except Exception as e:
            report_errors(e)
            messages.add_message(
                self.request,
                messages.ERROR,
                f"Error: {str(e)}",
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy("staff:samples-detail", kwargs={"id": self.object.pk})

    def form_invalid(self, form: Form) -> HttpResponse:
        return HttpResponseRedirect(self.get_success_url())


class ProjectListView(StaffMixin, SingleTableMixin, FilterView):
    model = Project
    table_class = ProjectTable
    filterset_fields = {
        "number": ["startswith"],
        "name": ["startswith"],
        "verified_at": ["isnull"],
        "active": ["exact"],
    }


class ProjectDetailView(StaffMixin, DetailView):
    model = Project


class ProjectValidateActionView(SingleObjectMixin, ActionView):
    model = Project

    def get_queryset(self) -> QuerySet[Project]:
        return super().get_queryset().filter(verified_at=None)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponse:
        self.object.verified_at = now()
        self.object.save()
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _("The project is verified"),
        )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy("staff:projects-detail", kwargs={"pk": self.object.pk})

    def form_invalid(self, form: Form) -> HttpResponse:
        return HttpResponseRedirect(self.get_success_url())


class OrderPrioritizedAdminView(StaffMixin, ActionView):
    def get_success_url(self) -> str:
        next_url = self.request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url

        return reverse("staff:dashboard")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        pk = kwargs.get("pk")
        order = Order.objects.get(pk=pk)
        order.toggle_prioritized()

        return redirect(self.get_success_url())
