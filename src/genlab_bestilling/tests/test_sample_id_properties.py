import uuid

from genlab_bestilling.models import Sample, Species


def _sample_for_area(extraction, area_name: str) -> Sample:
    species = Species.objects.filter(area__name=area_name).first()
    assert species is not None, f"no species fixture for area {area_name!r}"
    return Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=species,
        type=extraction.sample_types.first(),
        year=2024,
        name="1",
        genlab_id="G24ABC00123",
        pop_id="MELFJ",
    )


def test_bird_id_is_generated_for_bird_species(extraction):
    sample = _sample_for_area(extraction, "Fugl")

    assert sample.bird_id == "ABC123"


def test_miljodna_id_is_generated_for_miljodna_species(extraction):
    sample = _sample_for_area(extraction, "MiljøDNA")

    assert sample.miljodna_id == "MELFJ_24_00123"
