import uuid

import pytest

from genlab_bestilling.models import ExtractionPlate, PlatePosition, Sample
from staff.filters import ExtractionPlateFilter


@pytest.mark.django_db
def test_extraction_plate_filter_by_year(extraction):
    """Filtering plates by Year only returns plates with a sample from
    that year, mirroring the Samples page's own year filter.
    """
    samples = list(Sample.objects.filter(order=extraction))
    assert samples, "fixture should create at least one sample"
    first_sample = samples[0]

    plate_2020 = ExtractionPlate.objects.create()
    position_2020 = plate_2020.positions.first()
    if position_2020 is None:
        position_2020 = PlatePosition.objects.create(plate=plate_2020, position=0)
    position_2020.sample_raw = first_sample
    position_2020.save(update_fields=["sample_raw"])

    other_sample = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=first_sample.species,
        type=first_sample.type,
        year=1999,
        name=uuid.uuid1(),
    )
    plate_1999 = ExtractionPlate.objects.create()
    position_1999 = plate_1999.positions.first()
    if position_1999 is None:
        position_1999 = PlatePosition.objects.create(plate=plate_1999, position=0)
    position_1999.sample_raw = other_sample
    position_1999.save(update_fields=["sample_raw"])

    filtered = ExtractionPlateFilter(
        data={"positions__sample_raw__year": first_sample.year},
        queryset=ExtractionPlate.objects.all(),
    ).qs

    assert list(filtered) == [plate_2020]


@pytest.mark.django_db
def test_extraction_plate_filter_year_field_present():
    filterset = ExtractionPlateFilter(data={}, queryset=ExtractionPlate.objects.all())
    assert "positions__sample_raw__year" in filterset.filters
    assert filterset.filters["positions__sample_raw__year"].label == "Year"
