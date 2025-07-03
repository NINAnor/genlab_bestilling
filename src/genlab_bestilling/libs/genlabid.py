from typing import Any

import sqlglot
import sqlglot.expressions
from django.db import connection, transaction
from django.db.models import Case, QuerySet, When

from ..models import Sample


def get_replica_for_sample() -> None:
    """
    TODO: implement
    """
    pass


def get_current_sequences(order_id: int | str) -> Any:
    """
    Invoke a Postgres function to get the current sequence number
    for a specific combination of year and species.
    """
    samples = (
        Sample.objects.select_related("order", "species")
        .filter(order=order_id)
        .values("order__created_at", "species__code")
        .distinct()
    )

    with connection.cursor() as cursor:
        sequences = {}
        for sample in samples:
            query = sqlglot.select(
                sqlglot.expressions.func(
                    "get_genlab_sequence_name",
                    sqlglot.expressions.Literal.string(sample["species__code"]),
                    sqlglot.expressions.Literal.number(
                        sample["order__created_at"].year
                    ),
                    dialect="postgres",
                )
            ).sql(dialect="postgres")
            seq = cursor.execute(
                query,
            ).fetchone()[0]
            sequences[seq] = 0

        for k in sequences.keys():
            query = sqlglot.select("last_value").from_(k).sql(dialect="postgres")
            sequences[k] = cursor.execute(query).fetchone()[0]

        return sequences


def generate(
    order_id: int,
    sorting_order: list[str] | None = None,
    selected_samples: list[int] | None = None,
) -> None:
    """
    wrapper to handle errors and reset the sequence to the current sequence value
    """
    sequences = get_current_sequences(order_id)
    print(sequences)

    with connection.cursor() as cursor:
        try:
            with transaction.atomic():
                cursor.execute(
                    update_genlab_id_query(order_id, sorting_order, selected_samples)
                )
        except Exception:
            # if there is an error, reset the sequence
            # NOTE: this is unsafe unless this function is executed in a queue
            # by just one worker to prevent concurrency
            with connection.cursor() as cursor:  # noqa: PLW2901 # Was this intentional?
                for k, v in sequences.items():
                    cursor.execute("SELECT setval(%s, %s)", [k, v])

    sequences = get_current_sequences(order_id)
    print(sequences)


# Format the genlab ID as GYYCODEXXXX
def generate_genlab_id(code: str, year: int, count: int) -> str:
    """
    Generating the genlab ID in the format GYYCODEXXXX
    where:
    - YY is the last two digits of the year
    - CODE is the species code in uppercase
    - XXXX is a zero-padded number starting from 0001 for each species
    and year combination.
    Example: G23ABC0001 for the first sample of species ABC in 2023.
    """
    return f"G{str(year)[-2:]}{code.upper()}{count:04d}"


# Order samples by their names, assuming they are numeric strings
def order(samples: QuerySet) -> QuerySet:
    """
    Order samples by their names, assuming they are numeric strings.
    """
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
def update_genlab_id_query(
    order_id: int,
    sorting_order: list[str] | None = None,
    selected_samples: list[int] | None = None,
) -> None:
    """
    Generate genlab IDs for samples in a specific order using Django QuerySet API.
    """
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
