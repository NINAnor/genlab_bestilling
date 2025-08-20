from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.db.models import Count, Prefetch, QuerySet
from django.forms import Form
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from genlab_bestilling.models import (
    AnalysisOrder,
    AnalysisPlate,
    Area,
    EquipmentOrder,
    ExtractionOrder,
    ExtractionPlate,
    Genrequest,
    IsolationMethod,
    Marker,
    Order,
    Plate,
    Sample,
    SampleIsolationMethod,
    SampleMarkerAnalysis,
)
from nina.models import Project
from shared.sentry import report_errors
from shared.views import ActionView
from staff.mixins import SafeRedirectMixin

from .filters import (
    AnalysisOrderFilter,
    AnalysisPlateFilter,
    EquipmentOrderFilter,
    ExtractionOrderFilter,
    ExtractionPlateFilter,
    OrderSampleFilter,
    ProjectFilter,
    SampleFilter,
    SampleLabFilter,
    SampleMarkerOrderFilter,
)
from .forms import (
    AnalysisPlateForm,
    ExtractionPlateForm,
    OrderStaffForm,
)
from .tables import (
    AnalysisOrderTable,
    AnalysisPlateTable,
    EquipmentOrderTable,
    ExtractionOrderTable,
    ExtractionPlateTable,
    OrderAnalysisSampleTable,
    OrderExtractionSampleTable,
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

    class Params:
        area = "area"

    def get_area_from_query(self) -> Area | None:
        area_id = self.request.GET.get(self.Params.area)
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
    table_pagination = {"per_page": 20}

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
            .prefetch_related("samples__species")
            .annotate(total_samples=Count("samples"))
        )


class ExtractionOrderListView(StaffMixin, SingleTableMixin, FilterView):
    model = ExtractionOrder
    table_class = ExtractionOrderTable
    filterset_class = ExtractionOrderFilter
    table_pagination = {"per_page": 20}

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


# class ExtractionPlateListView(StaffMixin, SingleTableMixin, FilterView):
#     model = ExtractionPlate
#     table_class = PlateTable
#     filterset_class = ExtractionPlateFilter

#     def get_queryset(self) -> QuerySet[ExtractionPlate]:
#         return (
#             super()
#             .get_queryset()
#             .select_related()
#             .prefetch_related("sample_positions")
#             .annotate(samples_count=models.Count("sample_positions"))
#         )


class EqupimentOrderListView(StaffMixin, SingleTableMixin, FilterView):
    model = EquipmentOrder
    table_class = EquipmentOrderTable
    filterset_class = EquipmentOrderFilter
    table_pagination = {"per_page": 20}

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


class MarkAsSeenView(StaffMixin, DetailView, SafeRedirectMixin):
    model = Order

    def get_object(self) -> Order:
        return Order.objects.get(pk=self.kwargs["pk"])

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        try:
            order = self.get_object()
            order.toggle_seen()
            order.update_status()

            messages.success(request, _("Order is marked as seen"))
        except Exception as e:
            report_errors(e)
            messages.error(request, f"Error: {str(e)}")

        return redirect(self.get_next_url())

    def get_fallback_url(self) -> str:
        return self.get_object().get_absolute_staff_url()


class ExtractionOrderDetailView(StaffMixin, DetailView):
    model = ExtractionOrder

    # Prefetch species to avoid N+1 queries when accessing species in the template
    def get_queryset(self) -> QuerySet[ExtractionOrder]:
        return super().get_queryset().prefetch_related("species")

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


