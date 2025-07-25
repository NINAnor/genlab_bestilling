import contextlib
import re
import uuid
from typing import Any

from django.db import transaction
from django.db.models import Prefetch, QuerySet
from django.http import HttpResponse
from django.views import View
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import (  # type: ignore[attr-defined]
    GenericViewSet,
    ModelViewSet,
    mixins,
)
from rest_framework_csv.renderers import CSVRenderer

from genlab_bestilling.api.constants import (
    LABEL_CSV_FIELDS_BY_AREA,
    SAMPLE_CSV_FIELD_LABELS,
    SAMPLE_CSV_FIELDS_BY_AREA,
)

from ..filters import (
    LocationFilter,
    MarkerFilter,
    SampleFilter,
    SampleMarkerOrderFilter,
    SampleTypeFilter,
    SpeciesFilter,
)
from ..models import (
    AnalysisOrder,
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
    LabelCSVSerializer,
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

    def has_object_permission(self, request: Request, view: View, obj: Sample) -> bool:
        if obj.order.status != ExtractionOrder.OrderStatus.DRAFT:  # type: ignore[union-attr] # FIXME: order could be None.
            return request.method in SAFE_METHODS
        return True


class SampleCSVExportMixin:
    FIELD_LABELS = SAMPLE_CSV_FIELD_LABELS

    def get_area_name(self, queryset: QuerySet) -> str:
        return (
            queryset.values_list("order__genrequest__area__name", flat=True).first()
            or "default"
        )

    def get_csv_fields_and_labels(
        self,
        area_name: str,
        queryset: QuerySet,
        fields_by_area: dict[str, tuple[str, ...]],
    ) -> tuple[tuple[str, ...], list[str]]:
        get_fields = area_name
        if area_name == "Akvatisk":
            species = queryset.values_list("species__name", flat=True).distinct()
            if species.first() == "Elvemusling":
                get_fields = "Elvemusling"

        fields = fields_by_area.get(get_fields, fields_by_area["default"])
        labels = [self.FIELD_LABELS.get(f, f) for f in fields]
        return fields, labels

    def get_nested(self, obj: Any, dotted: str) -> Any:
        for part in dotted.split("."):
            obj = obj.get(part) if isinstance(obj, dict) else None
        return obj

    def build_csv_data(
        self,
        serialized_data: list[dict],
        fields: tuple[str, ...],
        area_name: str,
    ) -> list[dict[str, str]]:
        rows = []

        for item in serialized_data:
            row = {}

            for f in fields:
                if area_name in {"Akvatisk", "Elvemusling"} and f == "location.name":
                    full_location = self.get_nested(item, "location.name")
                    if (
                        full_location
                        and re.search(r"\d+", full_location)
                        and " " in full_location
                    ):
                        watercourse, location = full_location.split(" ", 1)
                    else:
                        watercourse, location = "", full_location or ""

                    row[self.FIELD_LABELS["watercourse_number"]] = watercourse
                    row[self.FIELD_LABELS["location.name"]] = location
                elif f != "watercourse_number":
                    value = self.get_nested(item, f)
                    label = self.FIELD_LABELS.get(f, f)
                    row[label] = (
                        ", ".join(value) if isinstance(value, list) else (value or "")
                    )

            rows.append(row)

        return rows

    def render_csv_response(
        self,
        queryset: QuerySet,
        serializer_class: type[BaseSerializer],
        fields_by_area: dict[str, tuple[str, ...]],
        filename: str = "export.csv",
    ) -> HttpResponse:
        area_name = self.get_area_name(queryset)
        serializer = serializer_class(queryset, many=True)
        fields, headers = self.get_csv_fields_and_labels(
            area_name, queryset, fields_by_area
        )
        data = self.build_csv_data(serializer.data, fields, area_name)

        csv_data = CSVRenderer().render(
            data, media_type="text/csv", renderer_context={"header": headers}
        )

        return HttpResponse(
            csv_data,
            content_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


class SampleViewset(ModelViewSet, SampleCSVExportMixin):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    filterset_class = SampleFilter
    pagination_class = IDCursorPagination
    permission_classes = [AllowSampleDraft, IsAuthenticated]

    def get_queryset(self) -> QuerySet:
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
            .prefetch_related(
                Prefetch(
                    "order__analysis_orders",
                    queryset=AnalysisOrder.objects.only("id"),
                )
            )
            .order_by("genlab_id", "type")
        )

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "csv":
            return SampleCSVSerializer
        if self.action == "labels-csv":
            return LabelCSVSerializer
        if self.action in ["update", "partial_update"]:
            return SampleUpdateSerializer
        return super().get_serializer_class()

    @action(
        methods=["GET"],
        url_path="csv",
        detail=False,
        renderer_classes=[CSVRenderer],
    )
    def csv(self, request: Request) -> HttpResponse:
        queryset = self.filter_queryset(self.get_queryset())
        return self.render_csv_response(
            queryset,
            serializer_class=SampleCSVSerializer,
            fields_by_area=SAMPLE_CSV_FIELDS_BY_AREA,
            filename="samples.csv",
        )

    @action(
        methods=["GET"],
        url_path="labels-csv",
        detail=False,
        renderer_classes=[CSVRenderer],
    )
    def labels_csv(self, request: Request) -> HttpResponse:
        queryset = self.filter_queryset(self.get_queryset())
        return self.render_csv_response(
            queryset,
            serializer_class=LabelCSVSerializer,
            fields_by_area=LABEL_CSV_FIELDS_BY_AREA,
            filename="sample_labels.csv",
        )

    @extend_schema(
        request=SampleBulkSerializer, responses={200: OperationStatusSerializer}
    )
    @action(methods=["POST"], url_path="bulk", detail=False)
    def bulk_create(self, request: Request) -> Response:
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
                        with contextlib.suppress(IndexError):
                            extra[li] = lists_data[li][i]

                samples.append(Sample(**extra, **serializer.validated_data))

            Sample.objects.bulk_create(samples, 50)

        return Response(data=OperationStatusSerializer({"success": True}).data)


class AllowOrderDraft(BasePermission):
    def has_object_permission(
        self,
        request: Request,
        view: View,
        obj: ExtractionOrder,
    ) -> bool:
        if obj.status != ExtractionOrder.OrderStatus.DRAFT:
            return request.method in SAFE_METHODS
        return True


class ExtractionOrderViewset(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet
):
    queryset = ExtractionOrder.objects.all()
    serializer_class = ExtractionSerializer

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset().filter_allowed(self.request.user)  # type: ignore[attr-defined]
        if self.request.method not in SAFE_METHODS:
            qs = qs.filter_in_draft()
        return qs

    @action(
        methods=["POST"],
        url_path="confirm",
        detail=True,
        permission_classes=[AllowOrderDraft],
    )
    def confirm_order(self, request: Request, pk: int | str) -> Response:
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
    def bulk_delete(self, request: Request, pk: int | str) -> Response:
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

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "create":
            return LocationCreateSerializer
        return super().get_serializer_class()


class SampleMarkerAnalysisViewset(mixins.ListModelMixin, GenericViewSet):
    queryset = SampleMarkerAnalysis.objects.all()
    serializer_class = SampleMarkerAnalysisSerializer
    filterset_class = SampleMarkerOrderFilter
    pagination_class = IDCursorPagination

    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .filter_allowed(self.request.user)  # type: ignore[attr-defined]
            .select_related(
                "marker", "order", "sample", "sample__species", "sample__location"
            )
        )

    @extend_schema(
        request=SampleMarkerAnalysisBulkSerializer,
        responses={200: OperationStatusSerializer},
    )
    @action(methods=["POST"], url_path="bulk", detail=False)
    def bulk_create(self, request: Request) -> Response:
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
    def bulk_delete(self, request: Request) -> Response:
        serializer = SampleMarkerAnalysisBulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            self.get_queryset().filter(
                id__in=serializer.validated_data.pop("ids")
            ).delete()

        return Response(data=OperationStatusSerializer({"success": True}).data)
