from rest_framework import serializers

from genlab_bestilling.models import (
    AnalysisPlate,
    ExtractionPlate,
    PlatePosition,
    PositiveControl,
    Sample,
    SampleMarkerAnalysis,
)


class PositiveControlSerializer(serializers.ModelSerializer):
    """Serializer for positive control options."""

    class Meta:
        model = PositiveControl
        fields = ("id", "name", "description")


class SampleSerializer(serializers.ModelSerializer):
    """Serializer for sample information in plate positions."""

    species_name = serializers.CharField(
        source="species.name", read_only=True, default=None
    )
    species_code = serializers.CharField(
        source="species.code", read_only=True, default=None
    )
    type_name = serializers.CharField(source="type.name", read_only=True, default=None)
    location_name = serializers.SerializerMethodField()
    location_river_id = serializers.CharField(
        source="location.river_id", read_only=True, default=None
    )
    location_code = serializers.CharField(
        source="location.code", read_only=True, default=None
    )
    order_id = serializers.PrimaryKeyRelatedField(source="order", read_only=True)

    class Meta:
        model = Sample
        fields = (
            "id",
            "genlab_id",
            "name",
            "species",
            "species_name",
            "species_code",
            "type",
            "type_name",
            "year",
            "pop_id",
            "location",
            "location_name",
            "location_river_id",
            "location_code",
            "order_id",
        )

    def get_location_name(self, obj: Sample) -> str | None:
        return str(obj.location) if obj.location else None


class SampleMarkerSerializer(serializers.ModelSerializer):
    """Serializer for sample marker analysis information in plate positions."""

    sample_genlab_id = serializers.CharField(
        source="sample.genlab_id", read_only=True, default=None
    )
    sample_name = serializers.CharField(
        source="sample.name", read_only=True, default=None
    )
    sample_species_name = serializers.CharField(
        source="sample.species.name", read_only=True, default=None
    )
    marker_name = serializers.CharField(
        source="marker.name", read_only=True, default=None
    )
    order_id = serializers.PrimaryKeyRelatedField(source="order", read_only=True)

    class Meta:
        model = SampleMarkerAnalysis
        fields = (
            "id",
            "sample",
            "sample_genlab_id",
            "sample_name",
            "sample_species_name",
            "marker",
            "marker_name",
            "order_id",
        )


class PlatePositionSerializer(serializers.ModelSerializer):
    """Serializer for plate position information and actions."""

    coordinate = serializers.SerializerMethodField()
    sample_raw = SampleSerializer(read_only=True)
    sample_marker = SampleMarkerSerializer(read_only=True)
    possible_actions = serializers.SerializerMethodField()
    filled_at = serializers.DateTimeField(format="%d/%m/%Y", read_only=True)
    positive_control_name = serializers.CharField(
        source="positive_control.name", read_only=True, allow_null=True
    )

    class Meta:
        model = PlatePosition
        fields = (
            "id",
            "position",
            "coordinate",
            "is_full",
            "is_reserved",
            "positive_control",
            "positive_control_name",
            "filled_at",
            "sample_raw",
            "sample_marker",
            "notes",
            "possible_actions",
        )

    def get_coordinate(self, obj: PlatePosition) -> str:
        return obj.position_to_coordinates()

    def get_possible_actions(self, obj: PlatePosition) -> list[dict]:
        """Return possible actions for this position based on state and plate type."""
        actions = []

        plate = obj.plate.get_real_instance()

        # Determine plate type
        is_extraction_plate = isinstance(plate, ExtractionPlate)
        is_analysis_plate = isinstance(plate, AnalysisPlate)

        # Check specific content first, then reservation status
        if obj.sample_raw:
            actions.extend(
                [
                    {
                        "action": "remove_sample",
                        "label": "Remove Sample",
                        "type": "danger",
                    },
                    {
                        "action": "view_sample",
                        "label": "View Sample Details",
                        "type": "info",
                    },
                ]
            )
        elif obj.sample_marker:
            actions.extend(
                [
                    {
                        "action": "remove_analysis",
                        "label": "Remove Sample Marker",
                        "type": "danger",
                    },
                    {
                        "action": "view_analysis",
                        "label": "View Sample Marker Details",
                        "type": "info",
                    },
                ]
            )
        elif obj.is_reserved:
            # Position is reserved but empty
            actions.append(
                {
                    "action": "unreserve",
                    "label": "Remove Reservation",
                    "type": "warning",
                }
            )
        else:
            # Position is completely empty
            actions.append(
                {
                    "action": "reserve",
                    "label": "Reserve Position",
                    "type": "warning",
                }
            )

            # Add different actions based on plate type
            if is_extraction_plate:
                actions.append(
                    {"action": "add_sample", "label": "Add Sample", "type": "success"}
                )
            elif is_analysis_plate:
                actions.append(
                    {
                        "action": "add_sample_marker",
                        "label": "Add Sample Marker",
                        "type": "success",
                    }
                )

        # Always allow editing notes
        actions.append(
            {"action": "edit_notes", "label": "Edit Notes", "type": "secondary"}
        )

        return actions