class OrderExtractionSamplesListView(
    StaffMixin, SingleTableMixin, SafeRedirectMixin, FilterView
):
    table_pagination = False

    model = Sample
    table_class = OrderExtractionSampleTable
    filterset_class = OrderSampleFilter

    class Params:
        sample_id = "sample_id"

    def get_queryset(self) -> QuerySet[Sample]:
        return (
            super()
            .get_queryset()
            .select_related("type", "location", "species")
            .filter(order=self.kwargs["pk"])
            .annotate_numeric_name()
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

    def get_fallback_url(self) -> str:
        return reverse(
            "staff:order-extraction-samples", kwargs={"pk": self.kwargs["pk"]}
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        sample_id = request.POST.get(self.Params.sample_id)
        if sample_id:
            sample = get_object_or_404(Sample, pk=sample_id)
            sample.is_prioritised = not sample.is_prioritised
            sample.save()

        if self.has_next_url():
            return HttpResponseRedirect(self.get_next_url())

        return self.get(
            request, *args, **kwargs
        )  # Re-render the view with updated data


class OrderAnalysisSamplesListView(
    StaffMixin, SingleTableMixin, SafeRedirectMixin, FilterView
):
    PCR = "pcr"
    ANALYSED = "analysed"
    NOT_ANALYSED = "invalid"
    OUTPUT = "output"
    VALID_STATUSES = [PCR, ANALYSED, OUTPUT, NOT_ANALYSED]

    table_pagination = False
    model = SampleMarkerAnalysis
    table_class = OrderAnalysisSampleTable
    filterset_class = SampleMarkerOrderFilter

    class Params:
        status = "status"

    def get_order(self) -> AnalysisOrder:
        return get_object_or_404(AnalysisOrder, pk=self.kwargs["pk"])

    def get_queryset(self) -> QuerySet[SampleMarkerAnalysis]:
        return (
            SampleMarkerAnalysis.objects.filter(order=self.get_order())
            .select_related(
                "sample",
                "sample__type",
                "sample__location",
                "sample__species",
                "marker",
                "sample__order",
                "order",
            )
            .prefetch_related("sample__isolation_method")
        )

    def get_base_fields(self) -> list[str]:
        return self.VALID_STATUSES

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "order": self.get_order(),
                "statuses": self.get_base_fields(),
            }
        )
        return context

    def get_fallback_url(self) -> str:
        return reverse(
            "staff:order-analysis-samples", kwargs={"pk": self.get_order().pk}
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        status_name = request.POST.get(self.Params.status)
        selected_ids = request.POST.getlist(f"checked-analysis-{self.get_order().pk}")

        if not selected_ids:
            messages.error(request, "No samples selected.")
            return HttpResponseRedirect(self.get_next_url())

        order = self.get_order()

        # Get the selected samples
        analyses = SampleMarkerAnalysis.objects.filter(id__in=selected_ids)

        if status_name:
            self.assign_status_to_samples(analyses, status_name, request)
            if status_name == self.OUTPUT:
                self.check_all_output(SampleMarkerAnalysis.objects.filter(order=order))
            else:
                self.get_order().to_processing()
        return HttpResponseRedirect(self.get_next_url())

    def statuses_with_lower_or_equal_priority(self, status_name: str) -> list[str]:
        if status_name != self.NOT_ANALYSED:
            index = self.VALID_STATUSES.index(status_name)
            return self.VALID_STATUSES[: index + 1]
        return [status_name]

    def assign_status_to_samples(
        self,
        analyses: QuerySet[SampleMarkerAnalysis],
        status_name: str,
        request: HttpRequest,
    ) -> None:
        if status_name not in self.VALID_STATUSES:
            messages.error(request, f"Status '{status_name}' is not valid.")
            return

        statuses_to_turn_on = self.statuses_with_lower_or_equal_priority(status_name)

        if status_name == self.PCR:
            field_name = "has_pcr"
        elif status_name == self.ANALYSED:
            field_name = "is_analysed"
        elif status_name == self.OUTPUT:
            field_name = "is_outputted"
        elif status_name == self.NOT_ANALYSED:
            field_name = "is_invalid"
        else:
            msg = "Unexpected status value"
            raise ValueError(msg)

        samples_to_turn_off_ids = list(
            analyses.filter(**{field_name: True}).values_list("id", flat=True)
        )
        samples_to_turn_on_ids = list(
            analyses.filter(**{field_name: False}).values_list("id", flat=True)
        )

        SampleMarkerAnalysis.objects.filter(id__in=samples_to_turn_off_ids).update(
            **{field_name: False}
        )

        update_dict = {}
        if self.PCR in statuses_to_turn_on:
            update_dict["has_pcr"] = True
        if self.ANALYSED in statuses_to_turn_on:
            update_dict["is_analysed"] = True
        if self.OUTPUT in statuses_to_turn_on:
            update_dict["is_outputted"] = True
        if self.NOT_ANALYSED in statuses_to_turn_on:
            update_dict["is_invalid"] = True

        SampleMarkerAnalysis.objects.filter(id__in=samples_to_turn_on_ids).update(
            **update_dict
        )
        messages.success(
            request,
            f"Set statuses {', '.join(statuses_to_turn_on)} for {analyses.count()} analyses.",  # noqa: E501
        )

    # Checks if all samples in the order have output
    # If they are, it updates the order status to completed
    def check_all_output(self, analyses: QuerySet[SampleMarkerAnalysis]) -> None:
        order = self.get_order()

        if not analyses.exclude(is_invalid=True).filter(is_outputted=False).exists():
            order.to_completed()
            messages.success(
                self.request,
                "All samples have an output. The order status is updated to completed.",
            )
        elif order.status in (Order.OrderStatus.COMPLETED, Order.OrderStatus.DELIVERED):
            order.to_processing()
            messages.success(
                self.request,
                "Not all samples have output. The order status is updated to processing.",  # noqa: E501
            )


class SamplesListView(StaffMixin, SingleTableMixin, FilterView):
    table_pagination = {"per_page": 50}

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
                "order__responsible_staff",
                Prefetch(
                    "markers", queryset=Marker.objects.order_by("name").distinct()
                ),
            )
            .exclude(order__status=Order.OrderStatus.DRAFT)
            .annotate_numeric_name()
            .order_by("species__name", "year", "location__name", "name")
        )


