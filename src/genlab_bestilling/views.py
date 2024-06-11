import traceback
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.generic import DetailView, UpdateView
from django_tables2.views import SingleTableView
from formset.views import (
    EditCollectionView,
    FormViewMixin,
    IncompleteSelectResponseMixin,
)
from neapolitan.views import CRUDView

from .forms import AnalysisOrderCollection, EquipmentOrderCollection, ProjectForm
from .models import AnalysisOrder, EquipmentOrder, Order, Project
from .tables import OrderTable, ProjectTable


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


class ProjectUpdateView(
    LoginRequiredMixin, IncompleteSelectResponseMixin, FormViewMixin, UpdateView
):
    model = Project
    form_class = ProjectForm


class ProjectCreateView(
    LoginRequiredMixin, IncompleteSelectResponseMixin, FormViewMixin, UpdateView
):
    model = Project
    form_class = ProjectForm

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:
        try:
            return super().get_object(queryset)
        except AttributeError:
            print(traceback.format_exc())
            return self.model()

    def get_success_url(self):
        return reverse("project-detail", kwargs={"pk": self.object.id})


class ProjectOrderListView(LoginRequiredMixin, SingleTableView):
    model = Order
    table_class = OrderTable

    def get_queryset(self) -> QuerySet[Any]:
        self.project = Project.objects.get(id=self.kwargs["project_id"])
        return super().get_queryset().filter(project_id=self.project.id)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        return ctx


class EquipmentOrderDetailView(LoginRequiredMixin, DetailView):
    model = EquipmentOrder

    def get_queryset(self) -> QuerySet[Any]:
        self.project = Project.objects.get(id=self.kwargs["project_id"])
        return super().get_queryset().filter(project_id=self.project.id)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        return ctx


class AnalysisOrderDetailView(LoginRequiredMixin, DetailView):
    model = AnalysisOrder

    def get_queryset(self) -> QuerySet[Any]:
        self.project = Project.objects.get(id=self.kwargs["project_id"])
        return super().get_queryset().filter(project_id=self.project.id)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        return ctx


class EquipmentOrderEditView(LoginRequiredMixin, EditCollectionView):
    model = EquipmentOrder
    collection_class = EquipmentOrderCollection
    template_name = "genlab_bestilling/equipmentorder_form.html"

    def get_queryset(self) -> QuerySet[Any]:
        self.project = Project.objects.get(id=self.kwargs["project_id"])
        return super().get_queryset().filter(project_id=self.project.id)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        return ctx

    def get_success_url(self):
        return reverse(
            "project-order-list", kwargs={"project_id": self.kwargs["project_id"]}
        )


class EquipmentOrderCreateView(EquipmentOrderEditView):
    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:
        try:
            return super().get_object(self.get_queryset())
        except AttributeError:
            print(traceback.format_exc())
            return self.model(project_id=self.kwargs["project_id"])


class AnalysisOrderEditView(LoginRequiredMixin, EditCollectionView):
    model = AnalysisOrder
    collection_class = AnalysisOrderCollection
    template_name = "genlab_bestilling/analysisorder_form.html"

    def get_queryset(self) -> QuerySet[Any]:
        self.project = Project.objects.get(id=self.kwargs["project_id"])
        return super().get_queryset().filter(project_id=self.project.id)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        return ctx

    def get_success_url(self):
        return reverse(
            "project-order-list", kwargs={"project_id": self.kwargs["project_id"]}
        )


class AnalysisOrderCreateView(AnalysisOrderEditView):
    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:
        try:
            return super().get_object(self.get_queryset())
        except AttributeError:
            return self.model(project_id=self.kwargs["project_id"])
