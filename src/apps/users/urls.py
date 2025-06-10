from django.urls import path

from apps.users.views import (  # type: ignore[attr-defined] # rename apps later
    UserDetail,
    UserRedirectView,
    UsersList,
    UserUpdate,
    UserUpdateView,
)

app_name = "users"
urlpatterns = [
    path("", view=UsersList.as_view(), name="list"),
    path("~redirect/", view=UserRedirectView.as_view(), name="redirect"),
    path("~update/", view=UserUpdateView.as_view(), name="update"),
    path("<int:pk>/", view=UserDetail.as_view(), name="detail"),
    path("<int:pk>/edit/", view=UserUpdate.as_view(), name="edit"),
]
