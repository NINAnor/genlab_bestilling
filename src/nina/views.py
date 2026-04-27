from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.views.generic import DetailView
from django_tables2.views import SingleTableView
from formset.views import (
    BulkEditCollectionView,
)

from genlab_bestilling.models import Genrequest, Order
from genlab_bestilling.tables import GenrequestTable, OrderTable
from shared.views import FormsetCreateView, FormsetUpdateView

from .forms import ProjectCreateForm, ProjectMembershipCollection, ProjectUpdateForm
from .models import Project, ProjectMembership
from .tables import MembersTable, MyProjectsTable


class ProjectList(LoginRequiredMixin, SingleTableView):
    model = ProjectMembership
    table_class = MyProjectsTable

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(user=self.request.user)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project

    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .prefetch_related("memberships")
            .filter(memberships=self.request.user)
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["table"] = MembersTable(data=self.object.members.all())

        # Get genetic projects (genrequests) for this project
        genrequests = (
            Genrequest.objects.filter(project=self.object)
            .select_related("area")
            .prefetch_related("species", "sample_types")
        )
        ctx["genrequests_table"] = GenrequestTable(data=genrequests)

        # Get orders for all genetic projects under this project
        orders = (
            Order.objects.filter(genrequest__project=self.object)
            .select_related("genrequest", "genrequest__project", "polymorphic_ctype")
            .order_by("-created_at")
        )
        ctx["orders_table"] = OrderTable(data=orders)

        return ctx


class ProjectMembershipUpdateView(
    LoginRequiredMixin, UserPassesTestMixin, BulkEditCollectionView
):
    collection_class = ProjectMembershipCollection
    template_name = "nina/projectmembership_form.html"
    model = ProjectMembership

    def test_func(self) -> bool:
        return (
            self.get_queryset()
            .filter(
                user=self.request.user,
                role__in=[ProjectMembership.Role.MANAGER, ProjectMembership.Role.OWNER],
            )
            .exists()
        )

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(project=self.kwargs["pk"])

    def get_collection_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_collection_kwargs()
        kwargs["context"] = {"project": self.kwargs["pk"]}
        return kwargs

    def get_success_url(self) -> str:
        return reverse(
            "nina:project-detail",
            kwargs={"pk": self.kwargs["pk"]},
        )

    def get_initial(self) -> Any:
        collection_class = self.get_collection_class()
        queryset = self.get_queryset()
        initial = collection_class(
            context={"project": self.kwargs["pk"]}
        ).models_to_list(queryset)
        return initial  # noqa: RET504


class ProjectCreateView(FormsetCreateView):
    model = Project
    form_class = ProjectCreateForm

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse(
            "nina:project-detail",
            kwargs={"pk": self.object.pk},  # type: ignore[union-attr]
        )


class ProjectEditView(FormsetUpdateView):
    model = Project
    form_class = ProjectUpdateForm

    def get_success_url(self) -> str:
        return reverse(
            "nina:project-detail",
            kwargs={"pk": self.object.pk},
        )
