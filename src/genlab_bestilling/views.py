from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.urls import reverse
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
from neapolitan.views import CRUDView

from .api.serializers import AnalysisSerializer
from .forms import (
    ActionForm,
    AnalysisOrderForm,
    EquipmentOrderForm,
    EquipmentQuantityCollection,
    GenrequestEditForm,
    GenrequestForm,
    SamplesCollection,
)
from .models import (
    AnalysisOrder,
    EquimentOrderQuantity,
    EquipmentOrder,
    Genrequest,
    Order,
    Sample,
)
from .tables import GenrequestTable, OrderTable, SampleTable


class ActionView(FormView):
    form_class = ActionForm

    def get(self, request, *args, **kwargs):
        """
        Action forms should be used just to modify the system
        """
        self.http_method_not_allowed(self, request, *args, **kwargs)


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


class GenrequestsView(LoginRequiredMixin, CRUDView):
    model = Genrequest
    fields = (
        "number",
        "name",
        "area",
        "species",
        "sample_types",
        "analysis_types",
        "expected_total_samples",
        "analysis_timerange",
    )
    filterset_fields = ["name"]


class GenrequestListView(LoginRequiredMixin, SingleTableView):
    model = Genrequest
    table_class = GenrequestTable

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(project__memberships=self.request.user)


class GenrequestDetailView(LoginRequiredMixin, DetailView):
    model = Genrequest

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(project__memberships=self.request.user)


class GenrequestUpdateView(FormsetUpdateView):
    model = Genrequest
    form_class = GenrequestEditForm

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(project__memberships=self.request.user)

    def get_success_url(self):
        return reverse(
            "genrequest-detail",
            kwargs={"pk": self.object.id},
        )


class GenrequestCreateView(FormsetCreateView):
    model = Genrequest
    form_class = GenrequestForm

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(project__memberships=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse(
            "genrequest-detail",
            kwargs={"pk": self.object.id},
        )


class GenrequestNestedMixin(LoginRequiredMixin):
    """
    Provide a Mixin to simplify views that operates under /genrequests/<id>/

    By default loads the genrequest from the database,
    filter the current queryset using the genrequest
    and adds it to the render context.
    """

    genrequest_accessor = "genrequest"

    def get_genrequest(self):
        return Genrequest.objects.filter(project__memberships=self.request.user).get(
            id=self.kwargs["genrequest_id"]
        )

    def get_project_filtered(self, qs):
        filters = {
            f"{self.genrequest_accessor}__project__memberships": self.request.user
        }
        return qs.filter(**filters)

    def post(self, request, *args, **kwargs):
        self.genrequest = self.get_genrequest()
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.genrequest = self.get_genrequest()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        qs = self.get_project_filtered(qs=super().get_queryset())
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


class EquipmentOrderDetailView(GenrequestNestedMixin, DetailView):
    model = EquipmentOrder


class AnalysisOrderDetailView(GenrequestNestedMixin, DetailView):
    model = AnalysisOrder


class GenrequestOrderDeleteView(GenrequestNestedMixin, DeleteView):
    model = Order
    template_name = "genlab_bestilling/order_confirm_delete.html"

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

    def post(self, request, *args, **kwargs):
        self.genrequest = self.get_genrequest()
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Any) -> HttpResponse:
        i = self.object.get_real_instance()
        try:
            # TODO: check state transition
            i.confirm_order()
            messages.add_message(
                self.request, messages.SUCCESS, _("Your order is confirmed")
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

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(status=Order.OrderStatus.DRAFT)

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
    form_class = AnalysisOrderForm

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(status=Order.OrderStatus.DRAFT)

    def get_success_url(self):
        return reverse(
            "genrequest-analysis-detail",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},
        )


class AnalysisOrderCreateView(
    GenrequestNestedMixin,
    FormsetCreateView,
):
    form_class = AnalysisOrderForm
    model = AnalysisOrder

    def get_success_url(self):
        return reverse(
            "genrequest-analysis-samples-edit",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.object.id},
        )


class EquipmentOrderQuantityUpdateView(GenrequestNestedMixin, BulkEditCollectionView):
    collection_class = EquipmentQuantityCollection
    template_name = "genlab_bestilling/equipmentorderquantity_form.html"
    model = EquimentOrderQuantity
    genrequest_accessor = "order__genrequest"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .filter(order_id=self.kwargs["pk"], order__status=Order.OrderStatus.DRAFT)
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
    model = AnalysisOrder
    template_name = "genlab_bestilling/sample_form_frontend.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["frontend_args"] = {
            "order": self.object.id,
            "csrf": get_token(self.request),
            "analysis_data": AnalysisSerializer(self.object).data,
        }
        return context

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(status=Order.OrderStatus.DRAFT)


class SamplesListView(GenrequestNestedMixin, SingleTableView):
    genrequest_accessor = "order__genrequest"
    table_pagination = False

    model = Sample
    table_class = SampleTable

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related("type", "location", "species")
            .filter(order=self.kwargs["pk"])
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["analysis"] = AnalysisOrder.objects.get(pk=self.kwargs.get("pk"))
        return context


class SamplesUpdateView(GenrequestNestedMixin, BulkEditCollectionView):
    collection_class = SamplesCollection
    template_name = "genlab_bestilling/sample_form.html"
    model = Sample
    genrequest_accessor = "order__genrequest"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .filter(order_id=self.kwargs["pk"], order__status=Order.OrderStatus.DRAFT)
        )

    def get_collection_kwargs(self):
        kwargs = super().get_collection_kwargs()
        kwargs["context"] = {
            "order_id": self.kwargs["pk"],
            "genrequest": self.genrequest,
        }
        return kwargs

    def get_success_url(self):
        return reverse(
            "genrequest-analysis-detail",
            kwargs={"genrequest_id": self.genrequest.id, "pk": self.kwargs["pk"]},
        )

    def get_initial(self):
        collection_class = self.get_collection_class()
        queryset = self.get_queryset()
        initial = collection_class(
            context={"order_id": self.kwargs["pk"], "genrequest": self.genrequest}
        ).models_to_list(queryset)
        return initial
