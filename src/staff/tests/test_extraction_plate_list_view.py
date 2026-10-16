import re
import uuid

import pytest
from django.urls import reverse

from genlab_bestilling.models import ExtractionPlate, Sample
from staff.filters import ExtractionPlateFilter
from staff.views import ExtractionPlateListView


def _create_plate_matching_both_filters(extraction):
    """Build a plate where `species` and `year` each independently match
    >= 2 and >= 1 extra position respectively - the shape that triggered
    the join-multiplication bug when both filters are combined.
    """
    plate = ExtractionPlate.objects.create()

    samples = list(extraction.samples.all())
    assert len(samples) >= 2
    species_id = samples[0].species_id
    same_species_samples = [s for s in samples if s.species_id == species_id]
    assert len(same_species_samples) >= 2, "fixture must provide same-species samples"

    year = same_species_samples[0].year
    same_year_sample = Sample.objects.create(
        order=extraction,
        guid=uuid.uuid4(),
        species_id=species_id,
        type=same_species_samples[0].type,
        year=year,
        name="combined-filter-regression-sample",
    )

    positions = list(plate.positions.order_by("position"))
    assert len(positions) == 96

    # Two positions match the species filter.
    for position, sample in zip(positions[:2], same_species_samples[:2], strict=False):
        position.sample_raw = sample
        position.save()

    # A third, distinct position also matches the year filter.
    positions[2].sample_raw = same_year_sample
    positions[2].save()

    reserved = positions[3]
    reserved.is_reserved = True
    reserved.save()

    return plate, species_id, year


@pytest.mark.django_db(transaction=True)
def test_extraction_plate_list_view_combined_filters_return_correct_counts(
    admin_client, extraction
):
    """Regression test for the reported bug: combining two
    `positions__sample_raw__*` filters (species *and* year, as both bug
    reports on the "calculation error" ticket did) must still return the
    plate with correct, non-inflated counts.
    """
    plate, species_id, year = _create_plate_matching_both_filters(extraction)

    url = reverse("staff:extraction-plates-list")
    response = admin_client.get(
        url,
        {
            "positions__sample_raw__species": species_id,
            "positions__sample_raw__year": year,
        },
    )

    assert response.status_code == 200
    table_data = list(response.context["table"].data)
    annotated = next(row for row in table_data if row.pk == plate.pk)

    assert annotated.sample_count == 3
    assert annotated.reserved_count == 1
    assert annotated.available_count == 92


@pytest.mark.django_db(transaction=True)
def test_extraction_plate_list_view_table_data_does_not_duplicate_joins(extraction):
    """`ExtractionPlateFilter` applies each field as its own separate
    `.filter()` call, each adding a JOIN on `positions`/`sample_raw`. If the
    view's `with_sample_species()`/`with_position_counts()` annotations
    (which force a `GROUP BY plate.id`) shared that same relation with two
    or more of those filter joins, matching positions multiply rows before
    grouping - slow enough, at real data volume, to time out (reported as
    "current main ends in a timeout running the query").

    `get_table_data()` must annotate only *after* filtering (against a
    restricted `pk__in` set), so the final queryset never combines filter
    joins with annotation joins, regardless of how many filter fields are
    active at once.
    """
    _create_plate_matching_both_filters(extraction)

    view = ExtractionPlateListView()
    view.object_list = ExtractionPlateFilter(
        data={
            "positions__sample_raw__species": extraction.samples.first().species_id,
            "positions__sample_raw__year": extraction.samples.first().year,
        },
        queryset=view.get_queryset(),
    ).qs

    table_queryset = view.get_table_data()
    sql = str(table_queryset.query)

    # Django aliases repeated joins on the same relation "T4", "T5", ...;
    # none should appear once filtering and annotation are decoupled.
    assert not re.search(r'"T\d+"', sql), (
        f"query contains duplicated joins from combining filters with "
        f"annotations: {sql}"
    )


@pytest.mark.django_db(transaction=True)
def test_extraction_plate_list_view_pagination_queryset_does_not_duplicate_joins(
    extraction,
):
    """Same guarantee as above, but for the lean seek queryset used by
    `CursorPaginatedTableMixin.get_table()` (`get_pagination_queryset()`).
    """
    _create_plate_matching_both_filters(extraction)

    view = ExtractionPlateListView()
    view.object_list = ExtractionPlateFilter(
        data={
            "positions__sample_raw__species": extraction.samples.first().species_id,
            "positions__sample_raw__year": extraction.samples.first().year,
        },
        queryset=view.get_queryset(),
    ).qs

    sql = str(view.get_pagination_queryset().query)

    assert not re.search(r'"T\d+"', sql), (
        f"query contains duplicated joins from combining filters with "
        f"annotations: {sql}"
    )


@pytest.mark.django_db(transaction=True)
def test_extraction_plate_list_view_pagination_queryset_has_no_group_by_or_joins(
    extraction,
):
    """The seek/ordering queryset must stay cheap: no `GROUP BY` and no join
    to `positions`/`sample_raw`/`species`, regardless of total plate size -
    the expensive annotations belong only in `get_page_data()`, applied to
    the current page's rows.
    """
    _create_plate_matching_both_filters(extraction)

    view = ExtractionPlateListView()
    view.object_list = view.get_queryset()

    sql = str(view.get_pagination_queryset().query)

    assert "GROUP BY" not in sql
    assert "genlab_bestilling_plateposition" not in sql
    assert "genlab_bestilling_sample" not in sql
    assert "genlab_bestilling_species" not in sql
