import django_tables2 as tables

from .models import ProjectMembership


class MyProjectsTable(tables.Table):
    project = tables.Column(linkify=True)

    class Meta:
        model = ProjectMembership
        fields = ("project", "role")


class MembersTable(tables.Table):
    class Meta:
        model = ProjectMembership
        fields = ("user", "role")
