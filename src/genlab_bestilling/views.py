from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.generic import DetailView
from django_tables2.views import SingleTableView
from formset.views import EditCollectionView
from neapolitan.views import CRUDView

from .forms import AnalysisOrderCollection, EquipmentOrderCollection
from .models import AnalysisOrder, EquipmentOrder, Order, Project
from .tables import OrderTable


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


class ProjectOrderListView(SingleTableView):
    model = Order
    table_class = OrderTable

    def get_queryset(self) -> QuerySet[Any]:
        self.project = Project.objects.get(id=self.kwargs["project_id"])
        return super().get_queryset().filter(project_id=self.project.id)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        return ctx


class EquipmentOrderDetailView(DetailView):
    model = EquipmentOrder

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(project_id=self.kwargs["project_id"])


class EquipmentOrderEditView(EditCollectionView):
    model = EquipmentOrder
    collection_class = EquipmentOrderCollection
    template_name = "genlab_bestilling/generic_form.html"

    def get_success_url(self):
        return reverse(
            "project-order-list", kwargs={"project_id": self.kwargs["project_id"]}
        )

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:
        try:
            return super().get_object(queryset)
        except AttributeError:
            return self.model(project_id=self.kwargs["project_id"])


class AnalysisOrderEditView(EditCollectionView):
    model = AnalysisOrder
    collection_class = AnalysisOrderCollection
    template_name = "genlab_bestilling/generic_form.html"

    def get_success_url(self):
        return reverse(
            "project-order-list", kwargs={"project_id": self.kwargs["project_id"]}
        )

    def get_object(self, queryset: QuerySet[Any] | None = ...) -> Model:
        try:
            return super().get_object(queryset)
        except AttributeError:
            return self.model(project_id=self.kwargs["project_id"])
