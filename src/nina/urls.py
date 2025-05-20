from django.urls import path

from .views import (
    ProjectCreateView,
    ProjectDetailView,
    ProjectEditView,
    ProjectList,
    ProjectMembershipUpdateView,
)

app_name = "nina"

urlpatterns = [
    path("projects/", ProjectList.as_view(), name="project-list"),
    path("projects/register/", ProjectCreateView.as_view(), name="project-create"),
    path("projects/<str:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path(
        "projects/<str:pk>/members/",
        ProjectMembershipUpdateView.as_view(),
        name="project-members-edit",
    ),
    path(
        "projects/<str:pk>/edit/",
        ProjectEditView.as_view(),
        name="project-edit",
    ),
]
