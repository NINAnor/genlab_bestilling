import uuid

from genlab_bestilling.models import Sample, Species
from staff.serializers import SampleSerializer


def test_sample_serializer_includes_bird_id(extraction):
    species = Species.objects.filter(area__name="Fugl").first()
    assert species is not None

    sample = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=species,
        type=extraction.sample_types.first(),
        year=2024,
        name="1",
        genlab_id="G24ABC00123",
    )

    data = SampleSerializer(sample).data

    assert data["bird_id"] == "ABC123"
