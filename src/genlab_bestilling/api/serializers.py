from rest_framework import serializers

from ..models import Sample


class OperationStatusSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField(allow_null=True)


class EnumSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class SampleSerializer(serializers.ModelSerializer):
    type = EnumSerializer()
    species = EnumSerializer()
    location = EnumSerializer(allow_null=True, required=False)

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