class SampleDetailView(StaffMixin, DetailView):
    model = Sample

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        referer = self.request.GET.get("from")
        if referer:
            context["url"] = referer
        else:
            # Fallback to a default page
            context["url"] = reverse("staff:samples-list")
        return context


class SampleLabView(StaffMixin, SingleTableMixin, SafeRedirectMixin, FilterView):
    # TODO: move away the logic, validation logic should be in a form,
    # any other logic should be in a manager/model method (FAT models, THIN views)
    # TODO: write test to assert the behavior
    MARKED = "marked"
    PLUCKED = "plucked"
    ISOLATED = "isolated"
    INVALID = "invalid"
    VALID_STATUSES = [MARKED, PLUCKED, ISOLATED, INVALID]

    table_pagination = False
    template_name = "staff/sample_lab.html"
    table_class = SampleStatusTable
    filterset_class = SampleLabFilter

    class Params:
        status = "status"
        isolation_method = "isolation_method"

    def get_order(self) -> ExtractionOrder:
        if not hasattr(self, "_order"):
            self._order = get_object_or_404(ExtractionOrder, pk=self.kwargs["pk"])
        return self._order

    def get_queryset(self) -> QuerySet[Sample]:
        return (
            Sample.objects.filter(order=self.get_order(), genlab_id__isnull=False)
            .select_related(
                "position",
                "position__plate",
                "type",
                "order",
            )
            .prefetch_related(
                Prefetch(
                    "isolation_method",
                    queryset=IsolationMethod.objects.order_by("name").distinct(),
                ),
            )
        )

    def get_isolation_methods(self) -> QuerySet[IsolationMethod, str]:
        types = self.get_queryset().values_list("type", flat=True).distinct()
        return (
            IsolationMethod.objects.filter(sample_types__in=types)
            .values_list("name", flat=True)
            .distinct()
        )

    def get_base_fields(self) -> list[str]:
        return self.VALID_STATUSES

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        order = self.get_order()
        total_samples = order.samples.count()
        filled_count = order.isolated_count
        context["progress_percent"] = (
            (float(filled_count) / float(total_samples)) * 100
            if total_samples > 0
            else 0
        )

        context.update(
            {
                "order": order,
                "statuses": self.get_base_fields(),
                "isolation_methods": self.get_isolation_methods(),
            }
        )
        return context

    def get_fallback_url(self) -> str:
        return reverse(
            "staff:order-extraction-samples-lab", kwargs={"pk": self.get_order().pk}
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # TODO: use a form instead of manual extraction
        status_name = request.POST.get(self.Params.status)
        selected_ids = request.POST.getlist(f"checked-{self.get_order().pk}")
        isolation_method = request.POST.get(self.Params.isolation_method)

        replicate = request.POST.get("replicate")
        plate_id = request.POST.get("plate_id")

        if not selected_ids:
            messages.error(request, "No samples selected.")
            return HttpResponseRedirect(self.get_next_url())

        if replicate and len(selected_ids) > 1:
            messages.error(request, "Select a single sample")
            return HttpResponseRedirect(self.get_next_url())

        order = self.get_order()

        # Get the selected samples
        samples = Sample.objects.filter(id__in=selected_ids).order_by("genlab_id")

        if status_name:
            self.assign_status_to_samples(samples, status_name, request)
            if status_name in [self.ISOLATED, self.INVALID]:
                # Cannot use "samples" here
                # because we need to check all samples in the order
                self.check_all_isolated(Sample.objects.filter(order=order))

        if isolation_method:
            self.update_isolation_methods(samples, isolation_method, request)

        if replicate:
            first_sample = samples.first()
            if first_sample:
                first_sample.replicate(int(replicate))

        if plate_id:
            plate = get_object_or_404(ExtractionPlate, pk=plate_id)
            try:
                sample_list = list(
                    samples.filter(
                        is_marked=True,
                        is_invalid=False,
                        position__isnull=True,
                    )
                )
                plate.populate(sample_list)
                messages.success(
                    request,
                    f"Populated {len(sample_list)} samples in the plate {plate}.",
                )
            except Plate.NotEnoughPositions:
                messages.error(request, "Not enough empty positions in the plate.")
                return HttpResponseRedirect(self.get_next_url())

        return HttpResponseRedirect(self.get_next_url())

    def statuses_with_lower_or_equal_priority(self, status_name: str) -> list[str]:
        if status_name != "invalid":
            index = self.VALID_STATUSES.index(status_name)
            return self.VALID_STATUSES[: index + 1]
        return [status_name]

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
        if not samples.exclude(is_invalid=True).filter(is_isolated=False).exists():
            self.get_order().to_completed()
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

        if selected_isolation_method is None:
            messages.error(
                request,
                f"Isolation method '{isolation_method}' not found.",
            )
            return

        for sample in samples:
            # Remove any existing methods for this sample
            SampleIsolationMethod.objects.filter(sample=sample).delete()

            # Add the new one
            SampleIsolationMethod.objects.create(
                sample=sample, isolation_method=selected_isolation_method
            )
        messages.success(
            request,
            f"{samples.count()} samples updated with isolation method '{isolation_method}'.",  # noqa: E501
        )


class UpdateInternalNote(StaffMixin, ActionView):
    class Params:
        sample_id = "sample_id"
        field_name = "field_name"
        field_value = "field_value"

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        sample_id = request.POST.get(self.Params.sample_id)
        field_name = request.POST.get(self.Params.field_name)
        field_value = request.POST.get(self.Params.field_value)

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


class GenerateGenlabIDsView(SingleObjectMixin, StaffMixin, SafeRedirectMixin):
    model = ExtractionOrder

    def get_object(self) -> ExtractionOrder:
        return ExtractionOrder.objects.get(pk=self.kwargs["pk"])

    def get_fallback_url(self) -> str:
        return reverse_lazy(
            "staff:order-extraction-samples", kwargs={"pk": self.object.pk}
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()

        # getlist automatically reads the values in the order presented in the table
        selected_ids = request.POST.getlist("checked")

        if not selected_ids:
            messages.error(request, "No samples were selected.")
            return HttpResponseRedirect(self.get_next_url())

        if not self.object.confirmed_at:
            messages.error(
                request, "Order needs to be confirmed before generating genlab IDs"
            )
            return HttpResponseRedirect(self.get_next_url())

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

        return HttpResponseRedirect(self.get_next_url())


class ProjectListView(StaffMixin, SingleTableMixin, FilterView):
    model = Project
    table_class = ProjectTable
    filterset_class = ProjectFilter


class ProjectDetailView(StaffMixin, DetailView):
    model = Project


class ProjectValidateActionView(SingleObjectMixin, SafeRedirectMixin, ActionView):
    model = Project

    def get_queryset(self) -> QuerySet[Project]:
        return super().get_queryset().filter(verified_at=None)

    def form_valid(self, form: Form) -> HttpResponse:
        self.object = self.get_object()
        self.object.verified_at = now()
        self.object.save()
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _("The project is verified"),
        )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return self.get_next_url()

    def get_fallback_url(self) -> str:
        return self.request.GET.get("next", reverse("staff:projects-list"))

    def form_invalid(self, form: Form) -> HttpResponse:
        return HttpResponseRedirect(self.get_next_url())


class ProjectArchiveActionView(SingleObjectMixin, ActionView):
    model = Project

    def get_queryset(self) -> QuerySet[Project]:
        return Project.objects.all()

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Form) -> HttpResponse:
        # Toggle the active state of the project
        self.object.active = not self.object.active
        self.object.save()
        status = _("activated") if self.object.active else _("archived")
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _(f"The project is {status}"),
        )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("staff:projects-list")

    def form_invalid(self, form: Form) -> HttpResponse:
        return HttpResponseRedirect(self.get_success_url())


