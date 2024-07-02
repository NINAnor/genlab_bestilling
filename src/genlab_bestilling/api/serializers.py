from rest_framework import serializers

from ..models import Marker, Sample, SampleType, Species


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


class SampleSerializer(serializers.ModelSerializer):
    type = SampleTypeSerializer()
    species = SpeciesSerializer()
    location = EnumSerializer(allow_null=True, required=False)
    markers = MarkerSerializer(many=True)
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
            "id",
            "order",
            "guid",
            "species",
            "markers",
            "date",
            "notes",
            "pop_id",
            "location",
            "volume",
            "type",
        )


class SampleUpdateSerializer(serializers.ModelSerializer):
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
            "id",
            "order",
            "guid",
            "species",
            "markers",
            "date",
            "notes",
            "pop_id",
            "location",
            "volume",
            "type",
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
            "location",
            "quantity",
        )
