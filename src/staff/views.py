from collections import defaultdict
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.db.models import Count
from django.forms import Form
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, TemplateView
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
    SampleStatusAssignment,
)
from nina.models import Project
from shared.views import ActionView

from .filters import (
    AnalysisOrderFilter,
    ExtractionPlateFilter,
    OrderSampleFilter,
    SampleFilter,
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
        # type: ignore[misc] # TODO: This doesn't look right, fix later.
        names = super().get_template_names()
        return [
            name.replace("genlab_bestilling", "staff").replace("nina", "staff")
            for name in names
        ]

    def test_func(self) -> bool:
        return self.request.user.is_superuser or self.request.user.is_genlab_staff()


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

    def get_areas(self) -> models.QuerySet[Area]:
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

    def get_queryset(self) -> models.QuerySet[AnalysisOrder]:
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
        )


class ExtractionOrderListView(StaffMixin, SingleTableMixin, FilterView):
    model = ExtractionOrder
    table_class = ExtractionOrderTable
    filterset_class = AnalysisOrderFilter

    def get_queryset(self) -> models.QuerySet[ExtractionOrder]:
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
            .annotate(sample_count=Count("samples"))
        )


class ExtractionPlateListView(StaffMixin, SingleTableMixin, FilterView):
    model = ExtractionPlate
    table_class = PlateTable
    filterset_class = ExtractionPlateFilter

    def get_queryset(self) -> models.QuerySet[ExtractionPlate]:
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

    def get_queryset(self) -> models.QuerySet[EquipmentOrder]:
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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        analysis_order = self.object
        context["extraction_order"] = analysis_order.from_order
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
            messages.error(request, f"Error: {str(e)}")

        return_to = request.POST.get("return_to")
        return HttpResponseRedirect(self.get_return_url(return_to))

    def get_return_url(self, return_to: str) -> str:
        if return_to == "dashboard":
            return reverse("staff:dashboard")
        else:
            return self.get_object().get_absolute_staff_url()


class ExtractionOrderDetailView(StaffMixin, DetailView):
    model = ExtractionOrder

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        extraction_order = self.object
        context["analysis_orders"] = extraction_order.analysis_orders.all()
        return context


class OrderExtractionSamplesListView(StaffMixin, SingleTableMixin, FilterView):
    table_pagination = False

    model = Sample
    table_class = OrderExtractionSampleTable
    filterset_class = OrderSampleFilter

    def get_queryset(self) -> models.QuerySet[Sample]:
        return (
            super()
            .get_queryset()
            .select_related("type", "location", "species")
            .prefetch_related("plate_positions")
            .filter(order=self.kwargs["pk"])
            .order_by("species__name", "year", "location__name", "name")
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["order"] = ExtractionOrder.objects.get(pk=self.kwargs.get("pk"))
        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        sample_id = request.POST.get("sample_id")

        if sample_id:
            sample = get_object_or_404(Sample, pk=sample_id)
            sample.is_prioritised = not sample.is_prioritised
            sample.save()

        return self.get(
            request, *args, **kwargs
        )  # Re-render the view with updated data


class OrderAnalysisSamplesListView(StaffMixin, SingleTableMixin, FilterView):
    table_pagination = False

    model = SampleMarkerAnalysis
    table_class = OrderAnalysisSampleTable
    filterset_class = SampleMarkerOrderFilter

    def get_queryset(self) -> models.QuerySet[SampleMarkerAnalysis]:
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
    model = Sample
    table_class = SampleTable
    filterset_class = SampleFilter

    def get_queryset(self) -> models.QuerySet[Sample]:
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
            .prefetch_related("plate_positions")
            .exclude(order__status=Order.OrderStatus.DRAFT)
            .order_by("species__name", "year", "location__name", "name")
        )


class SampleDetailView(StaffMixin, DetailView):
    model = Sample


