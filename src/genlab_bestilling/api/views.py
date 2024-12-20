import uuid

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, mixins

from ..filters import (
    LocationFilter,
    MarkerFilter,
    SampleFilter,
    SampleTypeFilter,
    SpeciesFilter,
)
from ..models import AnalysisOrder, Location, Marker, Sample, SampleType, Species
from .serializers import (
    AnalysisSerializer,
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


class AllowSampleDraft(BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.order.status != AnalysisOrder.OrderStatus.DRAFT:
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
            .filter_allowed(self.request.user)
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
        return super().get_serializer_class()

    @extend_schema(
        request=SampleBulkSerializer, responses={200: OperationStatusSerializer}
    )
    @action(methods=["POST"], url_path="bulk", detail=False)
    def bulk_create(self, request):
        serializer = SampleBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qty = serializer.validated_data.pop("quantity")
        lists = [
            "pop_id",
            "name",
            "guid",
        ]
        lists_data = {
            li: serializer.validated_data.pop(li)
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
        if obj.status != AnalysisOrder.OrderStatus.DRAFT:
            return request.method in SAFE_METHODS
        return True


class AnalysisOrderViewset(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    queryset = AnalysisOrder.objects.all()
    serializer_class = AnalysisSerializer

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
