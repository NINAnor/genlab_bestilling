from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import StringAgg
from django.db.models.query import QuerySet
from django.forms import Form
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import (
    DeleteView,
    DetailView,
)
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin, SingleTableView
from formset.views import (
    BulkEditCollectionView,
)
from rest_framework.exceptions import ValidationError
from view_breadcrumbs import BaseBreadcrumbMixin

from nina.models import Project
from shared.views import ActionView, FormsetCreateView, FormsetUpdateView

from .api.serializers import AnalysisSerializer, ExtractionSerializer
from .filters import (
    GenrequestFilter,
    OrderAnalysisFilter,
    OrderEquipmentFilter,
    OrderExtractionFilter,
    OrderFilter,
)
from .forms import (
    AnalysisOrderForm,
    AnalysisOrderUpdateForm,
    EquipmentOrderForm,
    EquipmentQuantityCollection,
    ExtractionOrderForm,
    GenrequestEditForm,
    GenrequestForm,
)
from .models import (
    AnalysisOrder,
    EquimentOrderQuantity,
    EquipmentOrder,
    ExtractionOrder,
    Genrequest,
    Order,
    Sample,
    SampleMarkerAnalysis,
)
from .tables import (
    AnalysisOrderTable,
    AnalysisSampleTable,
    EquipmentOrderTable,
    ExtractionOrderTable,
    GenrequestTable,
    OrderTable,
    SampleTable,
)


class GenrequestListView(
    BaseBreadcrumbMixin, LoginRequiredMixin, SingleTableMixin, FilterView
):
    model = Genrequest
    table_class = GenrequestTable
    add_home = False
    filterset_class = GenrequestFilter

    @cached_property
    def crumbs(self) -> list[tuple]:
        return [(self.model._meta.verbose_name_plural, reverse("genrequest-list"))]

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related("project", "area")
            .prefetch_related("tags", "sample_types", "species")
            .filter_allowed(self.request.user)
        )


class GenrequestDetailView(BaseBreadcrumbMixin, LoginRequiredMixin, DetailView):
    model = Genrequest
    add_home = False

    @cached_property
    def crumbs(self) -> list[tuple]:
        return [
            (self.model._meta.verbose_name_plural, reverse("genrequest-list")),
            (str(self.object), ""),
        ]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter_allowed(self.request.user)  # type: ignore[attr-defined]


class GenrequestUpdateView(BaseBreadcrumbMixin, FormsetUpdateView):
    model = Genrequest
    form_class = GenrequestEditForm
    add_home = False

    @cached_property
    def crumbs(self) -> list[tuple]:
        return [
            (self.model._meta.verbose_name_plural, reverse("genrequest-list")),
            (
                str(self.object),
                reverse("genrequest-detail", kwargs={"pk": self.object.pk}),
            ),
            ("Update", ""),
        ]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter_allowed(self.request.user)  # type: ignore[attr-defined]

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-detail",
            kwargs={"pk": self.object.id},
        )


class GenrequestDeleteView(BaseBreadcrumbMixin, DeleteView):
    model = Genrequest

    add_home = False

    @cached_property
    def crumbs(self) -> list[tuple]:
        return [
            (self.model._meta.verbose_name_plural, reverse("genrequest-list")),
            (
                str(self.object),
                reverse("genrequest-detail", kwargs={"pk": self.object.pk}),
            ),
            ("Delete", ""),
        ]

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-list",
        )


class GenrequestCreateView(BaseBreadcrumbMixin, FormsetCreateView):
    model = Genrequest
    form_class = GenrequestForm

    add_home = False

    class Params:
        project = "project"

    @cached_property
    def crumbs(self) -> list[tuple]:
        return [
            (self.model._meta.verbose_name_plural, reverse("genrequest-list")),
            ("Create", ""),
        ]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter_allowed(self.request.user)  # type: ignore[attr-defined]

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        if project := self.request.GET.get(self.Params.project):
            kwargs["project"] = Project.objects.filter(pk=project).first()
        return kwargs

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-detail",
            kwargs={"pk": self.object.id},  # type: ignore[union-attr] # FIXME: Can object be None?
        )


