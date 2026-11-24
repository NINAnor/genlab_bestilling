import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from genlab_bestilling.models import Location


@pytest.fixture
def api_client():
    user = get_user_model().objects.create_user(email="locations@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_create_location_with_external_id(api_client):
    response = api_client.post(
        reverse("locations-list"),
        {"name": "Test location", "external_id": "source-123"},
    )

    assert response.status_code == 201
    assert response.data["external_id"] == "source-123"
    assert Location.objects.get(pk=response.data["id"]).external_id == "source-123"


@pytest.mark.django_db
def test_create_location_without_external_id(api_client):
    response = api_client.post(reverse("locations-list"), {"name": "Test location"})

    assert response.status_code == 201
    assert response.data["external_id"] is None


@pytest.mark.django_db
def test_filter_locations_by_external_id_exact_and_prefix(api_client):
    matching = Location.objects.create(name="Matching", external_id="source-123")
    Location.objects.create(name="Also matching", external_id="source-456")
    Location.objects.create(name="Other", external_id="other-123")

    exact_response = api_client.get(
        reverse("locations-list"), {"external_id": "source-123"}
    )
    prefix_response = api_client.get(
        reverse("locations-list"), {"external_id__startswith": "source-"}
    )

    assert exact_response.status_code == 200
    assert [item["id"] for item in exact_response.data] == [matching.id]
    assert prefix_response.status_code == 200
    assert {item["external_id"] for item in prefix_response.data} == {
        "source-123",
        "source-456",
    }


@pytest.mark.django_db
def test_create_location_rejects_duplicate_external_id(api_client):
    Location.objects.create(name="Existing", external_id="source-123")

    response = api_client.post(
        reverse("locations-list"),
        {"name": "Duplicate", "external_id": "source-123"},
    )

    assert response.status_code == 400
    assert any(error["attr"] == "external_id" for error in response.data["errors"])
