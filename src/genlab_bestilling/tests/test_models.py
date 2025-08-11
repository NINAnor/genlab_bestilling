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
    with pytest.raises(IntegrityError), transaction.atomic():
        gid = GIDSequence.objects.select_for_update().get(id=gid.id)
        assert gid.id == f"G{extraction.confirmed_at.year % 100}{sample.species.code}"
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


def test_must_be_in_transaction(extraction):
    """
    Test the generation of the id for a single sample without a transaction
    """
    with pytest.raises(AssertionError):
        extraction.confirm_order()
        sample = extraction.samples.first()
        assert (
            sample.generate_genlab_id()
            == f"G{extraction.confirmed_at.year % 100}{sample.species.code}00001"
        )


def test_sample_genlab_id_generation(extraction):
    """
    Test the generation of the id for a single sample
    """
    with transaction.atomic():
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
    with transaction.atomic():
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
    with transaction.atomic():
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
    with transaction.atomic():
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
        samples.sort(key=natural_sort_key)
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

        assert s1.genlab_id == gid.id + "00002"
        assert s2.genlab_id == gid.id + "00001"
        assert s3.genlab_id == gid.id + "00004"
        assert s4.genlab_id == gid.id + "00003"


def test_ids_generation_order_by_pop_id(genlab_setup):
    """
    Test that ids are can be generated using a custom order based on different fields
    """
    with transaction.atomic():
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


def test_get_sequence_for_replication_without_genlab_id(extraction):
    """
    Test that get_sequence_for_replication
    raises ValueError for sample without genlab_id
    """
    extraction.confirm_order()
    sample = extraction.samples.first()

    with pytest.raises(ValueError, match="Cannot replicate a sample without genlab id"):
        GIDSequence.objects.get_sequence_for_replication(sample=sample)


def test_get_sequence_for_replication_creates_new_sequence(extraction):
    """
    Test that get_sequence_for_replication
    creates a new sequence for sample with genlab_id
    """
    with transaction.atomic():
        extraction.confirm_order()
        sample = extraction.samples.first()
        sample.generate_genlab_id()

        sequence = GIDSequence.objects.get_sequence_for_replication(sample=sample)

        assert sequence.id == f"{sample.genlab_id}-"
        assert sequence.last_value == 1
        assert sequence.year == sample.order.confirmed_at.year
        assert sequence.species == sample.species
        assert sequence.sample == sample


def test_get_sequence_for_replication_returns_existing_sequence(extraction):
    """
    Test that get_sequence_for_replication returns existing sequence if already created
    """
    with transaction.atomic():
        extraction.confirm_order()
        sample = extraction.samples.first()
        sample.generate_genlab_id()

        # Create sequence first time
        sequence1 = GIDSequence.objects.get_sequence_for_replication(sample=sample)

        # Get sequence second time - should return same instance
        sequence2 = GIDSequence.objects.get_sequence_for_replication(sample=sample)

        assert sequence1.id == sequence2.id
        assert sequence1.pk == sequence2.pk


def test_get_sequence_for_replication_with_lock(extraction):
    """
    Test that get_sequence_for_replication works with lock=True
    """
    with transaction.atomic():
        extraction.confirm_order()
        sample = extraction.samples.first()
        sample.generate_genlab_id()

        sequence = GIDSequence.objects.get_sequence_for_replication(
            sample=sample, lock=True
        )

        assert sequence.id == f"{sample.genlab_id}-"
        assert sequence.sample == sample


def test_replicate_function_without_transaction(extraction):
    """
    Test that replicate function requires atomic transaction
    """
    extraction.confirm_order()
    sample = extraction.samples.first()

    with pytest.raises(AssertionError):
        sample.replicate(count=2)


def test_replicate_function_creates_replicas(extraction):
    """
    Test that replicate function creates specified number
    of replicas with proper genlab_ids
    """
    with transaction.atomic():
        extraction.confirm_order()
        samples = list(extraction.samples.all())
        sample = samples[0]  # Use first sample and check initial sequence state
        sample.generate_genlab_id()
        sample_genlab_id = sample.genlab_id
        original_sample_count = Sample.objects.count()

        # Get the replication sequence to check its initial state

        sequence = GIDSequence.objects.get_sequence_for_replication(sample=sample)
        initial_last_value = sequence.last_value

        # Call replicate to create 3 replicas
        sample.replicate(count=3)

        # Check that 3 new samples were created
        assert Sample.objects.count() == original_sample_count + 3

        # Check that all new samples have proper genlab_ids and parent relationship
        replica_samples = Sample.objects.filter(parent=sample)
        assert replica_samples.count() == 3

        # Check genlab_ids start from the correct sequence position
        # Note: replication sequences don't use zero padding
        for i, replica_sample in enumerate(replica_samples.order_by("id"), 1):
            expected_id = f"{sample_genlab_id}-{initial_last_value + i}"
            assert replica_sample.genlab_id == expected_id
            assert replica_sample.parent == sample
            assert replica_sample.species == sample.species
            assert replica_sample.order == sample.order


def test_replicate_function_without_genlab_id_fails(extraction):
    """
    Test that replicate function fails when sample doesn't have genlab_id
    """
    with transaction.atomic():
        extraction.confirm_order()
        sample = extraction.samples.first()

        # Sample doesn't have genlab_id yet
        assert sample.genlab_id is None

        with pytest.raises(
            ValueError, match="Cannot replicate a sample without genlab id"
        ):
            sample.replicate(count=2)


def test_replicate_function_multiple_calls(extraction):
    """
    Test that multiple calls to replicate function continue incrementing the sequence
    """
    with transaction.atomic():
        extraction.confirm_order()
        samples = list(extraction.samples.all())
        sample = samples[1] if len(samples) > 1 else samples[0]  # Use second sample
        sample.generate_genlab_id()
        sample_genlab_id = sample.genlab_id
        original_sample_count = Sample.objects.count()

        sequence = GIDSequence.objects.get_sequence_for_replication(sample=sample)
        initial_last_value = sequence.last_value

        # First call - create 2 replicas
        sample.replicate(count=2)
        assert Sample.objects.count() == original_sample_count + 2

        # Second call - create 1 more replica
        sample.replicate(count=1)
        assert Sample.objects.count() == original_sample_count + 3

        # Check that all replicas have proper sequential genlab_ids
        replica_samples = Sample.objects.filter(parent=sample).order_by("id")
        assert replica_samples.count() == 3

        expected_ids = [
            f"{sample_genlab_id}-{initial_last_value + i}" for i in range(1, 4)
        ]
        actual_ids = [replica.genlab_id for replica in replica_samples]
        assert actual_ids == expected_ids


def test_replicate_function_with_commit_false(extraction):
    """
    Test replicate function behavior with commit=False parameter
    """
    with transaction.atomic():
        extraction.confirm_order()
        samples = list(extraction.samples.all())
        sample = samples[-1]  # Use last sample to avoid conflicts
        sample.generate_genlab_id()
        original_sample_count = Sample.objects.count()

        # Call replicate with commit=False (though current implementation always saves)
        sample.replicate(count=2, commit=False)

        assert Sample.objects.count() == original_sample_count + 2
