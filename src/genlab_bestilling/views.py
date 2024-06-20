from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import CreateView, DetailView, FormView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django_tables2.views import SingleTableView
from formset.views import (
    BulkEditCollectionView,
    FormViewMixin,
    IncompleteSelectResponseMixin,
)
from neapolitan.views import CRUDView

from .forms import (
    ActionForm,
    AnalysisOrderForm,
    EquipmentOrderForm,
    EquipmentQuantityCollection,
    ProjectForm,
    SamplesCollection,
)
from .models import (
    AnalysisOrder,
    EquimentOrderQuantity,
    EquipmentOrder,
    Order,
    Project,
    Sample,
)
from .tables import OrderTable, ProjectTable


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


class ProjectsView(LoginRequiredMixin, CRUDView):
    model = Project
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


class ProjectListView(LoginRequiredMixin, SingleTableView):
    model = Project
    table_class = ProjectTable


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project


class ProjectUpdateView(FormsetUpdateView):
    model = Project
    form_class = ProjectForm


class ProjectCreateView(FormsetCreateView):
    model = Project
    form_class = ProjectForm


class ProjectNestedMixin(LoginRequiredMixin):
    """
    Provide a Mixin to simplify views that operates under /projects/<id>/

    By default loads the project from the database,
    filter the current queryset using the project
    and adds it to the render context.
    """

    project_id_accessor = "project_id"

    def get_project(self):
        return Project.objects.get(id=self.kwargs["project_id"])

    def post(self, request, *args, **kwargs):
        self.project = self.get_project()
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.project = self.get_project()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        kwargs = {self.project_id_accessor: self.project.id}
        return super().get_queryset().filter(**kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        return ctx

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        return kwargs


class ProjectOrderListView(ProjectNestedMixin, SingleTableView):
    model = Order
    table_class = OrderTable


class EquipmentOrderDetailView(ProjectNestedMixin, DetailView):
    model = EquipmentOrder


class AnalysisOrderDetailView(ProjectNestedMixin, DetailView):
    model = AnalysisOrder


class ConfirmOrderActionView(ProjectNestedMixin, SingleObjectMixin, ActionView):
    model = Order

    def post(self, request, *args, **kwargs):
        self.project = self.get_project()
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form: Any) -> HttpResponse:
        # TODO: check state transition
        self.object.status = Order.OrderStatus.CONFIRMED
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class EquipmentOrderEditView(
    ProjectNestedMixin,
    FormsetUpdateView,
):
    model = EquipmentOrder
    form_class = EquipmentOrderForm

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(status=Order.OrderStatus.DRAFT)

    def get_success_url(self):
        return reverse(
            "project-order-detail",
            kwargs={"project_id": self.project.id, "pk": self.object.id},
        )


class EquipmentOrderCreateView(
    ProjectNestedMixin,
    FormsetCreateView,
):
    model = EquipmentOrder
    form_class = EquipmentOrderForm

    def get_success_url(self):
        return reverse(
            "project-order-detail",
            kwargs={"project_id": self.project.id, "pk": self.object.id},
        )


class AnalysisOrderEditView(
    ProjectNestedMixin,
    FormsetUpdateView,
):
    model = AnalysisOrder
    form_class = AnalysisOrderForm

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(status=Order.OrderStatus.DRAFT)

    def get_success_url(self):
        return reverse(
            "project-analysis-detail",
            kwargs={"project_id": self.project.id, "pk": self.object.id},
        )


class AnalysisOrderCreateView(
    ProjectNestedMixin,
    FormsetCreateView,
):
    form_class = AnalysisOrderForm
    model = AnalysisOrder

    def get_success_url(self):
        return reverse(
            "project-analysis-detail",
            kwargs={"project_id": self.project.id, "pk": self.object.id},
        )


class EquipmentOrderQuantityUpdateView(ProjectNestedMixin, BulkEditCollectionView):
    collection_class = EquipmentQuantityCollection
    template_name = "genlab_bestilling/equipmentorderquantity_form.html"
    model = EquimentOrderQuantity
    project_id_accessor = "order__project_id"

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
            "project-equipment-detail",
            kwargs={"project_id": self.project.id, "pk": self.kwargs["pk"]},
        )

    def get_initial(self):
        collection_class = self.get_collection_class()
        queryset = self.get_queryset()
        initial = collection_class(
            context={"order_id": self.kwargs["pk"]}
        ).models_to_list(queryset)
        return initial


class SamplesUpdateView(ProjectNestedMixin, BulkEditCollectionView):
    collection_class = SamplesCollection
    template_name = "genlab_bestilling/sample_form.html"
    model = Sample
    project_id_accessor = "order__project_id"

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
            "project": self.project,
        }
        return kwargs

    def get_success_url(self):
        return reverse(
            "project-analysis-detail",
            kwargs={"project_id": self.project.id, "pk": self.kwargs["pk"]},
        )

    def get_initial(self):
        collection_class = self.get_collection_class()
        queryset = self.get_queryset()
        initial = collection_class(
            context={"order_id": self.kwargs["pk"], "project": self.project}
        ).models_to_list(queryset)
        return initial
