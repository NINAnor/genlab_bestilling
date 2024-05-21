from django.urls import path

from .views import (
    GenLabProjectCreateView,
    GenLabProjectDetailView,
    GenLabProjectsListView,
    OrdersListView,
)

appname = "genlab_bestilling"
urlpatterns = [
    path("projects/", GenLabProjectsListView.as_view(), name="projects-list"),
    path("projects/create/", GenLabProjectCreateView.as_view(), name="projects-create"),
    path(
        "projects/<int:pk>/", GenLabProjectDetailView.as_view(), name="projects-detail"
    ),
    path(
        "projects/<int:project_id>/orders/",
        OrdersListView.as_view(),
        name="orders-list",
    ),
]
