import django_tables2 as tables

from .models import Genrequest, Order, Sample


class OrderTable(tables.Table):
    polymorphic_ctype = tables.Column(verbose_name="Type")
    id = tables.Column(linkify=True, orderable=False, empty_values=())

    class Meta:
        model = Order
        fields = (
            "name",
            "status",
            "polymorphic_ctype",
            "created_at",
            "last_modified_at",
        )
        sequence = (
            "id",
            "name",
            "status",
            "polymorphic_ctype",
        )
        empty_text = "No Orders"

    def render_polymorphic_ctype(self, value):
        return value.name

    def render_id(self, record):
        return str(record)


class GenrequestTable(tables.Table):
    project_id = tables.Column(linkify=True)

    class Meta:
        model = Genrequest
        fields = (
            "project_id",
            "name",
            "area",
            "species",
            "sample_types",
            "expected_total_samples",
            "expected_samples_delivery_date",
            "expected_analysis_delivery_date",
            "tags",
        )

        empty_text = "No requests"

    def render_tags(self, record):
        return ",".join(map(str, record.tags.all()))


class SampleTable(tables.Table):
    plate_positions = tables.Column(
        empty_values=(), orderable=False, verbose_name="Extraction position"
    )

    class Meta:
        model = Sample
        fields = (
            "guid",
            "name",
            "species",
            "type",
            "year",
            "pop_id",
            "location",
            "notes",
            "genlab_id",
            "plate_positions",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"

    def render_plate_positions(self, value):
        return ", ".join([str(v) for v in value.all()])


class AnalysisSampleTable(tables.Table):
    sample__location__name = tables.Column(verbose_name="Location")
    sample__type__name = tables.Column(verbose_name="Sample type")
    sample__species__name = tables.Column(verbose_name="Species")
    markers_names = tables.Column(verbose_name="Markers")

    class Meta:
        model = Sample
        fields = (
            "sample__genlab_id",
            "markers_names",
            "sample__guid",
            "sample__name",
            "sample__species__name",
            "sample__type__name",
            "sample__year",
            "sample__pop_id",
            "sample__location__name",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"
