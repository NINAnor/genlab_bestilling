from django import forms
from django.db import transaction
from formset.renderers.tailwind import FormRenderer
from genlab_bestilling.libs.formset import ContextFormCollection

from .models import Project, ProjectMembership


class ProjectMembershipForm(forms.ModelForm):
    id = forms.IntegerField(required=False, widget=forms.widgets.HiddenInput)

    def reinit(self, context):
        self.project_id = context["project"]

    def save(self, commit=True):
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

    def retrieve_instance(self, data):
        if data := data.get("members"):
            try:
                return ProjectMembership.objects.get(id=data.get("id") or -1)
            except (AttributeError, ProjectMembership.DoesNotExist, ValueError):
                return ProjectMembership(
                    user_id=data.get("user"),
                    role=data.get("role"),
                    project_id=data.get("project_id"),
                )

    def update_holder_instances(self, name, holder):
        if name == "members":
            holder.reinit(self.context)


class ProjectCreateForm(forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        with transaction.atomic():
            obj = super().save(commit=True)
            ProjectMembership.objects.create(
                user=self.user, project=obj, role=ProjectMembership.Role.OWNER
            )
        return obj

    class Meta:
        model = Project
        fields = ("number", "name")


class ProjectUpdateForm(forms.ModelForm):
    default_renderer = FormRenderer(field_css_classes="mb-3")

    class Meta:
        model = Project
        fields = ("name",)