class GenrequestNestedMixin(BaseBreadcrumbMixin, LoginRequiredMixin):
    """
    Provide a Mixin to simplify views that operates under /genrequests/<id>/

    By default loads the genrequest from the database,
    filter the current queryset using the genrequest
    and adds it to the render context.
    """

    genrequest_accessor = "genrequest"

    add_home = False
    gen_crumbs: list[tuple] = []

    @cached_property
    def crumbs(self) -> list[tuple]:
        return [
            (Genrequest._meta.verbose_name_plural, reverse("genrequest-list")),
            (
                str(self.genrequest),
                self.genrequest.get_absolute_url(),
            ),
        ] + self.gen_crumbs

    def get_genrequest(self) -> Genrequest:
        return Genrequest.objects.filter_allowed(self.request.user).get(
            id=self.kwargs["genrequest_id"]
        )

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.genrequest = self.get_genrequest()
        return super().post(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.genrequest = self.get_genrequest()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        qs: QuerySet = super().get_queryset().filter_allowed(self.request.user)
        kwargs = {f"{self.genrequest_accessor}_id": self.genrequest.id}
        return qs.filter(**kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx: dict = super().get_context_data(**kwargs)
        ctx["genrequest"] = self.genrequest
        return ctx

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs: dict = super().get_form_kwargs()
        kwargs["genrequest"] = self.genrequest
        return kwargs


class GenrequestOrderListView(GenrequestNestedMixin, SingleTableMixin, FilterView):
    model = Order
    table_class = OrderTable
    filterset_class = OrderFilter
    gen_crumbs = [("Orders", "")]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().select_related("genrequest", "polymorphic_ctype")


class OrderListView(SingleTableMixin, FilterView):
    model = Order
    table_class = OrderTable
    filterset_class = OrderFilter
    crumbs = [("Orders", "")]

    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .select_related("genrequest", "polymorphic_ctype", "genrequest__project")
        )


class GenrequestEquipmentOrderListView(
    GenrequestNestedMixin, SingleTableMixin, FilterView
):
    model = EquipmentOrder
    table_class = EquipmentOrderTable
    filterset_class = OrderEquipmentFilter

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                "",
            ),
        ]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().select_related("genrequest")


class EquipmentOrderListView(SingleTableMixin, FilterView):
    model = EquipmentOrder
    table_class = EquipmentOrderTable
    filterset_class = OrderEquipmentFilter

    @cached_property
    def crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "order-list",
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                "",
            ),
        ]

    def get_queryset(self) -> QuerySet:
        return (
            super().get_queryset().select_related("genrequest", "genrequest__project")
        )


class GenrequestExtractionOrderListView(
    GenrequestNestedMixin, SingleTableMixin, FilterView
):
    model = ExtractionOrder
    table_class = ExtractionOrderTable
    filterset_class = OrderExtractionFilter

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                "",
            ),
        ]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().select_related("genrequest")


class ExtractionOrderListView(SingleTableMixin, FilterView):
    model = ExtractionOrder
    table_class = ExtractionOrderTable
    filterset_class = OrderExtractionFilter

    @cached_property
    def crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "order-list",
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                "",
            ),
        ]

    def get_queryset(self) -> QuerySet:
        return (
            super().get_queryset().select_related("genrequest", "genrequest__project")
        )


class GenrequestAnalysisOrderListView(
    GenrequestNestedMixin, SingleTableMixin, FilterView
):
    model = AnalysisOrder
    table_class = AnalysisOrderTable
    filterset_class = OrderAnalysisFilter

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                "",
            ),
        ]

    def get_queryset(self) -> QuerySet:
        return (
            super().get_queryset().select_related("genrequest", "genrequest__project")
        )


class AnalysisOrderListView(SingleTableMixin, FilterView):
    model = AnalysisOrder
    table_class = AnalysisOrderTable
    filterset_class = OrderAnalysisFilter

    @cached_property
    def crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "order-list",
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                "",
            ),
        ]

    def get_queryset(self) -> QuerySet:
        return (
            super().get_queryset().select_related("genrequest", "genrequest__project")
        )


