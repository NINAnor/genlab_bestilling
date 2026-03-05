from django.contrib import messages
from django.db import transaction
from django.db.models import Count, F, Prefetch, Q
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import CursorPagination, LimitOffsetPagination
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from capps.users.models import User
from genlab_bestilling.models import (
    AnalysisOrder,
    AnalysisPlate,
    ExtractionPlate,
    Order,
    PlatePosition,
    PositiveControl,
    Sample,
    SampleMarkerAnalysis,
)

from .filters import AnalysisPlateAPIFilter, SampleMarkerAnalysisAPIFilter
from .serializers import (
    AnalysisOrderListSerializer,
    AnalysisPlateListSerializer,
    OrderSampleMarkerSerializer,
    PlatePositionSerializer,
    PositiveControlSerializer,
)


class IsGenlabStaffOrSuperuser(BasePermission):
    """Allow access only to users in the 'genlab' group or superusers."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user.is_genlab_staff()


class OrderAPIView(APIView):
    permission_classes = [IsGenlabStaffOrSuperuser]

    class RequestJson:
        user_ids = "user_ids"

    def get_object(self) -> Order:
        return Order.objects.get(pk=self.kwargs["pk"])

    def get_genlab_staff(self) -> QuerySet[User]:
        return User.objects.filter(groups__name="genlab")

    def post(self, request: Request, *args, **kwargs) -> Response:
        order = self.get_object()

        if not order.is_seen:
            msg = "Order must be seen before assigning staff."

            messages.error(request, msg)
            return Response(
                status=400,
                data={"detail": msg},
            )

        try:
            users = self.get_genlab_staff().filter(
                id__in=request.data.get(self.RequestJson.user_ids, [])
            )
            order.responsible_staff.clear()
            order.responsible_staff.set(users)
            order.save()

            return Response(
                status=200,
            )
        except Exception:
            # TODO Report to Sentry
            return Response(
                status=500,
            )


class PlatePositionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing plate positions."""

    permission_classes = [IsGenlabStaffOrSuperuser]
    queryset = PlatePosition.objects.select_related(
        "plate",
        "sample_raw",
        "sample_raw__species",
        "sample_raw__type",
        "sample_raw__location",
        "sample_marker",
        "sample_marker__sample",
        "sample_marker__sample__species",
        "sample_marker__marker",
    ).all()
    serializer_class = PlatePositionSerializer
    filterset_fields = ["plate"]

    @action(detail=True, methods=["post"])
    def reserve(self, request: Request, pk: int | str) -> Response:
        """Reserve a plate position."""
        position = PlatePosition.objects.select_for_update().get(pk=pk)

        if position.is_full:
            return Response(
                {"error": "Cannot reserve an occupied position"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        position.is_reserved = True
        position.save(update_fields=["is_reserved"])

        serializer = self.get_serializer(position)
        return Response(
            {"message": "Position reserved successfully", "position": serializer.data}
        )

    @action(detail=True, methods=["post"])
    def unreserve(self, request: Request, pk: int | str) -> Response:
        """Remove reservation from a plate position."""
        position = PlatePosition.objects.select_for_update().get(pk=pk)

        position.is_reserved = False
        position.save(update_fields=["is_reserved"])

        serializer = self.get_serializer(position)
        return Response(
            {"message": "Position unreserved successfully", "position": serializer.data}
        )

    @action(detail=True, methods=["post"])
    def remove_sample(self, request: Request, pk: int | str) -> Response:
        """Remove sample from a plate position."""
        position = PlatePosition.objects.select_for_update().get(pk=pk)

        if not position.sample_raw:
            return Response(
                {"error": "No sample to remove"}, status=status.HTTP_400_BAD_REQUEST
            )

        position.sample_raw = None
        position.save(update_fields=["sample_raw"])

        serializer = self.get_serializer(position)
        return Response(
            {"message": "Sample removed successfully", "position": serializer.data}
        )

    @action(detail=True, methods=["post"])
    def remove_analysis(self, request: Request, pk: int | str) -> Response:
        """Remove analysis from a plate position."""
        position = PlatePosition.objects.select_for_update().get(pk=pk)

        if not position.sample_marker:
            return Response(
                {"error": "No analysis to remove"}, status=status.HTTP_400_BAD_REQUEST
            )

        position.sample_marker = None
        position.save(update_fields=["sample_marker"])

        serializer = self.get_serializer(position)
        return Response(
            {"message": "Analysis removed successfully", "position": serializer.data}
        )

    @action(detail=True, methods=["post"])
    def edit_notes(self, request: Request, pk: int | str) -> Response:
        """Edit notes for a plate position."""
        position = PlatePosition.objects.select_for_update().get(pk=pk)
        notes = request.data.get("notes", "")

        position.notes = notes
        position.save(update_fields=["notes"])

        serializer = self.get_serializer(position)
        return Response(
            {"message": "Notes updated successfully", "position": serializer.data}
        )

    @action(detail=True, methods=["post"], url_path="toggle-invalid")
    def toggle_invalid(self, request: Request, pk: int | str) -> Response:
        """Toggle the invalid status of a plate position."""
        position = PlatePosition.objects.select_for_update().get(pk=pk)

        position.is_invalid = not position.is_invalid
        position.save(update_fields=["is_invalid"])

        status_text = "invalid" if position.is_invalid else "valid"
        serializer = self.get_serializer(position)
        return Response(
            {
                "message": f"Position marked as {status_text}",
                "position": serializer.data,
            }
        )

    @action(detail=True, methods=["post"])
    def add_sample(self, request: Request, pk: int | str) -> Response:
        """Add a sample to a plate position."""
        with transaction.atomic():
            position = PlatePosition.objects.select_for_update().get(pk=pk)
            sample_id = request.data.get("sample_id")

            if not sample_id:
                return Response(
                    {"error": "Sample ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if position.sample_raw:
                return Response(
                    {"error": "Position already has a sample"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                sample = Sample.objects.select_for_update().get(
                    pk=sample_id,
                    genlab_id__isnull=False,
                    is_isolated=True,
                    is_invalid=False,
                )
            except Sample.DoesNotExist:
                return Response(
                    {"error": "Sample not found or not available"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Enforce extraction plate species / sample_type whitelists
            try:
                plate = ExtractionPlate.objects.get(pk=position.plate_id)
                plate.validate_sample(sample)
            except ExtractionPlate.DoesNotExist:
                pass  # Not an extraction plate, skip whitelist checks
            except ExtractionPlate.SampleNotAllowed as exc:
                return Response(
                    {"error": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            position.sample_raw = sample
            position.is_reserved = False  # Remove reservation when adding sample
            position.save(update_fields=["sample_raw", "is_reserved"])

            serializer = self.get_serializer(position)
            return Response(
                {"message": "Sample added successfully", "position": serializer.data}
            )

    @action(detail=True, methods=["post"])
    def add_sample_marker(self, request: Request, pk: int | str) -> Response:
        """Add a sample marker to a plate position."""
        with transaction.atomic():
            position = PlatePosition.objects.select_for_update().get(pk=pk)
            sample_marker_id = request.data.get("sample_marker_id")

            if not sample_marker_id:
                return Response(
                    {"error": "Sample marker ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if position.sample_marker:
                return Response(
                    {"error": "Position already has a sample marker"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                sample_marker = SampleMarkerAnalysis.objects.select_for_update().get(
                    pk=sample_marker_id,
                )
            except SampleMarkerAnalysis.DoesNotExist:
                return Response(
                    {"error": "Sample marker not found or not available"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            position.sample_marker = sample_marker
            position.is_reserved = False  # Remove reservation when adding sample marker

            # Enforce analysis plate marker whitelist
            try:
                plate = AnalysisPlate.objects.get(pk=position.plate_id)
                plate.validate_sample_marker(sample_marker)
            except AnalysisPlate.DoesNotExist:
                pass  # Not an analysis plate, skip whitelist checks
            except AnalysisPlate.SampleMarkerNotAllowed as exc:
                return Response(
                    {"error": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            position.save(update_fields=["sample_marker", "is_reserved"])

            serializer = self.get_serializer(position)
            return Response(
                {
                    "message": "Sample marker added successfully",
                    "position": serializer.data,
                }
            )

    @action(detail=True, methods=["post"])
    def move_to(self, request: Request, pk: int | str) -> Response:
        """Move sample marker from this position to a target position."""
        target_position_index = request.data.get("target_position")

        if target_position_index is None:
            return Response(
                {"error": "Target position index is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            source = PlatePosition.objects.select_for_update().get(pk=pk)

            try:
                target = source.move_sample_marker_to(target_position_index)
            except PlatePosition.NoSampleMarkerToMove as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except PlatePosition.TargetPositionNotFound as e:
                return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
            except PlatePosition.TargetPositionNotEmpty as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {
                    "message": "Sample marker moved successfully",
                    "source": self.get_serializer(source).data,
                    "target": self.get_serializer(target).data,
                }
            )

    @action(detail=True, methods=["post"])
    def set_positive_control(self, request: Request, pk: int | str) -> Response:
        """Set positive control on a reserved position."""
        positive_control_id = request.data.get("positive_control_id")

        with transaction.atomic():
            position = PlatePosition.objects.select_for_update().get(pk=pk)

            if not position.is_reserved:
                return Response(
                    {"error": "Position must be reserved to set a positive control"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if positive_control_id:
                try:
                    positive_control = PositiveControl.objects.get(
                        pk=positive_control_id
                    )
                except PositiveControl.DoesNotExist:
                    return Response(
                        {"error": "Positive control not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                position.positive_control = positive_control
            else:
                position.positive_control = None

            position.save(update_fields=["positive_control"])

            serializer = self.get_serializer(position)
            return Response(
                {
                    "message": "Positive control updated successfully",
                    "position": serializer.data,
                }
            )


class PositiveControlViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing positive control options."""

    permission_classes = [IsGenlabStaffOrSuperuser]
    queryset = PositiveControl.objects.all()
    serializer_class = PositiveControlSerializer


class AnalysisOrderSampleMarkerViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff API for listing sample markers of an analysis order."""

    permission_classes = [IsGenlabStaffOrSuperuser]
    serializer_class = OrderSampleMarkerSerializer
    filterset_class = SampleMarkerAnalysisAPIFilter

    def get_queryset(self) -> QuerySet[SampleMarkerAnalysis]:
        order = get_object_or_404(AnalysisOrder, pk=self.kwargs["order_pk"])
        # Prefetch positions with plate fields annotated to avoid N+1 from polymorphic
        positions_prefetch = Prefetch(
            "positions",
            queryset=PlatePosition.objects.annotate(
                plate_analysis_date=F("plate__analysisplate__analysis_date"),
                plate_result_file=F("plate__analysisplate__result_file"),
                plate_analysis_number=F("plate__analysisplate__analysis_number"),
            ),
        )
        return (
            SampleMarkerAnalysis.objects.filter(order=order)
            .select_related(
                "sample",
                "sample__species",
                "sample__type",
                "sample__position",
                "marker",
            )
            .prefetch_related(
                "sample__isolation_method",
                positions_prefetch,
            )
            # Annotate extraction plate qiagen_id to avoid polymorphic lookup
            .annotate(
                _sample_extraction_qiagen_id=F(
                    "sample__position__plate__extractionplate__qiagen_id"
                ),
            )
            .order_by("sample__genlab_id", "marker__name")
        )


class SampleMarkerCursorPagination(CursorPagination):
    """Cursor pagination for sample markers with dynamic ordering.

    Supports ordering by: genlab_id, marker, species, sample_position.
    Always appends 'id' to ensure stable cursor pagination.
    Use '-field' prefix for descending order.
    """

    page_size = 10

    # Map frontend field names to annotated flat field names
    FIELD_MAPPING: dict[str, str] = {
        "genlab_id": "_sort_genlab_id",
        "marker": "_sort_marker",
        "species": "_sort_species",
        "sample_position": "_sort_position",
    }

    def get_ordering(
        self, request: Request, queryset: QuerySet, view: viewsets.ViewSet
    ) -> tuple[str, ...]:
        """Get ordering from request param, map to annotated fields, append 'id'."""
        ordering_param = request.query_params.get("ordering", "")

        if not ordering_param:
            return ("id",)

        ordering_fields: list[str] = []
        for raw_field in ordering_param.split(","):
            field = raw_field.strip()
            if not field:
                continue

            # Handle descending order prefix
            descending = field.startswith("-")
            field_name = field.lstrip("-")

            # Map to annotated field if valid
            annotated_field = self.FIELD_MAPPING.get(field_name)
            if annotated_field:
                if descending:
                    ordering_fields.append(f"-{annotated_field}")
                else:
                    ordering_fields.append(annotated_field)

        # Always append 'id' for stable cursor pagination
        if ordering_fields:
            ordering_fields.append("id")
            return tuple(ordering_fields)

        return ("id",)


class SampleMarkerViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff API for listing all sample markers with optional filters."""

    permission_classes = [IsGenlabStaffOrSuperuser]
    serializer_class = OrderSampleMarkerSerializer
    filterset_class = SampleMarkerAnalysisAPIFilter
    pagination_class = SampleMarkerCursorPagination

    def get_queryset(self) -> QuerySet[SampleMarkerAnalysis]:
        # Prefetch positions with plate fields annotated to avoid N+1 from polymorphic
        positions_prefetch = Prefetch(
            "positions",
            queryset=PlatePosition.objects.annotate(
                plate_analysis_date=F("plate__analysisplate__analysis_date"),
                plate_result_file=F("plate__analysisplate__result_file"),
                plate_analysis_number=F("plate__analysisplate__analysis_number"),
            ),
        )
        return (
            SampleMarkerAnalysis.objects.all()
            .select_related(
                "sample",
                "sample__species",
                "sample__type",
                "sample__position",
                "marker",
                "order",
            )
            .prefetch_related(
                "sample__isolation_method",
                positions_prefetch,
            )
            # Annotate flat fields for cursor pagination and to avoid polymorphic N+1
            .annotate(
                _sort_genlab_id=F("sample__genlab_id"),
                _sort_marker=F("marker__name"),
                _sort_species=F("sample__species__name"),
                _sort_position=F("sample__position__position"),
                # Annotate extraction plate qiagen_id to avoid polymorphic lookup
                _sample_extraction_qiagen_id=F(
                    "sample__position__plate__extractionplate__qiagen_id"
                ),
            )
        )


class AnalysisOrdersListViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff API for listing analysis orders (for filter dropdowns)."""

    permission_classes = [IsGenlabStaffOrSuperuser]
    serializer_class = AnalysisOrderListSerializer
    queryset = AnalysisOrder.objects.all().order_by("-id")
    pagination_class = LimitOffsetPagination
    filter_backends = [SearchFilter]
    search_fields = ["=id", "name", "genrequest__name"]


class AnalysisPlatesViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """List all analysis plates."""

    permission_classes = [IsGenlabStaffOrSuperuser]
    queryset = (
        AnalysisPlate.objects.all()
        .select_related("analysis_type")
        .prefetch_related("markers", "positions")
        .annotate(
            available_positions_count=Count(
                "positions", filter=Q(positions__is_full=False)
            ),
            filled_positions_count=Count(
                "positions", filter=Q(positions__is_full=True)
            ),
            invalid_positions_count=Count(
                "positions", filter=Q(positions__is_invalid=True)
            ),
        )
        .order_by("-created_at")
    )
    serializer_class = AnalysisPlateListSerializer
    filterset_class = AnalysisPlateAPIFilter
    pagination_class = LimitOffsetPagination

    @action(detail=True, methods=["post"], url_path="add-sample-markers")
    def add_sample_markers(self, request: Request, pk: str) -> Response:
        """Add sample markers to plate, filling from first available position."""
        sample_marker_ids = request.data.get("sample_marker_ids", [])

        if not sample_marker_ids:
            return Response(
                {"error": "No sample markers provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            plate = self.get_object()
            try:
                added = plate.add_sample_markers(sample_marker_ids)
            except AnalysisPlate.NotEnoughPositions as exc:
                return Response(
                    {"error": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except AnalysisPlate.SampleMarkerNotFound as exc:
                return Response(
                    {"error": str(exc)},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except AnalysisPlate.SampleMarkerNotAllowed as exc:
                return Response(
                    {"error": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "message": f"Added {len(added)} sample markers to plate",
                    "added": added,
                },
                status=status.HTTP_200_OK,
            )

    @action(detail=True, methods=["post"], url_path="set-analysis-date")
    def set_analysis_date(self, request: Request, pk: str) -> Response:
        """Set the analysis date for a plate."""
        analysis_date = request.data.get("analysis_date")

        plate = self.get_object()
        plate.analysis_date = analysis_date
        plate.save(update_fields=["analysis_date"])

        return Response(
            {
                "message": "Analysis date updated",
                "analysis_date": plate.analysis_date,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="set-name")
    def set_name(self, request: Request, pk: str) -> Response:
        """Set the name for a plate."""
        name = request.data.get("name")
        # Strip whitespace and convert empty string to None
        if name:
            name = name.strip()
        name = name or None

        plate = self.get_object()
        plate.name = name
        plate.save(update_fields=["name"])

        return Response(
            {
                "message": "Plate name updated",
                "name": plate.name,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="upload-result-file")
    def upload_result_file(self, request: Request, pk: str) -> Response:
        """Upload a result file for a plate."""
        result_file = request.FILES.get("result_file")

        if not result_file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        plate = self.get_object()
        plate.result_file = result_file
        plate.save(update_fields=["result_file"])

        return Response(
            {
                "message": "Result file uploaded",
                "result_file": plate.result_file.url if plate.result_file else None,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="delete-result-file")
    def delete_result_file(self, request: Request, pk: str) -> Response:
        """Delete the result file for a plate."""
        plate = self.get_object()
        if plate.result_file:
            plate.result_file.delete(save=False)
        plate.result_file = None
        plate.save(update_fields=["result_file"])

        return Response(
            {"message": "Result file deleted"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="clone")
    def clone(self, request: Request, pk: str) -> Response:
        """Clone a plate with same name, markers, and filled positions."""
        source_plate = self.get_object()
        new_plate = source_plate.clone()

        # Return the new plate using the serializer
        serializer = self.get_serializer(new_plate)
        return Response(
            {
                "message": f"Cloned plate {source_plate} to {new_plate}",
                "plate": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
