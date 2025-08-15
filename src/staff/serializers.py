from rest_framework import serializers

from genlab_bestilling.models import (
    AnalysisPlate,
    ExtractionPlate,
    PlatePosition,
    Sample,
    SampleMarkerAnalysis,
)


class SampleSerializer(serializers.ModelSerializer):
    """Serializer for sample information in plate positions."""

    class Meta:
        model = Sample
        fields = ("id", "genlab_id", "name", "species", "type")


class SampleMarkerSerializer(serializers.ModelSerializer):
    """Serializer for sample marker analysis information in plate positions."""

    class Meta:
        model = SampleMarkerAnalysis
        fields = ("id", "sample", "marker")


class PlatePositionSerializer(serializers.ModelSerializer):
    """Serializer for plate position information and actions."""

    coordinate = serializers.SerializerMethodField()
    sample_raw = SampleSerializer(read_only=True)
    sample_marker = SampleMarkerSerializer(read_only=True)
    possible_actions = serializers.SerializerMethodField()

    class Meta:
        model = PlatePosition
        fields = (
            "id",
            "position",
            "coordinate",
            "is_full",
            "is_reserved",
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
