import django_tables2 as tables

from ..models import AnalysisOrder, EquipmentOrder, ExtractionPlate, Order, Sample


class OrderTable(tables.Table):
    id = tables.Column(
        linkify=True,
        orderable=False,
        empty_values=(),
    )

    class Meta:
        model = Order
        fields = (
            "name",
            "status",
            "species",
            "sample_types",
            "genrequest",
            "genrequest__name",
            "genrequest__project",
            "genrequest__area",
            "genrequest__analysis_timerange",
            "genrequest__expected_total_samples",
            "genrequest__samples_owner",
            "created_at",
            "last_modified_at",
        )
        sequence = (
            "id",
            "name",
            "status",
            "species",
            "sample_types",
        )
        empty_text = "No Orders"

    def render_id(self, record):
        return str(record)


class AnalysisOrderTable(OrderTable):
    id = tables.Column(
        linkify=("staff:order-analysis-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    class Meta(OrderTable.Meta):
        model = AnalysisOrder
        fields = ("return_samples",)


class EquipmentOrderTable(OrderTable):
    id = tables.Column(
        linkify=("staff:order-equipment-detail", {"pk": tables.A("id")}),
        orderable=False,
        empty_values=(),
    )

    class Meta(OrderTable.Meta):
        model = EquipmentOrder


class OrderSampleTable(tables.Table):
    plate_positions = tables.Column(
        empty_values=(), orderable=False, verbose_name="Extraction position"
    )

    class Meta:
        model = Sample
        fields = (
            "genlab_id",
            "guid",
            "name",
            "species",
            "type",
            "year",
            "pop_id",
            "location",
            "notes",
            "desired_extractions",
            "plate_positions",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"

    def render_plate_positions(self, value):
        return ", ".join([str(v) for v in value.all()])


class SampleTable(tables.Table):
    plate_positions = tables.Column(
        empty_values=(), orderable=False, verbose_name="Extraction position"
    )

    class Meta:
        model = Sample
        fields = (
            "genlab_id",
            "guid",
            "name",
            "species",
            "type",
            "year",
            "pop_id",
            "location",
            "notes",
            "desired_extractions",
            "order",
            "order__status",
            "order__genrequest__project",
            "plate_positions",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"

    def render_plate_positions(self, value):
        return ", ".join([str(v) for v in value.all()])


class PlateTable(tables.Table):
    class Meta:
        model = ExtractionPlate
        fields = (
            "id",
            "created_at",
            "last_updated_at",
            "samples_count",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Plates"
