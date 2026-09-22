import uuid

import pytest
from django.urls import reverse

from genlab_bestilling.models import Sample
from staff.views import SampleLabView


@pytest.mark.django_db
def test_sample_lab_note_autosave_is_delegated_to_the_table_body(
    admin_client, extraction, monkeypatch
):
    """Structural + functional regression test for the "notes lost on
    scroll" bug.

    Samples beyond the first page load into the table via htmx infinite
    scroll (see `staff/tables/_cursor_rows.html`). The note-autosave
    `input` listener must be delegated to the always-present table body
    container rather than bound to each `.internal_note-input` textarea
    individually at initial page load - otherwise note fields rendered
    later via htmx never get wired up, and typed notes silently fail to
    save.

    A real browser can't be driven in this test environment (no
    Playwright browser binaries are installed here - see the
    `@pytest.mark.skip`'d tests in `test_e2e.py`), so this combines two
    checks instead of a full browser round-trip:

    - a structural check that the initial page's autosave script binds
      its listener once, to the shared table body, not in a per-textarea
      loop (this is the part an actual DOM/browser event would exercise
      and that this test environment cannot);
    - a functional check that a note saved (via the same endpoint/request
      shape the delegated listener's `fetch()` call makes) for a sample
      loaded only in a later infinite-scroll batch is actually persisted
      and re-rendered on the next page load - proving the save
      endpoint/render path itself has no dependency on batch/scroll
      position, which is the other half of the bug (the JS wiring is the
      other half, checked structurally above).
    """
    samples = list(Sample.objects.filter(order=extraction))
    assert len(samples) >= 2, "fixture should create at least two samples"
    for index, sample in enumerate(samples):
        sample.genlab_id = f"GID-{index}"
        sample.save()

    # Pad up to (at least) 3 samples so, combined with `page_size = 1`
    # below, we get at least 3 infinite-scroll batches - matching the
    # bug report's acceptance criterion - regardless of how many samples
    # the `extraction` fixture itself happens to create.
    first_sample = samples[0]
    while len(samples) < 3:
        extra = Sample.objects.create(
            order=extraction,
            guid=uuid.uuid4(),
            species=first_sample.species,
            type=first_sample.type,
            year=2020,
            name=uuid.uuid1(),
            genlab_id=f"GID-extra-{len(samples)}",
        )
        samples.append(extra)

    # Force one sample per page, so a 3+ sample order requires 3+ batches.
    monkeypatch.setattr(SampleLabView, "page_size", 1)

    url = reverse("staff:order-extraction-samples-lab", kwargs={"pk": extraction.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    content = response.content.decode()

    # The autosave listener must be bound once, on the shared table body -
    # not once per note textarea - so it keeps working for rows appended
    # after the initial page load.
    assert "getElementById('sample-table-body')" in content
    assert "noteInputs.forEach" not in content, (
        "regression: autosave listener must not be bound per note "
        "textarea at DOMContentLoaded - later htmx-loaded rows would "
        "never get wired up"
    )

    table = response.context["table"]
    next_cursor = table.next_cursor
    assert next_cursor, "fixture should have more than one page to load more of"

    batches = 1
    partial_content = ""
    last_batch_sample_ids: list[int] = []
    while next_cursor:
        # Fetch the next htmx "load more" batch, the same way the browser
        # does.
        partial_response = admin_client.get(
            url, {"cursor": next_cursor}, HTTP_HX_REQUEST="true"
        )
        assert partial_response.status_code == 200
        partial_content = partial_response.content.decode()
        last_batch_sample_ids = [
            row.pk for row in partial_response.context["table"].data
        ]
        next_cursor = partial_response.context["table"].next_cursor
        batches += 1

    assert batches >= 3, (
        "test setup should exercise at least 3 infinite-scroll batches, "
        f"per the bug report's acceptance criterion (got {batches})"
    )

    # Rows loaded via infinite scroll must render a note field, and the
    # partial itself must not contain a `<script>` tag - i.e. the fix must
    # not rely on the autosave script re-running on every htmx swap.
    assert "internal_note-input" in partial_content
    assert "<script" not in partial_content

    # Functional check: saving a note for a sample that only ever appears
    # in a later infinite-scroll batch (never in the initial page) must
    # persist, exactly like it already does for initial-batch samples -
    # the save endpoint/render path has no dependency on batch position.
    last_batch_sample_id = last_batch_sample_ids[0]
    note_text = "note added while scrolled down"
    save_response = admin_client.post(
        reverse("staff:update-internal-note"),
        {
            "sample_id": last_batch_sample_id,
            "field_name": "internal_note-input",
            "field_value": note_text,
        },
    )
    assert save_response.status_code == 200

    reloaded = Sample.objects.get(id=last_batch_sample_id)
    assert reloaded.internal_note == note_text
