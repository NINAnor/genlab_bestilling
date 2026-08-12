from django.db import close_old_connections
from django.tasks import task

from .models import ExtractionPlate


@task
def isolate_all_samples(
    plate_id: str,
) -> None:
    close_old_connections()
    ExtractionPlate.objects.get(pk=plate_id).deferred_isolate_all_samples()
