from django.db import transaction

from ..models import ExtractionPlate, ExtractPlatePosition, Sample

PLATE_SIZE = 96


# NOTE: this is probably a naive implementation
# we might need full user control on how to fill a certain plate
def isolate(order_id: int | str) -> None:
    with transaction.atomic():
        base_query = (
            Sample.objects.select_related("species", "location")
            .filter(order_id=order_id)
            .exclude(genlab_id=None)
            .order_by("species__name", "year", "location__name", "name")
        )

        # TODO: Get incomplete plates if available!
        plates_to_create = []
        positions_to_create = []
        current_plate_id = None
        position = PLATE_SIZE

        for sample in base_query:
            for _ in range(sample.desired_extractions):
                if position >= PLATE_SIZE:
                    # Create new plate
                    plate = ExtractionPlate()
                    plates_to_create.append(plate)
                    current_plate_id = len(plates_to_create) - 1
                    position = 0

                positions_to_create.append({
                    'plate_index': current_plate_id,
                    'sample': sample,
                    'position': position,
                })
                position += 1

        # Bulk create plates first
        if plates_to_create:
            ExtractionPlate.objects.bulk_create(plates_to_create)
            
            # Get the created plates to reference in positions
            created_plates = list(ExtractionPlate.objects.order_by('-id')[:len(plates_to_create)])
            created_plates.reverse()  # Match creation order
            
            # Create position objects with references to created plates
            position_objects = []
            for pos_data in positions_to_create:
                position_objects.append(ExtractPlatePosition(
                    plate=created_plates[pos_data['plate_index']],
                    sample=pos_data['sample'],
                    position=pos_data['position'],
                ))
            
            # Bulk create positions
            ExtractPlatePosition.objects.bulk_create(position_objects)
