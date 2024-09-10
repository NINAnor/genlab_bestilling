from rest_framework import exceptions, serializers

from ..models import (
    AnalysisOrder,
    Genrequest,
    Location,
    Marker,
    Sample,
    SampleType,
    Species,
)


class OperationStatusSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField(allow_null=True)


class EnumSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


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
    date = serializers.DateField(
        required=False,
        input_formats=[
            "iso-8601",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%SZ",
            "%m/%d/%Y",
        ],
    )

    # TODO: validate location
    ## species in (Laks, Ørret, Elvemusling and  Salamander)
    #   - should have location with river_id
    ## order.genrequest.area in (
    #   Akvatisk, Amfibier, Biodiversitet, Fisk, Parasitt og sykdomspåvisning
    # )
    #   - should have a location
    ## other
    # - location is optional

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
            "date",
            "notes",
            "pop_id",
            "location",
            "volume",
            "type",
            "has_error",
        )


class SampleUpdateSerializer(serializers.ModelSerializer):
    has_error = serializers.SerializerMethodField()
    date = serializers.DateField(
        required=False,
        input_formats=[
            "iso-8601",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%SZ",
            "%m/%d/%Y",
        ],
    )

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
            "markers",
            "date",
            "name",
            "notes",
            "pop_id",
            "location",
            "type",
            "has_error",
        )


class SampleBulkSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField()
    date = serializers.DateField(
        required=False,
        input_formats=[
            "iso-8601",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%SZ",
            "%m/%d/%Y",
        ],
    )

    class Meta:
        model = Sample
        fields = (
            "order",
            "species",
            "date",
            "pop_id",
            "type",
            "location",
            "quantity",
        )


class GenrequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genrequest
        fields = (
            "id",
            "project",
            "area",
        )


class AnalysisSerializer(serializers.ModelSerializer):
    species = SpeciesSerializer(many=True, read_only=True)
    sample_types = SampleTypeSerializer(many=True, read_only=True)
    genrequest = GenrequestSerializer()

    class Meta:
        model = AnalysisOrder
        fields = ("id", "genrequest", "species", "sample_types", "needs_guid")
