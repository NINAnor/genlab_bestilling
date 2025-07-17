import itertools
import uuid

import pytest
from django.db import IntegrityError, transaction
from pytest_django.asserts import assertQuerySetEqual

from genlab_bestilling.models import (
    AnalysisOrder,
    ExtractionOrder,
    GIDSequence,
    Marker,
    Sample,
)


def test_analysis_populate_without_order(genlab_setup):
    ao = AnalysisOrder.objects.create(genrequest_id=1)
    ao.populate_from_order()
    assert not ao.sample_markers.exists()


def test_analysis_populate_with_order_no_markers(extraction):
    ao = AnalysisOrder.objects.create(genrequest_id=1, from_order=extraction)
    ao.populate_from_order()
    assert not ao.sample_markers.exists()


def test_analysis_populate_with_order_one_marker_one_species(extraction):
    ao = AnalysisOrder.objects.create(genrequest_id=1, from_order=extraction)
    m = Marker.objects.filter(name="Elvemusling A").first()
    ao.markers.add(m)
    ao.populate_from_order()
    assert ao.sample_markers.count() == 2


def test_analysis_populate_with_order_wrong_marker(extraction):
    ao = AnalysisOrder.objects.create(genrequest_id=1, from_order=extraction)
    m = Marker.objects.filter(name="Kjønnstest").first()
    ao.markers.add(m)
    ao.populate_from_order()
    assert not ao.sample_markers.exists()


def test_analysis_populate_with_order_multiple_marker_same_species(extraction):
    ao = AnalysisOrder.objects.create(genrequest_id=1, from_order=extraction)
    m = Marker.objects.filter(name__startswith="Salamander").all()
    ao.markers.add(*m)
    ao.populate_from_order()
    assert ao.sample_markers.count() == 6


def test_analysis_populate_with_order_all_markers(extraction):
    ao = AnalysisOrder.objects.create(genrequest_id=1, from_order=extraction)
    m = ao.genrequest.markers.all()
    ao.markers.add(*m)
    ao.populate_from_order()
    assert ao.sample_markers.count() == 6


def test_gid_sequence_for_species_year(extraction):
    extraction.confirm_order()
    assert GIDSequence.objects.exists() is False
    sample = extraction.samples.first()
    gid = GIDSequence.objects.get_sequence_for_species_year(
        year=extraction.confirmed_at.year, species=sample.species, lock=False
    )
    assert gid.id == f"G{extraction.confirmed_at.year % 100}{sample.species.code}"
    assert gid.last_value == 0


def test_gid_sequence_increment(extraction):
    """
    Test the increment of the sequence
    """
    extraction.confirm_order()
    assert GIDSequence.objects.exists() is False
    sample = extraction.samples.first()

    with transaction.atomic():
        gid = GIDSequence.objects.get_sequence_for_species_year(
            year=extraction.confirmed_at.year, species=sample.species
        )
        assert gid.id == f"G{extraction.confirmed_at.year % 100}{sample.species.code}"
        assert gid.last_value == 0
        assert (
            gid.next_value()
            == f"G{extraction.confirmed_at.year % 100}{sample.species.code}00001"
        )
        assert gid.last_value == 1