class PlatePositionActionSerializer(serializers.Serializer):
    """Serializer for plate position actions."""

    action = serializers.ChoiceField(
        choices=[
            "reserve",
            "unreserve",
            "remove_sample",
            "remove_analysis",
            "edit_notes",
        ]
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class OrderSampleMarkerSerializer(serializers.ModelSerializer):
    """Serializer for managing sample markers within an analysis order."""

    sample_genlab_id = serializers.CharField(
        source="sample.genlab_id", read_only=True, default=None
    )
    sample_name = serializers.CharField(
        source="sample.name", read_only=True, default=None
    )
    sample_species_name = serializers.CharField(
        source="sample.species.name", read_only=True, default=None
    )
    sample_species_id = serializers.PrimaryKeyRelatedField(
        source="sample.species", read_only=True
    )
    sample_type_name = serializers.CharField(
        source="sample.type.name", read_only=True, default=None
    )
    sample_type_id = serializers.PrimaryKeyRelatedField(
        source="sample.type", read_only=True
    )
    marker_name = serializers.CharField(
        source="marker.name", read_only=True, default=None
    )
    sample_isolation_methods = serializers.SerializerMethodField()
    sample_position = serializers.SerializerMethodField()
    sample_position_index = serializers.IntegerField(
        source="sample.position.position", read_only=True, default=None
    )
    analysis_position = serializers.SerializerMethodField()

    class Meta:
        model = SampleMarkerAnalysis
        fields = (
            "id",
            "sample",
            "sample_genlab_id",
            "sample_name",
            "sample_species_id",
            "sample_species_name",
            "sample_type_id",
            "sample_type_name",
            "sample_isolation_methods",
            "marker",
            "marker_name",
            "has_pcr",
            "is_analysed",
            "is_outputted",
            "is_invalid",
            "sample_position",
            "sample_position_index",
            "analysis_position",
        )

    def get_sample_isolation_methods(self, obj: SampleMarkerAnalysis) -> list[dict]:
        return [
            {"id": im.id, "name": im.name} for im in obj.sample.isolation_method.all()
        ]

    def get_sample_position(self, obj: SampleMarkerAnalysis) -> str | None:
        """Return the sample's extraction plate position (e.g., 'PlateName@A1')."""
        position = getattr(obj.sample, "position", None)
        if position:
            return str(position)
        return None

    def get_analysis_position(self, obj: SampleMarkerAnalysis) -> str | None:
        """Return all analysis plate positions (e.g., '#A123@A1, #A123@B2')."""
        # Use prefetched positions if available
        positions = getattr(obj, "positions", None)
        if positions is not None:
            pos_list = [str(pos) for pos in positions.all()]
            if pos_list:
                return ", ".join(pos_list)
        return None


class AnalysisPlateListSerializer(serializers.ModelSerializer):
    """Simple serializer for listing analysis plates (for plate selection)."""

    label = serializers.SerializerMethodField()
    available_positions = serializers.SerializerMethodField()

    class Meta:
        model = AnalysisPlate
        fields = (
            "id",
            "name",
            "label",
            "available_positions",
            "created_at",
        )
        extra_kwargs = {
            "name": {"required": False, "allow_blank": True},
        }

    def validate_name(self, value: str | None) -> str | None:
        """Strip whitespace and convert empty string to None."""
        if value:
            value = value.strip()
        return value or None

    def get_label(self, obj: AnalysisPlate) -> str:
        return str(obj)

    def get_available_positions(self, obj: AnalysisPlate) -> int:
        return obj.positions.filter(is_full=False).count()
