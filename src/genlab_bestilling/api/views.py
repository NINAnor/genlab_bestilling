from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, mixins

from ..filters import MarkerFilter, SampleFilter, SampleTypeFilter, SpeciesFilter
from ..models import Marker, Sample, SampleType, Species
from .serializers import (
    EnumSerializer,
    MarkerSerializer,
    OperationStatusSerializer,
    SampleBulkSerializer,
    SampleSerializer,
)


class IDCursorPagination(CursorPagination):
    ordering = "-id"
    page_size = 50


class SampleViewset(ModelViewSet):
    queryset = Sample.objects.all().select_related("type", "species").order_by("id")
    serializer_class = SampleSerializer
    filterset_class = SampleFilter
    pagination_class = IDCursorPagination

    @extend_schema(
        request=SampleBulkSerializer, responses={200: OperationStatusSerializer}
    )
    @action(methods=["POST"], url_path="bulk", detail=False)
    def bulk_create(self, request):
        serializer = SampleBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qty = serializer.validated_data.pop("quantity")
        samples = []
        with transaction.atomic():
            for _ in range(qty):
                samples.append(Sample(**serializer.validated_data))

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
