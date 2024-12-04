from django.urls import path
from django.views.generic import TemplateView

from ..models import AnalysisOrder, EquipmentOrder
from .views import (
    AnalysisOrderDetailView,
    AnalysisOrderListView,
    EquipmentOrderDetailView,
    EqupimentOrderListView,
    ExtractionPlateListView,
    ManaullyCheckedOrderActionView,
    OrderToDraftActionView,
    SamplesListView,
)

app_name = "genlab.staff"

urlpatterns = [
    path("", TemplateView.as_view(template_name="staff/base.html"), name="dashboard"),
    path(
        "orders/analysis/", AnalysisOrderListView.as_view(), name="order-analysis-list"
    ),
    path(
        "orders/equipment/",
        EqupimentOrderListView.as_view(),
        name="order-equipment-list",
    ),
    path(
        "orders/analysis/<int:pk>/",
        AnalysisOrderDetailView.as_view(),
        name="order-analysis-detail",
    ),
    path(
        "orders/<int:pk>/to-draft/",
        OrderToDraftActionView.as_view(model=AnalysisOrder),
        name="order-to-draft",
    ),
    path(
        "orders/<int:pk>/to-draft/",
        OrderToDraftActionView.as_view(model=EquipmentOrder),
    ),
    path(
        "orders/<int:pk>/manually-checked/",
        ManaullyCheckedOrderActionView.as_view(model=AnalysisOrder),
        name="order-manually-checked",
    ),
    path(
        "orders/analysis/<int:pk>/samples/",
        SamplesListView.as_view(),
        name="order-analysis-samples",
    ),
    path(
        "orders/equipment/<int:pk>/",
        EquipmentOrderDetailView.as_view(),
        name="order-equipment-detail",
    ),
    path(
        "orders/plates/",
        ExtractionPlateListView.as_view(),
        name="plates-list",
    ),
]