class EquipmentOrderDetailView(GenrequestNestedMixin, DetailView):
    model = EquipmentOrder

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                reverse(
                    "genrequest-equipment-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (str(self.object), ""),
        ]


class AnalysisOrderDetailView(GenrequestNestedMixin, DetailView):
    model = AnalysisOrder

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                reverse(
                    "genrequest-analysis-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (str(self.object), ""),
        ]

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["results_contacts"] = self.object.results_contacts.all()
        return context

    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .select_related("genrequest", "from_order", "polymorphic_ctype")
            .prefetch_related("sample_markers", "markers")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        order = self.object
        all_samples_have_no_genlab_id = not order.samples.exclude(
            genlab_id__isnull=True
        ).exists()
        context["all_samples_have_no_genlab_id"] = all_samples_have_no_genlab_id
        return context


class ExtractionOrderDetailView(GenrequestNestedMixin, DetailView):
    model = ExtractionOrder

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                reverse(
                    "genrequest-extraction-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (str(self.object), ""),
        ]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        order = self.object
        all_samples_have_no_genlab_id = not order.samples.exclude(
            genlab_id__isnull=True
        ).exists()
        context["all_samples_have_no_genlab_id"] = all_samples_have_no_genlab_id
        return context


class GenrequestOrderDeleteView(GenrequestNestedMixin, DeleteView):
    model = Order
    template_name = "genlab_bestilling/order_confirm_delete.html"

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                reverse(
                    f"genrequest-{self.object.get_type()}-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (str(self.object), self.object.get_absolute_url()),
            ("Delete", ""),
        ]

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        return qs.filter(status=Order.OrderStatus.DRAFT)

    def get_object(self, queryset: QuerySet | None = None) -> Order:
        return (super().get_object(queryset)).get_real_instance()

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        del kwargs["genrequest"]
        return kwargs

    def form_valid(self, form: Form) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, f"Order #{self.kwargs['pk']} deleted!")
        return response

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-order-list", kwargs={"genrequest_id": self.genrequest.pk}
        )


class ConfirmOrderActionView(GenrequestNestedMixin, SingleObjectMixin, ActionView):
    model = Order

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter_in_draft()  # type: ignore[attr-defined]

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.genrequest = self.get_genrequest()
        self.object = (self.get_object()).get_real_instance()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs.pop("genrequest")
        return kwargs

    def form_valid(self, form: Any) -> HttpResponse:
        try:
            # TODO: check state transition
            self.object.confirm_order()
            messages.add_message(
                self.request, messages.SUCCESS, _("Your order is delivered")
            )
        except (Order.CannotConfirm, ValidationError) as e:
            messages.add_message(
                self.request,
                messages.ERROR,
                f"Error: {','.join(map(lambda error: str(error), e.detail))}",
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()

    def form_invalid(self, form: Form) -> HttpResponse:
        return HttpResponseRedirect(self.get_success_url())


class CloneOrderActionView(GenrequestNestedMixin, SingleObjectMixin, ActionView):
    model = Order

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.genrequest = self.get_genrequest()
        self.object = (self.get_object()).get_real_instance()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Any) -> HttpResponse:
        try:
            # NOTE: this will mutate self.object!!
            self.object.clone()
            messages.add_message(
                self.request, messages.SUCCESS, _("Your order is cloned")
            )
        except Order.CannotConfirm as e:
            messages.add_message(
                self.request,
                messages.ERROR,
                f"Error: {','.join(map(lambda error: str(error), e.detail))}",
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        order_type = self.object.get_type()
        if order_type == "extraction":
            return reverse(
                "genrequest-extraction-samples-edit",
                kwargs={
                    "pk": self.object.id,
                    "genrequest_id": self.object.genrequest_id,
                },
            )
        if order_type == "equipment":
            return reverse(
                "genrequest-equipment-quantity-update",
                kwargs={
                    "pk": self.object.id,
                    "genrequest_id": self.object.genrequest_id,
                },
            )
        return self.object.get_absolute_url()

    def form_invalid(self, form: Form) -> HttpResponse:
        return HttpResponseRedirect(self.get_success_url())


class EquipmentOrderEditView(
    GenrequestNestedMixin,
    FormsetUpdateView,
):
    model = EquipmentOrder
    form_class = EquipmentOrderForm

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (
                self.model._meta.verbose_name_plural,
                reverse(
                    f"genrequest-{self.object.get_type()}-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (str(self.object), self.object.get_absolute_url()),
            ("Update", ""),
        ]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter_in_draft()  # type: ignore[attr-defined]

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-equipment-detail",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},
        )


class EquipmentOrderCreateView(
    GenrequestNestedMixin,
    FormsetCreateView,
):
    model = EquipmentOrder
    form_class = EquipmentOrderForm

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            ("Create", ""),
        ]

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-equipment-quantity-update",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},  # type: ignore[union-attr] # FIXME: Can object be None?
        )


