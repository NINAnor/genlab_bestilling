from dal import autocomplete
from django.db import models
from django.http import HttpRequest, JsonResponse

from .models import (
    AnalysisOrder,
    AnalysisPlate,
    Area,
    EquipmentOrder,
    ExtractionOrder,
    ExtractionPlate,
    Genrequest,
    IsolationMethod,
    Location,
    Marker,
    Order,
    Sample,
    SampleMarkerAnalysis,
    SampleType,
    Species,
)


class AreaAutocomplete(autocomplete.Select2QuerySetView):
    model = Area


class StatusAutocomplete(autocomplete.Select2QuerySetView):
    class Params:
        q = "q"

    def get(self, request: "HttpRequest", *args, **kwargs) -> JsonResponse:
        term = request.GET.get(self.Params.q, "").lower()
        results = [
            {"id": choice[0], "text": choice[1]}
            for choice in Order.OrderStatus.choices
            if term in choice[1].lower()
        ]
        return JsonResponse({"results": results})


class SpeciesAutocomplete(autocomplete.Select2QuerySetView):
    model = Species


class SampleTypeAutocomplete(autocomplete.Select2QuerySetView):
    model = SampleType


class MarkerAutocomplete(autocomplete.Select2QuerySetView):
    model = Marker


class GenrequestAutocomplete(autocomplete.Select2QuerySetView):
    model = Genrequest


class LocationAutocomplete(autocomplete.Select2QuerySetView):
    model = Location

    def get_queryset(self) -> models.QuerySet:
        qs = Location.objects.all()
        if self.q:
            qs = qs.filter(
                models.Q(name__icontains=self.q)
                | models.Q(river_id__icontains=self.q)
                | models.Q(code__icontains=self.q)
            )
        return qs


class OrderAutocomplete(autocomplete.Select2QuerySetView):
    model = Order


class EquipmentAutocomplete(autocomplete.Select2QuerySetView):
    model = EquipmentOrder


class AnalysisOrderAutocomplete(autocomplete.Select2QuerySetView):
    model = AnalysisOrder


class ExtractionOrderAutocomplete(autocomplete.Select2QuerySetView):
    model = ExtractionOrder


class IsolationMethodAutocomplete(autocomplete.Select2QuerySetView):
    model = IsolationMethod


class AnalysisMarkerAutocomplete(autocomplete.Select2QuerySetView):
    model = Marker


class ExtractionPlateAutocomplete(autocomplete.Select2QuerySetView):
    model = ExtractionPlate

    def get_queryset(self) -> models.QuerySet:
        qs = super().get_queryset()
        if self.q:
            qs = qs.filter(qiagen__icontains=self.q)
        return qs


class AnalysisPlateAutocomplete(autocomplete.Select2QuerySetView):
    model = AnalysisPlate

    def get_queryset(self) -> models.QuerySet:
        qs = super().get_queryset()
        if self.q:
            qs = qs.filter(
                models.Q(id__istartswith=self.q) | models.Q(name__icontains=self.q)
            )
        return qs


class AvailableSampleAutocomplete(autocomplete.Select2QuerySetView):
    model = Sample

    def get_queryset(self) -> models.QuerySet:
        # Only show samples that are isolated, not invalid, and not already positioned
        qs = Sample.objects.filter(
            genlab_id__isnull=False,  # Has genlab ID
            is_isolated=True,  # Is isolated
            is_invalid=False,  # Not invalid
            position__isnull=True,  # Not already positioned
        ).select_related("species", "type", "order")

        if self.q:
            qs = qs.filter(
                models.Q(genlab_id__icontains=self.q) | models.Q(name__icontains=self.q)
            )

        return qs.order_by("genlab_id")[:50]  # Limit results

    def get_result_label(self, item: Sample) -> str:
        """Customize how samples appear in the dropdown."""
        species_name = item.species.name if item.species else "Unknown"
        return f"{item.genlab_id} - {item.name} ({species_name})"


class AvailableSampleMarkerAutocomplete(autocomplete.Select2QuerySetView):
    model = SampleMarkerAnalysis

    def get_queryset(self) -> models.QuerySet:
        # Only show sample markers where the sample has a position
        qs = SampleMarkerAnalysis.objects.filter(
            sample__position__isnull=False,
            is_invalid=False,
        ).select_related("sample", "marker", "order")

        if self.q:
            qs = qs.filter(
                models.Q(sample__genlab_id__icontains=self.q)
                | models.Q(marker__name__icontains=self.q)
                | models.Q(id__icontains=self.q)
            )

        return qs.order_by("sample__genlab_id", "marker__name")[:50]  # Limit results

    def get_result_label(self, item: SampleMarkerAnalysis) -> str:
        """Customize how sample markers appear in the dropdown."""
        sample_id = item.sample.genlab_id if item.sample else "Unknown"
        marker_name = item.marker.name if item.marker else "Unknown"
        order_id = item.order.id if item.order else "No Order"
        return f"{sample_id} - {marker_name} - {order_id}"
