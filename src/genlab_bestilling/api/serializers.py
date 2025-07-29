from rest_framework import exceptions, serializers

from ..models import (
    AnalysisOrder,
    ExtractionOrder,
    Genrequest,
    Location,
    Marker,
    Sample,
    SampleMarkerAnalysis,
    SampleType,
    Species,
)


class OperationStatusSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField(allow_null=True)


class EnumSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class KoncivSerializer(EnumSerializer):
    type = serializers.CharField(source="konciv_type")
    konciv_id = serializers.CharField()


class MarkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marker
        fields = ("name",)


class SampleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SampleType
        fields = ("id", "name")


class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = ("id", "name")


class LocationSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ("id", "name")

    def get_name(self, obj: Location) -> str:
        return str(obj)


class LocationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "name")


class SampleSerializer(serializers.ModelSerializer):
    type = SampleTypeSerializer()
    species = SpeciesSerializer()
    location = LocationSerializer(allow_null=True, required=False)
    has_error = serializers.SerializerMethodField()

    def get_has_error(self, obj: Sample) -> bool:
        try:
            return obj.has_error
        except exceptions.ValidationError as e:
            return e.detail[0]  # type: ignore[return-value,index]  # TODO: check if this is actually bool.

    class Meta:
        model = Sample
        fields = (
            "id",
            "order",
            "guid",
            "name",
            "species",
            "year",
            "notes",
            "pop_id",
            "location",
            "volume",
            "type",
            "has_error",
            "genlab_id",
        )


class FlagField(serializers.Field):
    def to_representation(self, value: bool) -> str:
        return "x" if value else ""


class SampleCSVSerializer(serializers.ModelSerializer):
    type = SampleTypeSerializer()
    species = SpeciesSerializer()
    location = LocationSerializer(allow_null=True, required=False)
    fish_id = serializers.SerializerMethodField()
    analysis_orders = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    isolation_method = serializers.SerializerMethodField()
    is_marked = FlagField()
    is_plucked = FlagField()
    is_isolated = FlagField()
    internal_note = serializers.SerializerMethodField()

    class Meta:
        model = Sample
        fields = (
            "order",
            "guid",
            "name",
            "species",
            "type",
            "year",
            "pop_id",
            "location",
            "notes",
            "genlab_id",
            "fish_id",
            "analysis_orders",
            "project",
            "isolation_method",
            "is_marked",
            "is_plucked",
            "is_isolated",
            "internal_note",
        )

    def get_fish_id(self, obj: Sample) -> str:
        return obj.fish_id or "-"

    def get_analysis_orders(self, obj: Sample) -> list[str]:
        if not obj.order:
            return []

        analysis_orders = obj.order.analysis_orders.all()
        # Return all analysis order IDs as strings
        # only if there is exactly one analysis order, else return empty list.
        # This is to ensure no duplicate rows in staffs common sheet
        if analysis_orders.count() == 1:
            return [str(analysis_orders.first().id)]
        return []

    def get_project(self, obj: Sample) -> str:
        if obj.order and obj.order.genrequest and obj.order.genrequest.project:
            return str(obj.order.genrequest.project)
        return ""

    def get_isolation_method(self, obj: Sample) -> str:
        method = obj.isolation_method.first()
        return method.name if method else ""

    def get_internal_note(self, obj: Sample) -> str:
        if obj.internal_note:
            return obj.internal_note
        return ""


class LabelCSVSerializer(serializers.ModelSerializer):
    location = LocationSerializer(allow_null=True, required=False)

    class Meta:
        model = Sample
        fields = (
            "genlab_id",
            "guid",
            "name",
            "fish_id",
            "order",
            "location",
        )

    def get_fish_id(self, obj: Sample) -> str:
        return obj.fish_id or "-"


class SampleUpdateSerializer(serializers.ModelSerializer):
    has_error = serializers.SerializerMethodField()

    def get_has_error(self, obj: Sample) -> bool:
        try:
            return obj.has_error
        except exceptions.ValidationError as e:
            return e.detail[0]  # type: ignore[return-value,index] # TODO: check if this is actually bool.

    class Meta:
        model = Sample
        fields = (
            "id",
            "order",
            "guid",
            "species",
            "year",
            "name",
            "notes",
            "pop_id",
            "location",
            "type",
            "has_error",
        )


class SampleBulkSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField()
    name = serializers.ListField(
        child=serializers.CharField(required=False, allow_blank=True), required=False
    )
    pop_id = serializers.ListField(
        child=serializers.CharField(required=False, allow_blank=True), required=False
    )
    guid = serializers.ListField(
        child=serializers.CharField(required=False, allow_blank=True), required=False
    )

    class Meta:
        model = Sample
        fields = (
            "order",
            "species",
            "year",
            "guid",
            "name",
            "pop_id",
            "type",
            "location",
            "quantity",
        )


class SampleDeleteBulkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = ("order",)


class GenrequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genrequest
        fields = (
            "id",
            "project",
            "area",
        )


class ExtractionSerializer(serializers.ModelSerializer):
    species = SpeciesSerializer(many=True, read_only=True)
    sample_types = SampleTypeSerializer(many=True, read_only=True)
    genrequest = GenrequestSerializer()

    class Meta:
        model = ExtractionOrder
        fields = ("id", "genrequest", "species", "sample_types", "needs_guid")


class AnalysisSerializer(serializers.ModelSerializer):
    markers = MarkerSerializer(many=True, read_only=True)
    genrequest = GenrequestSerializer()

    class Meta:
        model = AnalysisOrder
        fields = ("id", "genrequest", "markers")


class SampleMarkerAnalysisSerializer(serializers.ModelSerializer):
    sample = SampleSerializer(read_only=True)

    class Meta:
        model = SampleMarkerAnalysis
        fields = ("id", "order", "sample", "marker")


class SampleMarkerAnalysisBulkSerializer(serializers.ModelSerializer):
    markers = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Marker.objects.all()
    )
    samples = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Sample.objects.all()
    )

    class Meta:
        model = SampleMarkerAnalysis
        fields = ("order", "samples", "markers")


class SampleMarkerAnalysisBulkDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(required=True), required=True
    )
