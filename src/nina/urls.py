from django.urls import path

from .views import ProjectDetailView, ProjectList, ProjectMembershipUpdateView

app_name = "nina"

urlpatterns = [
    path("projects/", ProjectList.as_view(), name="project-list"),
    path("projects/<str:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path(
        "projects/<str:pk>/members/",
        ProjectMembershipUpdateView.as_view(),
        name="project-members-edit",
    ),
]
