from django.db import transaction

from genlab_bestilling.models import AnalysisOrder, SampleMarkerAnalysis
from staff.serializers import OrderSampleMarkerSerializer, SampleMarkerSerializer


def test_sample_marker_serializer_includes_bird_and_miljodna_id(extraction):
    extraction.confirm_order()
    sample = extraction.samples.first()
    with transaction.atomic():
        sample.generate_genlab_id()

    analysis = AnalysisOrder.objects.create(
        genrequest_id=1,
        status=AnalysisOrder.OrderStatus.DRAFT,
    )
    analysis.markers.add(*extraction.genrequest.markers.all())
    marker = extraction.genrequest.markers.first()

    sample_marker = SampleMarkerAnalysis.objects.create(
        sample=sample,
        order=analysis,
        marker=marker,
    )

    data = SampleMarkerSerializer(sample_marker).data

    assert data["sample_bird_id"] == sample.bird_id
    assert data["sample_miljodna_id"] == sample.miljodna_id


def test_order_sample_marker_serializer_includes_bird_and_miljodna_id(extraction):
    extraction.confirm_order()
    sample = extraction.samples.first()
    with transaction.atomic():
        sample.generate_genlab_id()

    analysis = AnalysisOrder.objects.create(
        genrequest_id=1,
        status=AnalysisOrder.OrderStatus.DRAFT,
    )
    analysis.markers.add(*extraction.genrequest.markers.all())
    marker = extraction.genrequest.markers.first()

    sample_marker = SampleMarkerAnalysis.objects.create(
        sample=sample,
        order=analysis,
        marker=marker,
    )

    data = OrderSampleMarkerSerializer(sample_marker).data

    assert data["sample_bird_id"] == sample.bird_id
    assert data["sample_miljodna_id"] == sample.miljodna_id
