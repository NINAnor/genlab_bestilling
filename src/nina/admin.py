from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters import admin as unfold_filters

from .models import (
    Project,
    ProjectMembership,
)


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    autocomplete_fields = ["user"]


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    M = Project
    list_display = [
        M.number.field.name,
        M.name.field.name,
        M.active.field.name,
        M.verified_at.field.name,
    ]

    search_help_text = "Search by project number or name"
    search_fields = [M.number.field.name, M.name.field.name]

    readonly_fields = [M.verified_at.field.name]
    list_filter = [
        (M.number.field.name, unfold_filters.FieldTextFilter),
        (M.name.field.name, unfold_filters.FieldTextFilter),
        M.active.field.name,
        M.verified_at.field.name,
    ]
    list_filter_submit = True
    list_filter_sheet = False
    inlines = [ProjectMembershipInline]


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(ModelAdmin):
    M = ProjectMembership
    search_fields = [
        f"{M.project.field.name}__{Project.number.field.name}",
        f"{M.project.field.name}__{Project.name.field.name}",
        f"{M.user.field.name}__email",
    ]
    list_filter = [M.role.field.name]
    list_display = [M.project.field.name, M.user.field.name, M.role.field.name]
    autocomplete_fields = [M.project.field.name, M.user.field.name]