class AnalysisOrderEditView(
    GenrequestNestedMixin,
    FormsetUpdateView,
):
    model = AnalysisOrder
    form_class = AnalysisOrderUpdateForm

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            (str(self.object), self.object.get_absolute_url()),
            ("Update", ""),
        ]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter_in_draft()  # type: ignore[attr-defined]

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-analysis-detail",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},
        )


class ExtractionOrderEditView(
    GenrequestNestedMixin,
    FormsetUpdateView,
):
    model = ExtractionOrder
    form_class = ExtractionOrderForm

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            (str(self.object), self.object.get_absolute_url()),
            ("Update", ""),
        ]

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter_in_draft()  # type: ignore[attr-defined]

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-extraction-detail",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},
        )


class AnalysisOrderCreateView(
    GenrequestNestedMixin,
    FormsetCreateView,
):
    form_class = AnalysisOrderForm
    model = AnalysisOrder

    def get_initial(self) -> Any:
        initial = super().get_initial()

        if "from_order" in self.request.GET:
            try:
                order = (
                    ExtractionOrder.objects.filter(
                        genrequest_id=self.kwargs["genrequest_id"],
                        id=self.request.GET["from_order"],
                    )
                    .exclude(status=Order.OrderStatus.DRAFT)
                    .get()
                )
                initial["from_order"] = order
                initial["use_all_samples"] = True
                initial["name"] = order.name + " - Analysis" if order.name else ""
            except ExtractionOrder.DoesNotExist as err:
                msg = f"Order {self.request.GET['from_order']} not found"
                raise Http404(msg) from err

        return initial

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            ("Create", ""),
        ]

    def get_success_url(self) -> str:
        # Clear any leftover error messages before redirect
        list(messages.get_messages(self.request))

        obj: AnalysisOrder = self.object  # type: ignore[assignment] # Possibly None
        if obj.from_order:
            return reverse(
                "genrequest-analysis-samples",
                kwargs={
                    "genrequest_id": self.genrequest.id,
                    "pk": obj.id,
                },
            )
        return reverse(
            "genrequest-analysis-samples-edit",
            kwargs={
                "genrequest_id": self.genrequest.id,
                "pk": self.object.id,  # type: ignore[union-attr]
            },
        )

    # Override form_invalid to show errors in the form
    # instead of just redirecting to the success URL.
    def form_invalid(self, form: Form) -> HttpResponse:
        for field, errors in form.errors.items():
            label = form.fields.get(field).label if field in form.fields else field
            for error in errors:
                messages.error(self.request, f"{label}: {error}")
        return super().form_invalid(form)


class ExtractionOrderCreateView(
    GenrequestNestedMixin,
    FormsetCreateView,
):
    form_class = ExtractionOrderForm
    model = ExtractionOrder

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            ("Create", ""),
        ]

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-extraction-samples-edit",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},  # type: ignore[union-attr] # FIXME: Can object be None?
        )


