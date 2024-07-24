import uuid

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, mixins

from ..filters import (
    LocationFilter,
    MarkerFilter,
    SampleFilter,
    SampleTypeFilter,
    SpeciesFilter,
)
from ..models import Location, Marker, Sample, SampleType, Species
from .serializers import (
    EnumSerializer,
    LocationCreateSerializer,
    LocationSerializer,
    MarkerSerializer,
    OperationStatusSerializer,
    SampleBulkSerializer,
    SampleSerializer,
    SampleUpdateSerializer,
)


class IDCursorPagination(CursorPagination):
    ordering = "-id"
    page_size = 50


class SampleViewset(ModelViewSet):
    queryset = (
        Sample.objects.all()
        .select_related(
            "type",
            "species",
            "order",
            "order__project",
            "order__project__area",
            "location",
        )
        .prefetch_related("markers")
        .order_by("id")
    )
    serializer_class = SampleSerializer
    filterset_class = SampleFilter
    pagination_class = IDCursorPagination

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return SampleUpdateSerializer
        return super().get_serializer_class()

    @extend_schema(
        request=SampleBulkSerializer, responses={200: OperationStatusSerializer}
    )
    @action(methods=["POST"], url_path="bulk", detail=False)
    def bulk_create(self, request):
        serializer = SampleBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qty = serializer.validated_data.pop("quantity")
        order = serializer.validated_data["order"]
        samples = []
        with transaction.atomic():
            for _ in range(qty):
                guid = uuid.uuid4() if order.needs_guid else None
                samples.append(Sample(guid=guid, **serializer.validated_data))

            Sample.objects.bulk_create(samples, 50)

        return Response(data=OperationStatusSerializer({"success": True}).data)


class SampleTypeViewset(mixins.ListModelMixin, GenericViewSet):
    queryset = SampleType.objects.all().order_by("name")
    serializer_class = EnumSerializer
    filterset_class = SampleTypeFilter


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
