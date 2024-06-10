from django.urls import path

from .views import (
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
        "project/<int:project_id>/equipment/create/",
        EquipmentOrderEditView.as_view(),
        name="project-equipment-create",
    ),
    path(
        "project/<int:project_id>/equipment/<int:pk>/",
        EquipmentOrderEditView.as_view(),
        name="project-equipment-detail",
    ),
]
