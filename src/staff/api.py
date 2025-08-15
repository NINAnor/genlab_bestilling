from django.contrib import messages
from django.db import transaction
from django.db.models.query import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from capps.users.models import User
from genlab_bestilling.models import Order, PlatePosition, Sample, SampleMarkerAnalysis

from .serializers import PlatePositionSerializer


class OrderAPIView(APIView):
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

    queryset = PlatePosition.objects.select_related(
        "plate", "sample_raw", "sample_marker"
    ).all()
    serializer_class = PlatePositionSerializer

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
                    sample__position__isnull=False,
                )
            except SampleMarkerAnalysis.DoesNotExist:
                return Response(
                    {"error": "Sample marker not found or not available"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            position.sample_marker = sample_marker
            position.is_reserved = False  # Remove reservation when adding sample marker
            position.save(update_fields=["sample_marker", "is_reserved"])

            serializer = self.get_serializer(position)
            return Response(
                {
                    "message": "Sample marker added successfully",
                    "position": serializer.data,
                }
            )