class SampleLabView(StaffMixin, TemplateView):
    disable_pagination = False
    template_name = "staff/sample_lab.html"
    table_class = SampleStatusTable

    def get_order(self) -> ExtractionOrder:
        if not hasattr(self, "_order"):
            self._order = get_object_or_404(ExtractionOrder, pk=self.kwargs["pk"])
        return self._order

    def get_data(self) -> list[Sample]:
        order = self.get_order()
        samples = Sample.objects.filter(order=order, genlab_id__isnull=False)
        sample_status = SampleStatusAssignment.SampleStatus.choices

        # Fetch all SampleStatusAssignment entries related to the current order
        sample_assignments = SampleStatusAssignment.objects.filter(order_id=order.id)

        # Build a lookup: {sample_id: set of status names}
        # This allows us to check status presence without querying per sample
        sample_status_map = defaultdict(set)
        for assignment in sample_assignments:
            name = str(assignment.status)

            sample_status_map[assignment.sample_id].add(name)

        # Annotate each sample instance with boolean flags per status
        # Equivalent to: sample.status_name = True/False
        # based on whether the sample has that status
        for sample in samples:
            sample.selected_isolation_method = (
                sample.isolation_method.first()
                if sample.isolation_method.exists()
                else None
            )
            status_names = sample_status_map.get(sample.id, set())
            for status, _i in sample_status:
                setattr(sample, status, status in status_names)

        return samples

    def get_isolation_methods(self) -> list[str]:
        order = self.get_order()
        samples = Sample.objects.filter(order=order)
        species_ids = samples.values_list("species_id", flat=True).distinct()

        return IsolationMethod.objects.filter(species_id__in=species_ids).values_list(
            "name", flat=True
        )

    def get_base_fields(self) -> list[str]:
        return [v for v, _ in SampleStatusAssignment.SampleStatus.choices]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["order"] = self.get_order()
        context["statuses"] = self.get_base_fields()
        context["isolation_methods"] = self.get_isolation_methods()
        context["table"] = self.table_class(data=self.get_data())

        return context

    def get_success_url(self) -> str:
        return reverse(
            "staff:order-extraction-samples-lab", kwargs={"pk": self.get_order().pk}
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        status_name = request.POST.get("status")
        selected_ids = request.POST.getlist("checked")
        isolation_method = request.POST.get("isolation_method")

        if not selected_ids:
            messages.error(request, "No samples selected.")
            return HttpResponseRedirect(self.get_success_url())

        order = self.get_order()

        # Get the selected samples
        samples = Sample.objects.filter(id__in=selected_ids)

        if status_name:
            self.assign_status_to_samples(samples, status_name, order, request)
        if isolation_method:
            self.update_isolation_methods(samples, isolation_method, request)
        return HttpResponseRedirect(self.get_success_url())

    def assign_status_to_samples(
        self,
        samples: models.QuerySet,
        status_name: str,
        order: ExtractionOrder,
        request: HttpRequest,
    ) -> None:
        statuses = SampleStatusAssignment.SampleStatus.choices

        # Check if the provided status exists
        if status_name not in [k for k, _ in statuses]:
            messages.error(request, f"Status '{status_name}' is not valid.")
            return HttpResponseRedirect(self.get_success_url())

        # Get the index of the target status
        status_weight = next(
            i for i, (name, _) in enumerate(statuses) if name == status_name
        )

        # Slice the list up to that index (inclusive) and extract only the names
        statuses_to_apply = [name for name, _ in statuses[: status_weight + 1]]

        # Apply status assignments
        assignments = []
        for sample in samples:
            for status in statuses_to_apply:
                assignment = SampleStatusAssignment(
                    sample=sample,
                    status=status,
                    order=order,
                )
                assignments.append(assignment)

        SampleStatusAssignment.objects.bulk_create(
            assignments,
            ignore_conflicts=True,
        )

        messages.success(
            request, f"{samples.count()} samples updated with status '{status_name}'."
        )

    def update_isolation_methods(
        self, samples: models.QuerySet, isolation_method: str, request: HttpRequest
    ) -> None:
        selected_isolation_method = IsolationMethod.objects.filter(
            name=isolation_method
        ).first()

        try:
            im = IsolationMethod.objects.get(name=selected_isolation_method.name)
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

    def get_queryset(self) -> models.QuerySet[Order] | models.QuerySet[Genrequest]:
        model_type = self._get_model_type()
        if model_type == "genrequest":
            return Genrequest.objects.all()
        return Order.objects.filter(status=Order.OrderStatus.DELIVERED)

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

    def get_queryset(self) -> models.QuerySet[Order]:
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

    def get_queryset(self) -> models.QuerySet[Order]:
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


class GenerateGenlabIDsView(
    SingleObjectMixin, StaffMixin, SingleTableMixin, FilterView
):
    model = ExtractionOrder

    def get_object(self) -> ExtractionOrder:
        return ExtractionOrder.objects.get(pk=self.kwargs["pk"])

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        selected_ids = request.POST.getlist("checked")

        if not selected_ids:
            messages.error(request, "No samples were selected.")
            return HttpResponseRedirect(self.get_return_url())

        sort_param = request.POST.get("sort", "")
        sorting_order = [s.strip() for s in sort_param.split(",") if s.strip()]

        selected_samples = Sample.objects.filter(pk__in=selected_ids)

        if sorting_order:
            selected_samples = selected_samples.order_by(*sorting_order)

        try:
            self.object.order_selected_checked(
                sorting_order=sorting_order, selected_samples=selected_samples
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                _(f"Genlab IDs generated for {selected_samples.count()} samples."),
            )
        except Exception as e:
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

    def get_queryset(self) -> models.QuerySet[Sample]:
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

    def get_queryset(self) -> models.QuerySet[Project]:
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
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        pk = kwargs.get("pk")
        order = Order.objects.get(pk=pk)
        order.toggle_prioritized()

        return HttpResponseRedirect(
            reverse(
                "staff:dashboard",
            )
        )
