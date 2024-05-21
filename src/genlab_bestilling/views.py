from apps.ui.views import UICreateView, UIDetailView, UIListView
from django.urls import reverse_lazy

from .models import GenLabProject, Order


class GenLabProjectsListView(UIListView):
    model = GenLabProject
    filterset_fields = ("name",)
    create_path = "projects-create"


class GenLabProjectCreateView(UICreateView):
    model = GenLabProject
    fields = (
        "project",
        "name",
        "area",
        "species",
        "sample_types",
        "analysis_types",
        "expected_total_samples",
        "analysis_timerange",
    )
    success_url = reverse_lazy("projects-list")


class GenLabProjectDetailView(UIDetailView):
    model = GenLabProject


class OrdersListView(UIListView):
    model = Order
    filterset_fields = ("polymorphic_ctype",)
    create_path = "projects-create"