class OrderPrioritizedAdminView(StaffMixin, SafeRedirectMixin, ActionView):
    def get_fallback_url(self) -> str:
        return reverse("staff:dashboard")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        pk = kwargs.get("pk")
        order = Order.objects.get(pk=pk)
        order.toggle_prioritized()

        return redirect(self.get_next_url())


# ExtractionPlate Views


class ExtractionPlateListView(StaffMixin, SingleTableMixin, FilterView):
    model = ExtractionPlate
    table_class = ExtractionPlateTable
    filterset_class = ExtractionPlateFilter
    context_object_name = "extraction_plates"
    paginate_by = 25

    def get_queryset(self) -> QuerySet[ExtractionPlate]:
        return (
            ExtractionPlate.objects.select_related()
            .prefetch_related("positions__sample_raw")
            .distinct()
            .order_by("-created_at")
        )


class ExtractionPlateDetailView(StaffMixin, DetailView):
    model = ExtractionPlate
    context_object_name = "plate"

    def get_queryset(self) -> QuerySet[ExtractionPlate]:
        return ExtractionPlate.objects.prefetch_related(
            "positions__sample_raw__species",
            "positions__sample_raw__type",
            "positions__sample_raw__location",
        )


class ExtractionPlateCreateView(StaffMixin, CreateView):
    model = ExtractionPlate
    form_class = ExtractionPlateForm

    def get_success_url(self) -> str:
        messages.success(
            self.request,
            f"Extraction plate #{self.object.qiagen_id} created successfully.",  # type: ignore[union-attr]
        )
        return reverse("staff:extraction-plates-detail", kwargs={"pk": self.object.pk})  # type: ignore[union-attr]


