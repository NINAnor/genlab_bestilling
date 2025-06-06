import uuid

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, mixins
from rest_framework_csv.renderers import CSVRenderer

from ..filters import (
    LocationFilter,
    MarkerFilter,
    SampleFilter,
    SampleMarkerOrderFilter,
    SampleTypeFilter,
    SpeciesFilter,
)
from ..models import (
    AnalysisType,
    ExtractionOrder,
    Location,
    Marker,
    Sample,
    SampleMarkerAnalysis,
    SampleType,
    Species,
)
from .serializers import (
    EnumSerializer,
    ExtractionSerializer,
    KoncivSerializer,
    LocationCreateSerializer,
    LocationSerializer,
    MarkerSerializer,
    OperationStatusSerializer,
    SampleBulkSerializer,
    SampleCSVSerializer,
    SampleMarkerAnalysisBulkDeleteSerializer,
    SampleMarkerAnalysisBulkSerializer,
    SampleMarkerAnalysisSerializer,
    SampleSerializer,
    SampleUpdateSerializer,
)


class IDCursorPagination(CursorPagination):
    ordering = "-id"
    page_size = 50


class AllowSampleDraft(BasePermission):
    """
    Prevent any UNSAFE method (POST, PUT, DELETE) on orders that are not draft
    """

    def has_object_permission(self, request, view, obj):
        if obj.order.status != ExtractionOrder.OrderStatus.DRAFT:
            return request.method in SAFE_METHODS
        return True


class SampleViewset(ModelViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    filterset_class = SampleFilter
    pagination_class = IDCursorPagination
    permission_classes = [AllowSampleDraft, IsAuthenticated]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "type",
                "species",
                "order",
                "order__genrequest",
                "order__genrequest__area",
                "location",
            )
            .order_by("id")
        )

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return SampleUpdateSerializer
        if self.action in ["csv"]:
            return SampleCSVSerializer
        return super().get_serializer_class()

    @action(
        methods=["GET"], url_path="csv", detail=False, renderer_classes=[CSVRenderer]
    )
    def csv(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            serializer.data,
            headers={"Content-Disposition": "attachment; filename=samples.csv"},
        )

    @extend_schema(
        request=SampleBulkSerializer, responses={200: OperationStatusSerializer}
    )
    @action(methods=["POST"], url_path="bulk", detail=False)
    def bulk_create(self, request):
        """
        Creata a multiple samples in bulk
        """
        serializer = SampleBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qty = serializer.validated_data.pop("quantity")
        lists = [
            "pop_id",
            "name",
            "guid",
        ]
        lists_data = {
            li: list(reversed(serializer.validated_data.pop(li)))
            for li in lists
            if li in serializer.validated_data
        }

        order = serializer.validated_data["order"]
        # TODO: raise validation issue if order is not "owned"
        # by a project the user is part of
        samples = []
        with transaction.atomic():
            for i in range(qty):
                extra = {}

                extra["guid"] = uuid.uuid4() if order.needs_guid else None

                for li in lists:
                    if li in lists_data:
                        try:
                            extra[li] = lists_data[li][i]
                        except IndexError:
                            pass

                samples.append(Sample(**extra, **serializer.validated_data))

            Sample.objects.bulk_create(samples, 50)

        return Response(data=OperationStatusSerializer({"success": True}).data)


class AllowOrderDraft(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.status != ExtractionOrder.OrderStatus.DRAFT:
            return request.method in SAFE_METHODS
        return True


class ExtractionOrderViewset(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    queryset = ExtractionOrder.objects.all()
    serializer_class = ExtractionSerializer

    def get_queryset(self):
        qs = super().get_queryset().filter_allowed(self.request.user)
        if self.request.method not in SAFE_METHODS:
            qs = qs.filter_in_draft()
        return qs

    @action(
        methods=["POST"],
        url_path="confirm",
        detail=True,
        permission_classes=[AllowOrderDraft],
    )
    def confirm_order(self, request, pk):
        obj = self.get_object()
        obj.confirm_order(persist=False)
        return Response(self.get_serializer(obj).data)

    @extend_schema(responses={200: OperationStatusSerializer})
    @action(
        methods=["POST"],
        url_path="delete-samples",
        detail=True,
        permission_classes=[AllowOrderDraft],
    )
    def bulk_delete(self, request, pk):
        obj = self.get_object()
        with transaction.atomic():
            obj.samples.all().delete()

        return Response(data=OperationStatusSerializer({"success": True}).data)


class SampleTypeViewset(mixins.ListModelMixin, GenericViewSet):
    queryset = SampleType.objects.all().order_by("name")
    serializer_class = KoncivSerializer
    filterset_class = SampleTypeFilter


class AnalysisTypeViewset(mixins.ListModelMixin, GenericViewSet):
    queryset = AnalysisType.objects.all().order_by("name")
    serializer_class = KoncivSerializer


class SpeciesViewset(mixins.ListModelMixin, GenericViewSet):
    queryset = Species.objects.all().order_by("name")
    serializer_class = EnumSerializer
    filterset_class = SpeciesFilter


class MarkerViewset(mixins.ListModelMixin, GenericViewSet):
    queryset = Marker.objects.all().order_by("name")
    serializer_class = MarkerSerializer
    filterset_class = MarkerFilter


class LocationViewset(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    queryset = Location.objects.all().order_by("name")
    serializer_class = LocationSerializer
    filterset_class = LocationFilter

    def get_serializer_class(self):
        if self.action == "create":
            return LocationCreateSerializer
        return super().get_serializer_class()


class SampleMarkerAnalysisViewset(mixins.ListModelMixin, GenericViewSet):
    queryset = SampleMarkerAnalysis.objects.all()
    serializer_class = SampleMarkerAnalysisSerializer
    filterset_class = SampleMarkerOrderFilter
    pagination_class = IDCursorPagination

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter_allowed(self.request.user)
            .select_related(
                "marker", "order", "sample", "sample__species", "sample__location"
            )
        )

    @extend_schema(
        request=SampleMarkerAnalysisBulkSerializer,
        responses={200: OperationStatusSerializer},
    )
    @action(methods=["POST"], url_path="bulk", detail=False)
    def bulk_create(self, request):
        serializer = SampleMarkerAnalysisBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        markers = serializer.validated_data.pop("markers")
        samples = serializer.validated_data.pop("samples")
        with transaction.atomic():
            for marker in markers:
                for sample in samples:
                    if (
                        not serializer.validated_data["order"]
                        .markers.filter(name=marker)
                        .exists()
                    ):
                        # skip if the marker of the sample is not in the analysis
                        continue

                    if not marker.species.filter(id=sample.species_id).exists():
                        # skip if the marker is not allowed for this species
                        continue

                    SampleMarkerAnalysis.objects.get_or_create(
                        marker=marker, sample=sample, **serializer.validated_data
                    )

        return Response(data=OperationStatusSerializer({"success": True}).data)

    @extend_schema(
        request=SampleMarkerAnalysisBulkDeleteSerializer,
        responses={200: OperationStatusSerializer},
    )
    @action(methods=["POST"], url_path="bulk-delete", detail=False)
    def bulk_delete(self, request):
        serializer = SampleMarkerAnalysisBulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            self.get_queryset().filter(
                id__in=serializer.validated_data.pop("ids")
            ).delete()

        return Response(data=OperationStatusSerializer({"success": True}).data)
