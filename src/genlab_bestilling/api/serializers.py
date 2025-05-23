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

    def get_name(self, obj):
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

    def get_has_error(self, obj):
        try:
            return obj.has_error
        except exceptions.ValidationError as e:
            return e.detail[0]

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


class SampleCSVSerializer(serializers.ModelSerializer):
    type = SampleTypeSerializer()
    species = SpeciesSerializer()
    location = LocationSerializer(allow_null=True, required=False)

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
        )


class SampleUpdateSerializer(serializers.ModelSerializer):
    has_error = serializers.SerializerMethodField()

    def get_has_error(self, obj):
        try:
            return obj.has_error
        except exceptions.ValidationError as e:
            return e.detail[0]

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
