from django.urls import path
from django.views.generic import TemplateView

from ..models import AnalysisOrder, EquipmentOrder
from .views import (
    AnalysisOrderDetailView,
    AnalysisOrderListView,
    EquipmentOrderDetailView,
    EqupimentOrderListView,
    ExtractionOrderDetailView,
    ExtractionOrderListView,
    ExtractionPlateListView,
    ManaullyCheckedOrderActionView,
    OrderAnalysisSamplesListView,
    OrderExtractionSamplesListView,
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
        "orders/extraction/",
        ExtractionOrderListView.as_view(),
        name="order-extraction-list",
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
        "orders/extraction/<int:pk>/samples/",
        OrderExtractionSamplesListView.as_view(),
        name="order-extraction-samples",
    ),
    path(
        "orders/analysis/<int:pk>/samples/",
        OrderAnalysisSamplesListView.as_view(),
        name="order-analysis-samples",
    ),
    path(
        "samples/",
        SamplesListView.as_view(),
        name="samples-list",
    ),
    path(
        "orders/equipment/<int:pk>/",
        EquipmentOrderDetailView.as_view(),
        name="order-equipment-detail",
    ),
    path(
        "orders/extraction/<int:pk>/",
        ExtractionOrderDetailView.as_view(),
        name="order-extraction-detail",
    ),
    path(
        "orders/plates/",
        ExtractionPlateListView.as_view(),
        name="plates-list",
    ),
]
