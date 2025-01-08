from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import StringAgg
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin
from django_tables2.views import SingleTableView
from formset.views import (
    BulkEditCollectionView,
    FormViewMixin,
    IncompleteSelectResponseMixin,
)
from rest_framework.exceptions import ValidationError
from view_breadcrumbs import BaseBreadcrumbMixin

from .api.serializers import ExtractionSerializer
from .forms import (
    ActionForm,
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
from .tables import AnalysisSampleTable, GenrequestTable, OrderTable, SampleTable


class ActionView(FormView):
    form_class = ActionForm

    def get(self, request, *args, **kwargs):
        """
        Action forms should be used just to modify the system
        """
        self.http_method_not_allowed(self, request, *args, **kwargs)

    def get_success_url(self) -> str:
        return self.request.path_info


class FormsetCreateView(
    IncompleteSelectResponseMixin,
    FormViewMixin,
    LoginRequiredMixin,
    CreateView,
):
    pass


class FormsetUpdateView(
    IncompleteSelectResponseMixin, FormViewMixin, LoginRequiredMixin, UpdateView
):
    pass


class GenrequestListView(BaseBreadcrumbMixin, LoginRequiredMixin, SingleTableView):
    model = Genrequest
    table_class = GenrequestTable
    add_home = False

    @cached_property
    def crumbs(self):
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
    def crumbs(self):
        return [
            (self.model._meta.verbose_name_plural, reverse("genrequest-list")),
            (str(self.object), ""),
        ]

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter_allowed(self.request.user)


class GenrequestUpdateView(BaseBreadcrumbMixin, FormsetUpdateView):
    model = Genrequest
    form_class = GenrequestEditForm
    add_home = False

    @cached_property
    def crumbs(self):
        return [
            (self.model._meta.verbose_name_plural, reverse("genrequest-list")),
            (
                str(self.object),
                reverse("genrequest-detail", kwargs={"pk": self.object.pk}),
            ),
            ("Update", ""),
        ]

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter_allowed(self.request.user)

    def get_success_url(self):
        return reverse(
            "genrequest-detail",
            kwargs={"pk": self.object.id},
        )


class GenrequestDeleteView(BaseBreadcrumbMixin, DeleteView):
    model = Genrequest

    add_home = False

    @cached_property
    def crumbs(self):
        return [
            (self.model._meta.verbose_name_plural, reverse("genrequest-list")),
            (
                str(self.object),
                reverse("genrequest-detail", kwargs={"pk": self.object.pk}),
            ),
            ("Delete", ""),
        ]

    def get_success_url(self):
        return reverse(
            "genrequest-list",
        )


class GenrequestCreateView(BaseBreadcrumbMixin, FormsetCreateView):
    model = Genrequest
    form_class = GenrequestForm

    add_home = False

    @cached_property
    def crumbs(self):
        return [
            (self.model._meta.verbose_name_plural, reverse("genrequest-list")),
            ("Create", ""),
        ]

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter_allowed(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse(
            "genrequest-detail",
            kwargs={"pk": self.object.id},
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
    gen_crumbs = []

    @cached_property
    def crumbs(self):
        return [
            (Genrequest._meta.verbose_name_plural, reverse("genrequest-list")),
            (
                str(self.genrequest),
                self.genrequest.get_absolute_url(),
            ),
        ] + self.gen_crumbs

    def get_genrequest(self):
        return Genrequest.objects.filter_allowed(self.request.user).get(
            id=self.kwargs["genrequest_id"]
        )

    def post(self, request, *args, **kwargs):
        self.genrequest = self.get_genrequest()
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.genrequest = self.get_genrequest()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset().filter_allowed(self.request.user)
        kwargs = {f"{self.genrequest_accessor}_id": self.genrequest.id}
        return qs.filter(**kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["genrequest"] = self.genrequest
        return ctx

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["genrequest"] = self.genrequest
        return kwargs


class GenrequestOrderListView(GenrequestNestedMixin, SingleTableView):
    model = Order
    table_class = OrderTable
    gen_crumbs = [("Orders", "")]

    def get_queryset(self):
        return super().get_queryset().select_related("genrequest", "polymorphic_ctype")


class EquipmentOrderDetailView(GenrequestNestedMixin, DetailView):
    model = EquipmentOrder

    @cached_property
    def gen_crumbs(self):
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            (str(self.object), ""),
        ]


class AnalysisOrderDetailView(GenrequestNestedMixin, DetailView):
    model = AnalysisOrder

    @cached_property
    def gen_crumbs(self):
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            (str(self.object), ""),
        ]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("genrequest", "from_order", "polymorphic_ctype")
            .prefetch_related("sample_markers", "markers")
        )


class ExtractionOrderDetailView(GenrequestNestedMixin, DetailView):
    model = ExtractionOrder

    @cached_property
    def gen_crumbs(self):
        return [
            (
                "Orders",
                reverse(
                    "genrequest-order-list",
                    kwargs={"genrequest_id": self.kwargs["genrequest_id"]},
                ),
            ),
            (self.model._meta.verbose_name_plural, ""),
            (str(self.object), ""),
        ]


class GenrequestOrderDeleteView(GenrequestNestedMixin, DeleteView):
    model = Order
    template_name = "genlab_bestilling/order_confirm_delete.html"

    @cached_property
    def gen_crumbs(self):
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
            ("Delete", ""),
        ]

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        return qs.filter(status=Order.OrderStatus.DRAFT)

    def get_object(self, queryset=None) -> Order:
        return (super().get_object(queryset)).get_real_instance()

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        del kwargs["genrequest"]
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Order #{self.kwargs['pk']} deleted!")
        return response

    def get_success_url(self) -> str:
        return reverse(
            "genrequest-order-list", kwargs={"genrequest_id": self.genrequest.pk}
        )


