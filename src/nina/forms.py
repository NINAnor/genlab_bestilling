from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Model
from formset.renderers.tailwind import FormRenderer

from genlab_bestilling.libs.formset import ContextFormCollection

from .models import Project, ProjectMembership


class ProjectMembershipForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)

    def reinit(self, context: dict[str, Any]) -> None:
        self.project_id = context["project"]

    def save(self, commit: bool = True) -> Model:
        obj = super().save(commit=False)
        obj.project_id = self.project_id
        if commit:
            obj.save()
            self.save_m2m()
        return obj

    class Meta:
        model = ProjectMembership
        fields = ("id", "user", "role")


class ProjectMembershipCollection(ContextFormCollection):
    min_siblings = 0
    add_label = "Add user"
    members = ProjectMembershipForm()
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def retrieve_instance(self, data: dict[str, Any]) -> ProjectMembership | None:
        if members := data.get("members"):
            try:
                return ProjectMembership.objects.get(id=members.get("id") or -1)
            except (AttributeError, ProjectMembership.DoesNotExist, ValueError):
                return ProjectMembership(
                    user_id=members.get("user"),
                    role=members.get("role"),
                    project_id=members.get("project_id"),
                )
        return None

    def update_holder_instances(self, name: str, holder: Any) -> None:
        if name == "members":
            holder.reinit(self.context)


class ProjectCreateForm(forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def __init__(self, *args, **kwargs) -> None:
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, commit: bool = True) -> Model:
        with transaction.atomic():
            obj = super().save(commit=True)
            ProjectMembership.objects.create(
                user=self.user, project=obj, role=ProjectMembership.Role.OWNER
            )
        return obj

    def clean_number(self) -> int:
        number = self.cleaned_data["number"]
        try:
            p = Project.objects.prefetch_related("members").get(pk=number)
            contacts = ", ".join(
                [
                    c.user.email
                    for c in p.members.filter(
                        models.Q(role=ProjectMembership.Role.MANAGER)
                        | models.Q(role=ProjectMembership.Role.OWNER)
                    )
                ]
            )

            msg = f"Project already exists, please contact {contacts} to be added to the project"  # noqa: E501
            raise ValidationError(msg)
        except Project.DoesNotExist:
            pass
        return number

    class Meta:
        model = Project
        fields = ("number", "name")


class ProjectUpdateForm(forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    class Meta:
        model = Project
        fields = ("name",)