class EquipmentOrderQuantityUpdateView(GenrequestNestedMixin, BulkEditCollectionView):
    collection_class = EquipmentQuantityCollection
    template_name = "genlab_bestilling/equipmentorderquantity_form.html"
    model = EquimentOrderQuantity
    genrequest_accessor = "order__genrequest"

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        self.get_queryset()
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            (str(self.equipment_order), self.equipment_order.get_absolute_url()),
            ("Order quantity", ""),
        ]

    def get_queryset(self) -> QuerySet[Any]:
        self.equipment_order = (
            EquipmentOrder.objects.filter_allowed(self.request.user)
            .filter(
                id=self.kwargs["pk"],
            )
            .first()
        )
        return (
            super()
            .get_queryset()
            .filter(order_id=self.kwargs["pk"])
            .select_related("order", "equipment")
        )

    def get_collection_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_collection_kwargs()
        kwargs["context"] = {"order_id": self.kwargs["pk"]}
        return kwargs

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-equipment-detail",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.kwargs["pk"]},
        )

    def get_initial(self) -> Any:
        collection_class = self.get_collection_class()
        queryset = self.get_queryset()
        initial = collection_class(
            context={"order_id": self.kwargs["pk"]}
        ).models_to_list(queryset)
        return initial  # noqa: RET504


class SamplesFrontendView(GenrequestNestedMixin, DetailView):
    model = ExtractionOrder
    template_name = "genlab_bestilling/sample_form_frontend.html"

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            (str(self.object), self.object.get_absolute_url()),
            (
                "Samples",
                reverse(
                    "genrequest-extraction-samples",
                    kwargs={
                        "genrequest_id": self.object.genrequest_id,
                        "pk": self.object.id,
                    },
                ),
            ),
            ("Update", ""),
        ]

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["frontend_args"] = {
            "order": self.object.id,
            "csrf": get_token(self.request),
            "analysis_data": ExtractionSerializer(self.object).data,
        }
        return context

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter_in_draft()  # type: ignore[attr-defined]


class SamplesListView(GenrequestNestedMixin, SingleTableView):
    genrequest_accessor = "order__genrequest"
    table_pagination = False

    model = Sample
    table_class = SampleTable

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        self.get_queryset()
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            (str(self.extraction), self.extraction.get_absolute_url()),
            ("Samples", ""),
        ]

    def get_queryset(self) -> QuerySet[Any]:
        self.extraction = ExtractionOrder.objects.get(pk=self.kwargs.get("pk"))
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
        context["extraction"] = self.extraction
        return context


class AnalysisSamplesFrontendView(GenrequestNestedMixin, DetailView):
    model = AnalysisOrder
    template_name = "genlab_bestilling/analysis_sample_form_frontend.html"

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            (str(self.object), self.object.get_absolute_url()),
            (
                "Samples",
                reverse(
                    "genrequest-analysis-samples",
                    kwargs={
                        "genrequest_id": self.object.genrequest_id,
                        "pk": self.object.id,
                    },
                ),
            ),
            ("Update", ""),
        ]

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["frontend_args"] = {
            "order": self.object.id,
            "csrf": get_token(self.request),
            "analysis_data": AnalysisSerializer(self.object).data,
        }
        return context

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter_in_draft()  # type: ignore[attr-defined]


class AnalysisSamplesListView(GenrequestNestedMixin, SingleTableView):
    genrequest_accessor = "order__genrequest"
    table_pagination = False

    model = SampleMarkerAnalysis
    table_class = AnalysisSampleTable

    @cached_property
    def gen_crumbs(self) -> list[tuple]:
        self.get_queryset()
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (AnalysisOrder._meta.verbose_name_plural, ""),
            (str(self.analysis), self.analysis.get_absolute_url()),
            ("Samples", ""),
        ]

    def get_queryset(self) -> QuerySet[Any]:
        self.analysis = AnalysisOrder.objects.get(pk=self.kwargs.get("pk"))
        return (
            super()
            .get_queryset()
            .select_related(
                "marker",
                "sample",
                "sample__species",
                "sample__type",
                "sample__location",
            )
            .filter(order=self.kwargs["pk"])
            .values(
                "sample__genlab_id",
                "sample__species__name",
                "sample__type__name",
                "sample__location__name",
                "sample__guid",
                "sample__year",
                "sample__pop_id",
                "sample__name",
                "order",
            )
            .annotate(
                markers_names=StringAgg("marker__name", delimiter=", ", distinct=True)
            )
            # .order_by("species__name", "year", "location__name", "name")
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["analysis"] = self.analysis
        return context