class ExtractionPlateUpdateView(StaffMixin, UpdateView):
    model = ExtractionPlate
    form_class = ExtractionPlateForm
    context_object_name = "plate"

    def get_success_url(self) -> str:
        messages.success(
            self.request,
            f"Extraction plate #{self.object.qiagen_id} updated successfully.",
        )
        return reverse("staff:extraction-plates-detail", kwargs={"pk": self.object.pk})


# AnalysisPlate Views


class AnalysisPlateListView(StaffMixin, SingleTableMixin, FilterView):
    model = AnalysisPlate
    table_class = AnalysisPlateTable
    filterset_class = AnalysisPlateFilter
    context_object_name = "analysis_plates"
    paginate_by = 25

    def get_queryset(self) -> QuerySet[AnalysisPlate]:
        return (
            AnalysisPlate.objects.select_related()
            .prefetch_related("positions__sample_marker")
            .order_by("-created_at")
        )


class AnalysisPlateDetailView(StaffMixin, DetailView):
    model = AnalysisPlate
    context_object_name = "plate"

    def get_queryset(self) -> QuerySet[AnalysisPlate]:
        return AnalysisPlate.objects.prefetch_related(
            "positions__sample_marker__sample__species",
            "positions__sample_marker__sample__type",
            "positions__sample_marker__marker",
            "positions__sample_marker__order",
        )


class AnalysisPlateCreateView(StaffMixin, CreateView):
    model = AnalysisPlate
    form_class = AnalysisPlateForm

    def get_success_url(self) -> str:
        messages.success(
            self.request,
            "Analysis plate created successfully.",
        )
        return reverse("staff:analysis-plates-detail", kwargs={"pk": self.object.pk})  # type: ignore[union-attr]


class AnalysisPlateUpdateView(StaffMixin, UpdateView):
    model = AnalysisPlate
    form_class = AnalysisPlateForm
    context_object_name = "plate"

    def get_success_url(self) -> str:
        messages.success(
            self.request,
            "Analysis plate updated successfully.",
        )
        return reverse("staff:analysis-plates-detail", kwargs={"pk": self.object.pk})


class PlatePositionsView(StaffMixin, DetailView):
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["grid"] = self.object.get_grid()
        context["rows"] = Plate.ROWS
        context["columns"] = range(1, Plate.COLUMNS + 1)
        return context


class ExtractionPlatePositionsView(PlatePositionsView):
    model = ExtractionPlate
    template_name = "staff/extractionplate_positions.html"

    def get_queryset(self) -> QuerySet[ExtractionPlate]:
        return (
            super()
            .get_queryset()
            .select_related()
            .prefetch_related(
                "positions__sample_raw",
                "positions__sample_raw__order",
            )
        )


class AnalysisPlatePositionsView(PlatePositionsView):
    model = AnalysisPlate
    template_name = "staff/extractionplate_positions.html"

    def get_queryset(self) -> QuerySet[AnalysisPlate]:
        return (
            super()
            .get_queryset()
            .select_related()
            .prefetch_related(
                "positions__sample_marker",
                "positions__sample_marker__marker",
                "positions__sample_marker__sample",
                "positions__sample_marker__order",
            )
        )
