import itertools
import uuid

import pytest
from django.core import mail
from django.db import IntegrityError, transaction
from pytest_django.asserts import assertQuerySetEqual

from genlab_bestilling.models import (
    AnalysisOrder,
    AnalysisPlate,
    ExtractionOrder,
    ExtractionPlate,
    GIDSequence,
    Marker,
    PlatePosition,
    Sample,
    SampleMarkerAnalysis,
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

            # Check that replicated samples have reset fields
            assert not replica_sample.is_isolated
            assert not replica_sample.is_marked
            assert not replica_sample.is_plucked
            assert replica_sample.internal_note == ""
            assert replica_sample.isolation_method.count() == 0


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


@pytest.mark.django_db(transaction=True)
def test_extraction_order_completion_sends_email(extraction):
    """Test that email is sent when an extraction order is completed."""
    # Clear any existing emails
    mail.outbox = []

    # Set contact email for the order
    extraction.contact_email = "customer@example.com"
    extraction.save()

    # Complete the order
    extraction.to_completed()

    # Check that one email was sent
    assert len(mail.outbox) == 1

    # Check email details
    email = mail.outbox[0]
    assert email.subject == f"{extraction} - completed"
    assert email.body == "the order is completed"
    assert email.from_email == "noreply@genlab.com"
    assert email.to == ["customer@example.com"]


@pytest.mark.django_db(transaction=True)
def test_analysis_order_completion_sends_email(genlab_setup):
    """Test that email is sent when an analysis order is completed."""
    # Clear any existing emails
    mail.outbox = []

    # Create an analysis order
    analysis_order = AnalysisOrder.objects.create(
        genrequest_id=1, contact_email="researcher@example.com"
    )

    # Complete the order
    analysis_order.to_completed()

    # Check that one email was sent
    assert len(mail.outbox) == 1

    # Check email details
    email = mail.outbox[0]
    assert email.subject == f"{analysis_order} - completed"
    assert email.body == "the order is completed"
    assert email.from_email == "noreply@genlab.com"
    assert email.to == ["researcher@example.com"]


@pytest.mark.django_db(transaction=True)
def test_order_status_change_to_processing_no_email(extraction):
    """Test that no email is sent when order status changes to processing."""
    # Clear any existing emails
    mail.outbox = []

    # Set contact email
    extraction.contact_email = "customer@example.com"
    extraction.save()

    # Change to processing (should not send email)
    extraction.to_processing()

    # Check that no email was sent
    assert len(mail.outbox) == 0


def test_replicate_creates_analysis_markers_for_incomplete_orders(genlab_setup):
    """
    Test that replicate function creates SampleMarkerAnalysis objects
    for analysis orders that are not completed
    """
    with transaction.atomic():
        # Create extraction order and confirm it
        extraction = ExtractionOrder.objects.create(
            genrequest_id=1,
            return_samples=False,
            pre_isolated=False,
        )
        extraction.species.add(*extraction.genrequest.species.all())
        extraction.sample_types.add(*extraction.genrequest.sample_types.all())

        # Create a sample with specific attributes for testing
        combo = list(
            itertools.product(extraction.species.all(), extraction.sample_types.all())
        )
        sample = Sample.objects.create(
            order=extraction,
            guid=uuid.uuid4(),
            species=combo[0][0],
            type=combo[0][1],
            year=2023,
            name="test_sample",
        )

        extraction.confirm_order()
        sample.generate_genlab_id()

        # Create analysis orders with different statuses
        # 1. Draft analysis order
        draft_analysis = AnalysisOrder.objects.create(
            genrequest_id=1,
            status=AnalysisOrder.OrderStatus.DRAFT,
        )
        draft_analysis.markers.add(*extraction.genrequest.markers.all())

        # 2. Delivered analysis order
        delivered_analysis = AnalysisOrder.objects.create(
            genrequest_id=1,
            status=AnalysisOrder.OrderStatus.DELIVERED,
        )
        delivered_analysis.markers.add(*extraction.genrequest.markers.all())

        # 3. Processing analysis order
        processing_analysis = AnalysisOrder.objects.create(
            genrequest_id=1,
            status=AnalysisOrder.OrderStatus.PROCESSING,
        )
        processing_analysis.markers.add(*extraction.genrequest.markers.all())

        # 4. Completed analysis order
        completed_analysis = AnalysisOrder.objects.create(
            genrequest_id=1,
            status=AnalysisOrder.OrderStatus.COMPLETED,
        )
        completed_analysis.markers.add(*extraction.genrequest.markers.all())

        # Create SampleMarkerAnalysis objects for the original sample

        for marker in extraction.genrequest.markers.all():
            # Create for draft order
            SampleMarkerAnalysis.objects.create(
                sample=sample,
                order=draft_analysis,
                marker=marker,
            )
            # Create for delivered order
            SampleMarkerAnalysis.objects.create(
                sample=sample,
                order=delivered_analysis,
                marker=marker,
            )
            # Create for processing order
            SampleMarkerAnalysis.objects.create(
                sample=sample,
                order=processing_analysis,
                marker=marker,
            )
            # Don't create for completed order to simulate realistic scenario

        # Replicate the sample
        sample.replicate(count=2)

        # Check that new SampleMarkerAnalysis objects were created for replicas
        replica_samples = Sample.objects.filter(parent=sample)
        assert replica_samples.count() == 2

        # Count analysis markers for each status
        draft_markers_count = SampleMarkerAnalysis.objects.filter(
            sample__in=replica_samples, order=draft_analysis
        ).count()

        delivered_markers_count = SampleMarkerAnalysis.objects.filter(
            sample__in=replica_samples, order=delivered_analysis
        ).count()

        processing_markers_count = SampleMarkerAnalysis.objects.filter(
            sample__in=replica_samples, order=processing_analysis
        ).count()

        completed_markers_count = SampleMarkerAnalysis.objects.filter(
            sample__in=replica_samples, order=completed_analysis
        ).count()

        # Should have created markers for draft and delivered orders
        expected_markers_per_replica = extraction.genrequest.markers.count()
        assert draft_markers_count == 2 * expected_markers_per_replica
        assert delivered_markers_count == 2 * expected_markers_per_replica
        assert processing_markers_count == 0
        assert completed_markers_count == 0

        # Verify the created analysis markers have proper initial values
        for replica_sample in replica_samples:
            replica_markers = SampleMarkerAnalysis.objects.filter(sample=replica_sample)
            for marker in replica_markers:
                assert not marker.has_pcr
                assert not marker.is_analysed
                assert not marker.is_outputted
                assert not marker.is_invalid


@pytest.mark.django_db(transaction=True)
def test_order_completion_without_contact_email_fails(extraction):
    """Test that order completion without contact email fails gracefully."""
    # Clear any existing emails
    mail.outbox = []

    # Complete order without setting contact_email (should be None)
    extraction.to_completed()


@pytest.mark.django_db
def test_plate_get_grid_column_filling():
    """Test that get_grid method fills the matrix by columns instead of rows."""
    # Create an extraction plate for testing
    plate = ExtractionPlate.objects.create()

    # Create some plate positions to test with
    # Positions are filled by columns: A1=0, B1=1, C1=2..., H1=7, A2=8, B2=9...
    test_positions = [0, 1, 8, 9, 16, 17]  # A1, B1, A2, B2, A3, B3
    for pos in test_positions:
        PlatePosition.objects.create(plate=plate, position=pos)

    # Get the grid
    grid = plate.get_grid()

    # Verify grid structure
    assert len(grid) == 8  # 8 rows (A-H)
    assert len(grid[0]) == 12  # 12 columns (1-12)

    # Test specific positions and their coordinates
    # Row A (index 0)
    assert grid[0][0]["index"] == 0  # A1
    assert grid[0][0]["coordinate"] == "A1"
    assert grid[0][0]["position"] is not None

    assert grid[0][1]["index"] == 8  # A2
    assert grid[0][1]["coordinate"] == "A2"
    assert grid[0][1]["position"] is not None

    assert grid[0][2]["index"] == 16  # A3
    assert grid[0][2]["coordinate"] == "A3"
    assert grid[0][2]["position"] is not None

    # Row B (index 1)
    assert grid[1][0]["index"] == 1  # B1
    assert grid[1][0]["coordinate"] == "B1"
    assert grid[1][0]["position"] is not None

    assert grid[1][1]["index"] == 9  # B2
    assert grid[1][1]["coordinate"] == "B2"
    assert grid[1][1]["position"] is not None

    assert grid[1][2]["index"] == 17  # B3
    assert grid[1][2]["coordinate"] == "B3"
    assert grid[1][2]["position"] is not None

    # Test empty positions
    assert grid[0][3]["index"] == 24  # A4
    assert grid[0][3]["coordinate"] == "A4"
    assert grid[0][3]["position"] is None  # No position created for this

    # Test column filling pattern - verify that positions are filled column by column
    # Column 1: A1=0, B1=1, C1=2, ..., H1=7
    # Column 2: A2=8, B2=9, C2=10, ..., H2=15
    for row in range(8):  # Rows A-H
        for col in range(12):  # Columns 1-12
            expected_position = col * 8 + row
            assert grid[row][col]["index"] == expected_position
            assert grid[row][col]["coordinate"] == f"{'ABCDEFGH'[row]}{col + 1}"


@pytest.mark.django_db
def test_analysis_plate_get_grid():
    """Test that get_grid method works for AnalysisPlate as well."""
    # Create an analysis plate for testing
    plate = AnalysisPlate.objects.create()

    # Create a few plate positions
    test_positions = [0, 7, 8, 15]  # A1, H1, A2, H2
    for pos in test_positions:
        PlatePosition.objects.create(plate=plate, position=pos)

    # Get the grid
    grid = plate.get_grid()

    # Verify basic structure
    assert len(grid) == 8  # 8 rows
    assert len(grid[0]) == 12  # 12 columns

    # Test that positions are found correctly
    assert grid[0][0]["position"] is not None  # A1
    assert grid[7][0]["position"] is not None  # H1
    assert grid[0][1]["position"] is not None  # A2
    assert grid[7][1]["position"] is not None  # H2


@pytest.mark.django_db
def test_plate_position_to_coordinates():
    """Test position_to_coordinates method for column-wise filling."""
    # Create a plate for testing
    plate = ExtractionPlate.objects.create()

    # Test specific position mappings with column-wise filling
    test_cases = [
        # (position_index, expected_coordinate)
        (0, "A1"),  # First position: row A, column 1
        (1, "B1"),  # Second position: row B, column 1
        (2, "C1"),  # Third position: row C, column 1
        (7, "H1"),  # Eighth position: row H, column 1
        (8, "A2"),  # Ninth position: row A, column 2
        (9, "B2"),  # Tenth position: row B, column 2
        (15, "H2"),  # Sixteenth position: row H, column 2
        (16, "A3"),  # Seventeenth position: row A, column 3
        (24, "A4"),  # Twenty-fifth position: row A, column 4
        (31, "H4"),  # Thirty-second position: row H, column 4
        (88, "A12"),  # Position 88: row A, column 12
        (95, "H12"),  # Last position: row H, column 12
    ]

    for position_index, expected_coordinate in test_cases:
        # Create a plate position with the given index
        plate_position = PlatePosition.objects.create(
            plate=plate, position=position_index
        )

        # Test the position_to_coordinates method
        actual_coordinate = plate_position.position_to_coordinates()
        assert actual_coordinate == expected_coordinate, (
            f"Position {position_index} should map to {expected_coordinate}, "
            f"got {actual_coordinate}"
        )

        # Clean up for next iteration
        plate_position.delete()


@pytest.mark.django_db
def test_plate_position_str_method():
    """Test that PlatePosition.__str__ method uses position_to_coordinates correctly."""
    # Create a plate for testing
    plate = ExtractionPlate.objects.create()

    # Create a position
    position = PlatePosition.objects.create(plate=plate, position=0)  # A1

    # Test the __str__ method
    str_representation = str(position)
    assert "@A1" in str_representation
    assert str(plate) in str_representation


@pytest.mark.django_db
def test_position_to_coordinates_edge_cases():
    """Test edge cases for position_to_coordinates method."""
    # Create a plate for testing
    plate = ExtractionPlate.objects.create()

    # Test boundary positions
    test_cases = [
        (0, "A1"),  # First position
        (7, "H1"),  # Last position in first column
        (8, "A2"),  # First position in second column
        (87, "H11"),  # Last position in second-to-last column
        (88, "A12"),  # First position in last column
        (95, "H12"),  # Very last position
    ]

    for position_index, expected_coordinate in test_cases:
        plate_position = PlatePosition.objects.create(
            plate=plate, position=position_index
        )

        coordinate = plate_position.position_to_coordinates()
        assert coordinate == expected_coordinate, (
            f"Edge case: position {position_index} should be {expected_coordinate}, "
            f"got {coordinate}"
        )

        # Clean up
        plate_position.delete()
