from typing import Any, Self

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView

from capps.ui.views import UIDetailView, UIListView, UIUpdateView

from .exceptions import NotAuthenticated
from .filters import UserFilterSet
from .tables import UserTable

User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["first_name", "last_name"]
    success_message = _("Information successfully updated")

    def get_success_url(self: Self) -> str:
        if not self.request.user.is_authenticated:
            raise NotAuthenticated
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> Any:
        return self.request.user


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self: Self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


class UsersList(UIListView):
    model = User
    table_class = UserTable
    filterset_class = UserFilterSet
    active_dropdown = "users"
    active_route = "users_list"


class UserUpdate(UIUpdateView):
    model = User
    fields = [
        "first_name",
        "last_name",
    ]
    active_dropdown = "users"


class UserDetail(UIDetailView):
    model = User
    active_dropdown = "users"
