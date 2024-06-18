from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.generic import CreateView, DetailView, UpdateView
from django_tables2.views import SingleTableView
from formset.views import (
    FormViewMixin,
    IncompleteSelectResponseMixin,
)
from neapolitan.views import CRUDView

from .forms import (
    AnalysisOrderForm,
    EquipmentOrderForm,
    ProjectForm,
)
from .models import AnalysisOrder, EquipmentOrder, Order, Project
from .tables import OrderTable, ProjectTable


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
    def get_project(self):
        return Project.objects.get(id=self.kwargs["project_id"])

    def post(self, request, *args, **kwargs):
        self.project = self.get_project()
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.project = self.get_project()
        return super().get(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(project_id=self.project.id)

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


class EquipmentOrderEditView(
    ProjectNestedMixin,
    FormsetUpdateView,
):
    model = EquipmentOrder
    form_class = EquipmentOrderForm

    def get_success_url(self):
        return reverse(
            "project-analysis-detail",
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
            "project-analysis-detail",
            kwargs={"project_id": self.project.id, "pk": self.object.id},
        )


class AnalysisOrderEditView(
    ProjectNestedMixin,
    FormsetUpdateView,
):
    model = AnalysisOrder
    form_class = AnalysisOrderForm

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


class SamplesView(LoginRequiredMixin, DetailView):
    model = AnalysisOrder
    template_name = "genlab_bestilling/samples.html"

    def get_queryset(self) -> QuerySet[Any]:
        self.project = Project.objects.get(id=self.kwargs["project_id"])
        return super().get_queryset().filter(project_id=self.project.id)
