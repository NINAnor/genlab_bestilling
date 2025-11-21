from procrastinate.contrib.django import app

from .models import ExtractionPlate


@app.task
def isolate_all_samples(
    plate_id: str,
) -> None:
    ExtractionPlate.objects.get(pk=plate_id).deferred_isolate_all_samples()
