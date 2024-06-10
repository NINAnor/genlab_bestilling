from django.urls import path

from .views import (
    AnalysisOrderEditView,
    EquipmentOrderEditView,
    ProjectOrderListView,
    ProjectsView,
)

appname = "genlab_bestilling"
urlpatterns = [
    *ProjectsView.get_urls(),
    path(
        "project/<int:project_id>/orders/",
        ProjectOrderListView.as_view(),
        name="project-order-list",
    ),
    path(
        "project/<int:project_id>/orders/equipment/create/",
        EquipmentOrderEditView.as_view(),
        name="project-equipment-create",
    ),
    path(
        "project/<int:project_id>/orders/equipment/<int:pk>/",
        EquipmentOrderEditView.as_view(),
        name="project-equipment-detail",
    ),
    path(
        "project/<int:project_id>/orders/analysis/create/",
        AnalysisOrderEditView.as_view(),
        name="project-analysis-create",
    ),
    path(
        "project/<int:project_id>/orders/analysis/<int:pk>/",
        AnalysisOrderEditView.as_view(),
        name="project-analysis-detail",
    ),
]
