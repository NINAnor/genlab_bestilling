from typing import Any

import pytest
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from genlab_bestilling.models import AnalysisOrder


@pytest.fixture
def analysis_order_with_metadata_file(genlab_setup):
    order = AnalysisOrder.objects.create(
        genrequest_id=1,
        contact_person="Test Person",
        contact_email="test@example.com",
    )
    order.metadata_file.save(
        "metadata.csv",
        SimpleUploadedFile("metadata.csv", b"col_a,col_b\n1,2\n"),
        save=True,
    )
    return order


def test_edit_view_renders_when_storage_does_not_support_path(
    client, monkeypatch, analysis_order_with_metadata_file
):
    """
    Regression test for the edit page crashing with
    ``NotImplementedError: This backend doesn't support absolute paths.``
    when the default storage backend doesn't implement ``.path()``
    (e.g. S3Boto3Storage in production).
    """
    order = analysis_order_with_metadata_file

    def raise_not_implemented(self: Any, name: str) -> str:
        msg = "This backend doesn't support absolute paths."
        raise NotImplementedError(msg)

    monkeypatch.setattr(FileSystemStorage, "path", raise_not_implemented)

    client.force_login(order.genrequest.creator)

    url = reverse(
        "genrequest-analysis-update",
        kwargs={"genrequest_id": order.genrequest_id, "pk": order.id},
    )
    response = client.get(url)

    assert response.status_code == 200


def test_edit_view_renders_without_metadata_file(client, genlab_setup):
    """Existing behavior for orders without a metadata_file is unchanged."""
    order = AnalysisOrder.objects.create(
        genrequest_id=1,
        contact_person="Test Person",
        contact_email="test@example.com",
    )

    client.force_login(order.genrequest.creator)

    url = reverse(
        "genrequest-analysis-update",
        kwargs={"genrequest_id": order.genrequest_id, "pk": order.id},
    )
    response = client.get(url)

    assert response.status_code == 200


def test_edit_view_renders_with_local_filesystem_storage(
    client, analysis_order_with_metadata_file
):
    """Existing behavior with the local filesystem storage (dev) is unchanged."""
    order = analysis_order_with_metadata_file

    client.force_login(order.genrequest.creator)

    url = reverse(
        "genrequest-analysis-update",
        kwargs={"genrequest_id": order.genrequest_id, "pk": order.id},
    )
    response = client.get(url)

    assert response.status_code == 200