class ConfirmOrderActionView(GenrequestNestedMixin, SingleObjectMixin, ActionView):
    model = Order

    def get_queryset(self):
        return super().get_queryset().filter_in_draft()

    def post(self, request, *args, **kwargs):
        self.genrequest = self.get_genrequest()
        self.object = (self.get_object()).get_real_instance()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Any) -> HttpResponse:
        try:
            # TODO: check state transition
            self.object.confirm_order()
            messages.add_message(
                self.request, messages.SUCCESS, _("Your order is confirmed")
            )
        except (Order.CannotConfirm, ValidationError) as e:
            messages.add_message(
                self.request,
                messages.ERROR,
                f'Error: {",".join(map(lambda error: str(error), e.detail))}',
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())


class CloneOrderActionView(GenrequestNestedMixin, SingleObjectMixin, ActionView):
    model = Order

    def post(self, request, *args, **kwargs):
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
                f'Error: {",".join(map(lambda error: str(error), e.detail))}',
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()

    def form_invalid(self, form):
        return HttpResponseRedirect(self.get_success_url())


class EquipmentOrderEditView(
    GenrequestNestedMixin,
    FormsetUpdateView,
):
    model = EquipmentOrder
    form_class = EquipmentOrderForm

    @cached_property
    def gen_crumbs(self):
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

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter_in_draft()

    def get_success_url(self):
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
    def gen_crumbs(self):
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

    def get_success_url(self):
        return reverse(
            "genrequest-equipment-quantity-update",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},
        )


class AnalysisOrderEditView(
    GenrequestNestedMixin,
    FormsetUpdateView,
):
    model = AnalysisOrder
    form_class = AnalysisOrderUpdateForm

    @cached_property
    def gen_crumbs(self):
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

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter_in_draft()

    def get_success_url(self):
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
    def gen_crumbs(self):
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

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter_in_draft()

    def get_success_url(self):
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

    @cached_property
    def gen_crumbs(self):
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

    def get_success_url(self):
        return reverse(
            "genrequest-analysis-samples-edit",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},
        )


class ExtractionOrderCreateView(
    GenrequestNestedMixin,
    FormsetCreateView,
):
    form_class = ExtractionOrderForm
    model = ExtractionOrder

    @cached_property
    def gen_crumbs(self):
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

    def get_success_url(self):
        return reverse(
            "genrequest-extraction-samples-edit",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},
        )


class EquipmentOrderQuantityUpdateView(GenrequestNestedMixin, BulkEditCollectionView):
    collection_class = EquipmentQuantityCollection
    template_name = "genlab_bestilling/equipmentorderquantity_form.html"
    model = EquimentOrderQuantity
    genrequest_accessor = "order__genrequest"

    @cached_property
    def gen_crumbs(self):
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

    def get_collection_kwargs(self):
        kwargs = super().get_collection_kwargs()
        kwargs["context"] = {"order_id": self.kwargs["pk"]}
        return kwargs

    def get_success_url(self):
        return reverse(
            "genrequest-equipment-detail",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.kwargs["pk"]},
        )

    def get_initial(self):
        collection_class = self.get_collection_class()
        queryset = self.get_queryset()
        initial = collection_class(
            context={"order_id": self.kwargs["pk"]}
        ).models_to_list(queryset)
        return initial


class SamplesFrontendView(GenrequestNestedMixin, DetailView):
    model = ExtractionOrder
    template_name = "genlab_bestilling/sample_form_frontend.html"

    @cached_property
    def gen_crumbs(self):
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

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter_in_draft()


class SamplesListView(GenrequestNestedMixin, SingleTableView):
    genrequest_accessor = "order__genrequest"
    table_pagination = False

    model = Sample
    table_class = SampleTable

    @cached_property
    def gen_crumbs(self):
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
    template_name = "genlab_bestilling/sample_form_frontend.html"

    @cached_property
    def gen_crumbs(self):
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
            # "analysis_data": ExtractionSerializer(self.object).data,
        }
        return context

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter_in_draft()


class AnalysisSamplesListView(GenrequestNestedMixin, SingleTableView):
    genrequest_accessor = "analysis_order__genrequest"
    table_pagination = False

    model = SampleMarkerAnalysis
    table_class = AnalysisSampleTable

    @cached_property
    def gen_crumbs(self):
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
            .filter(analysis_order=self.kwargs["pk"])
            .values(
                "sample__genlab_id",
                "sample__species__name",
                "sample__type__name",
                "sample__location__name",
                "sample__guid",
                "sample__year",
                "sample__pop_id",
                "sample__name",
                "analysis_order",
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
