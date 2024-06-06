from django.contrib.auth.mixins import LoginRequiredMixin
from neapolitan.views import CRUDView

from .models import Order, Project


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


class OrdersView(CRUDView):
    model = Order
    filterset_fields = ("polymorphic_ctype",)
