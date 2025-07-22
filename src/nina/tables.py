import django_tables2 as tables

from .models import ProjectMembership


class MyProjectsTable(tables.Table):
    project = tables.Column(linkify=True)
    project__verified_at = tables.BooleanColumn()

    class Meta:
        model = ProjectMembership
        fields = ["project", "role", "project__active", "project__verified_at"]


class MembersTable(tables.Table):
    class Meta:
        model = ProjectMembership
        fields = ["user", "role"]
