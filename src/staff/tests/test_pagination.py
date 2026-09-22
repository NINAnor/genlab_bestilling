import pytest
from django.urls import reverse

from genlab_bestilling.models import Sample
from staff.pagination import paginate_queryset


def _give_numeric_names(samples: list[Sample], count: int) -> list[Sample]:
    """Rename the first `count` samples to plain numeric strings in place.

    Used to make some fixture samples' `name_as_int` non-`NULL` (numeric)
    while others keep the fixture's default non-numeric (`uuid1()`) names,
    so tests can straddle the numeric/non-numeric ordering boundary.
    """
    numeric_samples = samples[:count]
    for index, sample in enumerate(numeric_samples):
        sample.name = str(index + 1)
        sample.save()
    return numeric_samples


@pytest.mark.django_db
def test_paginate_queryset_by_name_as_int_does_not_skip_non_numeric_names(extraction):
    """Regression test for the "sort by name" infinite-scroll bug.

    `name_as_int` is NULL for any sample whose `name` isn't a plain numeric
    string. Ordering/seeking primarily by a nullable column used to cause
    keyset pagination to permanently drop every row on the NULL side of the
    numeric/non-numeric boundary once the cursor crossed it.
    """
    samples = list(Sample.objects.filter(order=extraction))
    assert len(samples) >= 2, "fixture should create at least two samples"

    _give_numeric_names(samples, count=2)

    all_sample_ids = {sample.id for sample in samples}

    queryset = Sample.objects.filter(order=extraction).annotate_numeric_name()
    ordering = ["name_as_int", "name", "id"]

    collected_ids: set[int] = set()
    cursor = None
    # Paginate one row at a time so we cross the numeric/NULL boundary
    # across multiple "load more" requests, exactly like the real page does.
    for _ in range(len(samples) + 1):
        page = paginate_queryset(
            queryset.order_by(*ordering), page_size=1, cursor=cursor
        )
        collected_ids.update(sample.id for sample in page.object_list)
        if page.next_cursor is None:
            break
        cursor = page.next_cursor

    assert collected_ids == all_sample_ids


@pytest.mark.django_db
def test_paginate_queryset_by_name_as_int_does_not_skip_rows_mid_page(extraction):
    """The boundary can also fall in the middle of a page, not just at its
    edge (e.g. one numeric-named and one non-numeric-named sample sharing
    the same page) - this must not skip either row.
    """
    samples = list(Sample.objects.filter(order=extraction))
    assert len(samples) >= 4, "fixture should create at least four samples"

    _give_numeric_names(samples, count=1)
    all_sample_ids = {sample.id for sample in samples}

    queryset = Sample.objects.filter(order=extraction).annotate_numeric_name()
    ordering = ["name_as_int", "name", "id"]

    collected_ids: set[int] = set()
    cursor = None
    page_size = 2
    for _ in range((len(samples) // page_size) + 2):
        page = paginate_queryset(
            queryset.order_by(*ordering), page_size=page_size, cursor=cursor
        )
        collected_ids.update(sample.id for sample in page.object_list)
        if page.next_cursor is None:
            break
        cursor = page.next_cursor

    assert collected_ids == all_sample_ids


@pytest.mark.django_db
def test_paginate_queryset_by_name_as_int_orders_numeric_names_first(extraction):
    """Numeric-named samples should still sort before non-numeric ones."""
    samples = list(Sample.objects.filter(order=extraction))
    assert len(samples) >= 2

    numeric_samples = _give_numeric_names(samples, count=2)

    queryset = Sample.objects.filter(order=extraction).annotate_numeric_name()
    page = paginate_queryset(
        queryset.order_by("name_as_int", "name", "id"),
        page_size=len(numeric_samples),
    )

    assert {sample.id for sample in page.object_list} == {
        sample.id for sample in numeric_samples
    }


@pytest.mark.django_db
def test_order_extraction_samples_view_sort_by_name_loads_all_samples(
    admin_client, extraction
):
    """End-to-end regression test for the `?sort=name` infinite-scroll bug.

    Hits the actual `order-extraction-samples` view/URL named in the bug
    report, paginating through the `sort=name` cursors the same way the
    real "load more" htmx requests do, and asserts every sample eventually
    loads.
    """
    samples = list(Sample.objects.filter(order=extraction))
    assert len(samples) >= 2, "fixture should create at least two samples"

    _give_numeric_names(samples, count=2)
    all_sample_ids = {sample.id for sample in samples}

    url = reverse("staff:order-extraction-samples", kwargs={"pk": extraction.pk})
    collected_ids: set[int] = set()
    cursor = None
    for _ in range(len(samples) + 1):
        params = {"sort": "name"}
        if cursor:
            params["cursor"] = cursor
        response = admin_client.get(url, params)
        assert response.status_code == 200

        table = response.context["table"]
        collected_ids.update(sample.id for sample in table.data)

        next_cursor = getattr(table, "next_cursor", None)
        if next_cursor is None:
            break
        cursor = next_cursor

    assert collected_ids == all_sample_ids
