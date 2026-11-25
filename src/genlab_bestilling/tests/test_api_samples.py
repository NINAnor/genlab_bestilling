import pytest
from django.contrib.auth import get_user_model
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APIClient

from genlab_bestilling.models import Location, Sample


@pytest.fixture
def api_client():
    user = get_user_model().objects.create_user(email="samples@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
def test_create_sample_accepts_foreign_key_ids(api_client, extraction):
    species = extraction.species.first()
    sample_type = extraction.sample_types.first()
    location = Location.objects.create(name="Test location")

    response = api_client.post(
        "/api/samples/",
        {
            "order": extraction.id,
            "species": species.id,
            "type": sample_type.id,
            "location": location.id,
            "year": 2026,
        },
        format="json",
    )

    assert response.status_code == 201
    sample = Sample.objects.get(pk=response.data["id"])
    assert sample.species_id == species.id
    assert sample.type_id == sample_type.id
    assert sample.location_id == location.id
    assert response.data["species"] == {"id": species.id, "name": species.name}
    assert response.data["type"] == {
        "id": sample_type.id,
        "name": sample_type.name,
    }
    assert response.data["location"]["id"] == location.id


@pytest.mark.django_db
def test_sample_create_openapi_documents_foreign_key_ids():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    operation = schema["paths"]["/api/samples/"]["post"]

    def contains_type(schema_part, expected_type):
        if "$ref" in schema_part:
            component_name = schema_part["$ref"].rsplit("/", 1)[-1]
            return contains_type(
                schema["components"]["schemas"][component_name], expected_type
            )
        if schema_part.get("type") == expected_type:
            return True
        return any(
            contains_type(branch, expected_type)
            for keyword in ("anyOf", "oneOf", "allOf")
            for branch in schema_part.get(keyword, [])
        )

    request_schema = schema["components"]["schemas"][
        operation["requestBody"]["content"]["application/json"]["schema"][
            "$ref"
        ].rsplit("/", 1)[-1]
    ]

    for field in ("type", "species", "location"):
        assert contains_type(request_schema["properties"][field], "integer")

    response_schema_ref = operation["responses"]["201"]["content"]["application/json"][
        "schema"
    ]["$ref"]
    response_schema = schema["components"]["schemas"][
        response_schema_ref.rsplit("/", 1)[-1]
    ]
    for field in ("type", "species", "location"):
        assert contains_type(response_schema["properties"][field], "object")
