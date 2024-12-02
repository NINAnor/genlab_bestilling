import django_tables2 as tables

from ..models import AnalysisOrder, EquipmentOrder, Order, Sample


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


class SampleTable(tables.Table):
    # guid = tables.Column(
    #     linkify=("staff:order-equipment-detail", {"pk": tables.A("id")}),
    #     orderable=False,
    #     empty_values=(),
    # )

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
            "desidered_extractions",
        )
        attrs = {"class": "w-full table-auto tailwind-table table-sm"}

        empty_text = "No Samples"
