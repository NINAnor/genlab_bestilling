import django_tables2 as tables

from .models import Order, Project


class OrderTable(tables.Table):
    polymorphic_ctype = tables.Column(verbose_name="Type")
    name = tables.Column(linkify=True)

    class Meta:
        model = Order
        fields = ("name", "status", "polymorphic_ctype", "species", "sample_types")

        empty_text = "No Orders"

    def render_polymorphic_ctype(self, value):
        return value.name


class ProjectTable(tables.Table):
    number = tables.Column(linkify=True)

    class Meta:
        model = Project
        fields = (
            "number",
            "name",
            "area",
            "species",
            "sample_types",
            "analysis_types",
            "expected_total_samples",
            "analysis_timerange",
        )

        empty_text = "No Projects"
