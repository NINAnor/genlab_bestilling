from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    Project,
    ProjectMembership,
)


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    autocomplete_fields = ["user"]


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    search_fields = ["number", "name"]
    list_filter = ["active"]
    list_display = ["number", "name", "active"]

    inlines = [ProjectMembershipInline]


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(ModelAdmin):
    search_fields = ["project__number", "project__name", "user__email"]
    list_filter = ["role"]
    list_display = ["project", "user", "role"]
    autocomplete_fields = ["project", "user"]
