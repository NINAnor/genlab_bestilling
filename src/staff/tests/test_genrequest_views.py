import pytest
from django.urls import reverse

from genlab_bestilling.models import Genrequest


@pytest.mark.django_db
def test_genrequest_list_view_shows_all_genrequests_to_staff(admin_client, extraction):
    """Regression test for the reported bug: a staff user with no
    ownership/organization relationship to a genetic project must still be
    able to see it in the staff "Genetic Projects" list.
    """
    url = reverse("staff:genrequests-list")
    response = admin_client.get(url)

    assert response.status_code == 200
    table_data = list(response.context["table"].data)
    assert extraction.genrequest in table_data


@pytest.mark.django_db
def test_genrequest_detail_view_is_accessible_to_staff_regardless_of_ownership(
    admin_client, extraction
):
    """Regression test for the reported bug: `/staff/genrequests/<id>/`
    must not 404/403 for a staff user who isn't the genrequest's owner or a
    member of its organization - unlike the customer-facing
    `genrequest-detail` view, this staff view has no ownership scoping.
    """
    genrequest = extraction.genrequest
    url = reverse("staff:genrequests-detail", kwargs={"pk": genrequest.pk})
    response = admin_client.get(url)

    assert response.status_code == 200
    assert response.context["object"] == genrequest

    orders_table_data = list(response.context["orders_table"].data)
    assert extraction in orders_table_data


@pytest.mark.django_db
def test_genrequest_detail_view_404s_for_unknown_pk(admin_client):
    url = reverse(
        "staff:genrequests-detail",
        kwargs={"pk": Genrequest.objects.count() + 1000},
    )
    response = admin_client.get(url)

    assert response.status_code == 404
