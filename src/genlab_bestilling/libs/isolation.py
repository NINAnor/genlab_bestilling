from django.db import transaction

from ..models import ExtractionPlate, ExtractPlatePosition, Sample

PLATE_SIZE = 96


# NOTE: this is probably a naive implementation
# we might need full user control on how to fill a certain plate
def isolate(order_id):
    with transaction.atomic():
        base_query = (
            Sample.objects.select_related("species", "location")
            .filter(order_id=order_id)
            .exclude(genlab_id=None)
            .order_by("species__name", "year", "location__name", "name")
        )

        # TODO: Get incomplete plates if available!
        plate = None
        position = PLATE_SIZE

        for sample in base_query:
            for _ in range(sample.desired_extractions):
                if position >= PLATE_SIZE:
                    plate = ExtractionPlate.objects.create()
                    position = 0

                ExtractPlatePosition.objects.create(
                    plate=plate, sample=sample, position=position
                )
                position += 1
