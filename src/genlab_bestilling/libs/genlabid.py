from django.db import transaction
from django.db.models import Case, QuerySet, When

from ..models import Sample


# Format the genlab ID as GYYCODEXXXX
def generate_genlab_id(code: str, year: int, count: int) -> str:
    return f"G{str(year)[-2:]}{code.upper()}{count:04d}"


# Order samples by their names, assuming they are numeric strings
def order(samples: QuerySet) -> QuerySet:
    name_to_sample = {sample.name.strip(): sample for sample in samples}
    names = list(name_to_sample.keys())

    # Check all are digits
    if not all(name.isdigit() for name in names):
        return samples

    # Sort names as integers
    sorted_names = sorted(names, key=lambda x: int(x))

    # Build a CASE statement to preserve order in SQL
    when_statements = [
        When(name=name, then=pos) for pos, name in enumerate(sorted_names)
    ]

    return samples.order_by(Case(*when_statements))


# New entry point for generating genlab IDs
@transaction.atomic
def generate(
    order_id: int,
    sorting_order: list[str] | None = None,
    selected_samples: list[int] | None = None,
) -> None:
    if selected_samples is None:
        return

    # Sort order, default is by name
    order_by = sorting_order or ["name"]

    # Fetch samples
    samples = (
        Sample.objects.select_related("species", "order")
        .filter(order_id=order_id, id__in=selected_samples, genlab_id__isnull=True)
        .order_by(*order_by)
    )

    # If sorting order is by name, we might need to order them numerically
    if order_by == ["name"]:
        samples = order(samples)

    # Group counts by species + year
    counts = {}
    updates = []

    # Iterate through samples to generate genlab IDs in correct order
    for sample in list(samples):
        # Extract species code and year from the sample
        species_code = sample.species.code
        year = sample.order.confirmed_at.year
        key = (species_code, year)

        # Initialize count
        if key not in counts:
            existing_count = Sample.objects.filter(
                species__code=species_code,
                order__confirmed_at__year=year,
                genlab_id__isnull=False,
            ).count()
            counts[key] = existing_count + 1
        else:
            counts[key] += 1

        genlab_id = generate_genlab_id(species_code, year, counts[key])
        sample.genlab_id = genlab_id
        updates.append(sample)

    # Bulk update samples with new genlab IDs
    Sample.objects.bulk_update(updates, ["genlab_id"])
