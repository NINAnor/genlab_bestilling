import django_tables2 as tables

from .models import Order, Project, Sample


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


class SampleTable(tables.Table):
    class Meta:
        model = Sample
        fields = (
            "guid",
            "name",
            "species",
            "type",
            "date",
            "pop_id",
            "location",
            "notes",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"