def test_gid_sequence_rollback(extraction):
    """
    Test the rollback of the sequence
    """
    extraction.confirm_order()
    assert GIDSequence.objects.exists() is False
    sample = extraction.samples.first()
    gid = GIDSequence.objects.get_sequence_for_species_year(
        year=extraction.confirmed_at.year, species=sample.species
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            gid = GIDSequence.objects.select_for_update().get(id=gid.id)
            assert (
                gid.id == f"G{extraction.confirmed_at.year % 100}{sample.species.code}"
            )
            assert gid.last_value == 0
            assert (
                gid.next_value()
                == f"G{extraction.confirmed_at.year % 100}{sample.species.code}00001"
            )
            assert gid.last_value == 1

            # Expect an error here
            GIDSequence.objects.create(
                id=gid.id,
                year=gid.year,
                species=gid.species,
            )

    gid.refresh_from_db()
    assert gid.last_value == 0


def test_sample_genlab_id_generation(extraction):
    """
    Test the generation of the id for a single sample
    """
    extraction.confirm_order()
    sample = extraction.samples.first()
    assert (
        sample.generate_genlab_id()
        == f"G{extraction.confirmed_at.year % 100}{sample.species.code}00001"
    )


def test_full_order_ids_generation(extraction):
    """
    Test that by default all the ids are generated
    """
    extraction.confirm_order()

    sample_ids = list(
        Sample.objects.filter(order_id=extraction.id).values_list(
            "id", flat=True
        )  # selected_samples is always a list
    )

    Sample.objects.generate_genlab_ids(
        extraction.id,
        selected_samples=[str(pk) for pk in sample_ids],
    )

    assertQuerySetEqual(
        Sample.objects.filter(genlab_id__isnull=False),
        Sample.objects.filter(order_id=extraction.id),
        ordered=False,
    )


def test_order_selected_ids_generation(extraction):
    """
    Test that is possible to generate only a subset of ids
    """
    extraction.confirm_order()

    Sample.objects.generate_genlab_ids(
        extraction.id,
        selected_samples=extraction.samples.all().values_list("id", flat=True)[
            : extraction.samples.count() - 1
        ],
    )

    assert (
        Sample.objects.filter(genlab_id__isnull=False).count() + 1
        == Sample.objects.all().count()
    )


def natural_sort_key(s):
    """Return a key that sorts numbers numerically and strings lexicographically"""
    try:
        return (0, int(s.name))
    except (ValueError, TypeError):
        return (1, str(s.name))


def test_ids_generation_with_only_numeric_names(genlab_setup):
    """
    Test that by default the ordering is done on the column name
    ordering first the integers, and then all the other rows alphabetically
    """
    extraction = ExtractionOrder.objects.create(
        genrequest_id=1,
        return_samples=False,
        pre_isolated=False,
    )
    extraction.species.add(*extraction.genrequest.species.all())
    extraction.sample_types.add(*extraction.genrequest.sample_types.all())

    combo = list(
        itertools.product(extraction.species.all(), extraction.sample_types.all())
    )
    year = 2020

    s1 = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=combo[0][0],
        type=combo[0][1],
        year=year,
        name=10,
    )

    s2 = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=combo[0][0],
        type=combo[0][1],
        year=year,
        name=1,
    )

    s3 = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=combo[0][0],
        type=combo[0][1],
        year=year,
        name="20b",
    )

    s4 = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=combo[0][0],
        type=combo[0][1],
        year=year,
        name="20a",
    )

    extraction.confirm_order()

    samples = [s1, s2, s3, s4]
    print(samples)
    samples.sort(key=natural_sort_key)
    print(samples)

    sample_ids = [str(s.id) for s in samples]
    print(sample_ids)

    Sample.objects.generate_genlab_ids(
        order_id=extraction.id,
        selected_samples=sample_ids,
    )

    gid = GIDSequence.objects.get_sequence_for_species_year(
        species=combo[0][0], year=extraction.confirmed_at.year, lock=False
    )

    s1.refresh_from_db()
    s2.refresh_from_db()
    s3.refresh_from_db()
    s4.refresh_from_db()

    assert s1.genlab_id == gid.id + "00002"
    assert s2.genlab_id == gid.id + "00001"
    assert s3.genlab_id == gid.id + "00004"
    assert s4.genlab_id == gid.id + "00003"


def test_ids_generation_order_by_pop_id(genlab_setup):
    """
    Test that ids are can be generated using a custom order based on different fields
    """
    extraction = ExtractionOrder.objects.create(
        genrequest_id=1,
        return_samples=False,
        pre_isolated=False,
    )
    extraction.species.add(*extraction.genrequest.species.all())
    extraction.sample_types.add(*extraction.genrequest.sample_types.all())

    combo = list(
        itertools.product(extraction.species.all(), extraction.sample_types.all())
    )
    year = 2020

    s1 = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=combo[0][0],
        type=combo[0][1],
        year=year,
        name=10,
        pop_id="z",
    )

    s2 = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=combo[0][0],
        type=combo[0][1],
        year=year,
        name=1,
        pop_id="c",
    )

    s3 = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=combo[0][0],
        type=combo[0][1],
        year=year,
        name="20b",
        pop_id="z",
    )

    s4 = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species=combo[0][0],
        type=combo[0][1],
        year=year,
        name="20a",
        pop_id="r",
    )

    extraction.confirm_order()

    samples = list(Sample.objects.filter(order_id=extraction.id))
    samples.sort(key=lambda s: (s.pop_id, str(s.name)))
    sample_ids = [str(s.id) for s in samples]

    Sample.objects.generate_genlab_ids(
        order_id=extraction.id,
        selected_samples=sample_ids,
    )

    gid = GIDSequence.objects.get_sequence_for_species_year(
        species=combo[0][0], year=extraction.confirmed_at.year, lock=False
    )

    s1.refresh_from_db()
    s2.refresh_from_db()
    s3.refresh_from_db()
    s4.refresh_from_db()

    assert s1.genlab_id == gid.id + "00003"
    assert s2.genlab_id == gid.id + "00001"
    assert s3.genlab_id == gid.id + "00004"
    assert s4.genlab_id == gid.id + "00002"
