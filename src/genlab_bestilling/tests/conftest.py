import itertools
import os
import uuid

import pytest
from django.core.management import call_command

from genlab_bestilling.models import ExtractionOrder, Sample

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture(scope="session")
def live_server_url():
    return os.environ.get("LIVE_SERVER_URL")


@pytest.fixture
def genlab_setup(
    django_db_reset_sequences, transactional_db, django_db_setup, django_db_blocker
):
    with django_db_blocker.unblock():
        call_command("setup")


@pytest.fixture
def extraction(genlab_setup):
    ext = ExtractionOrder.objects.create(
        genrequest_id=1,
        return_samples=False,
        pre_isolated=False,
    )
    ext.species.add(*ext.genrequest.species.all())
    ext.sample_types.add(*ext.genrequest.sample_types.all())

    combo = itertools.product(ext.species.all(), ext.sample_types.all())

    for species, sample_type in combo:
        Sample.objects.create(
            order=ext,
            guid=uuid.uuid4(),
            species=species,
            type=sample_type,
            year=2020,
            name=uuid.uuid1(),
        )
    return ext
