from typing import Any

import sqlglot
import sqlglot.expressions
from django.db import connection, transaction
from sqlglot.expressions import (
    EQ,
    Alias,
    Cast,
    DataType,
    Extract,
    From,
    Literal,
    Subquery,
    and_,
    column,
)

from ..models import ExtractionOrder, Order, Sample, Species


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


def generate(order_id, sorting_order=None, selected_samples=None):
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


def update_genlab_id_query(order_id, sorting_order=None, selected_samples=None):
    """
    Safe generation of a SQL raw query using sqlglot
    The query runs an update on all the rows with a specific order_id
    and set genlab_id = generate_genlab_id(code, year)
    """
    if sorting_order is None:
        sorting_order = []

    samples_table = Sample._meta.db_table
    extraction_order_table = ExtractionOrder._meta.db_table
    order_table = Order._meta.db_table
    species_table = Species._meta.db_table

    order_by_columns = (
        [column(col, table=samples_table) for col in sorting_order]
        if sorting_order
        else [column("name", table=samples_table)]
    )

    return sqlglot.expressions.update(
        samples_table,
        properties={
            "genlab_id": column(
                "genlab_id",
                table="order_samples",
            )
        },
        where=sqlglot.expressions.EQ(
            this=column("id", table=samples_table),
            expression="order_samples.id",
        ),
        from_=From(
            this=Alias(
                this=Subquery(
                    this=(
                        sqlglot.select(
                            column(
                                "id",
                                table=samples_table,
                            ),
                            Alias(
                                this=sqlglot.expressions.func(
                                    "generate_genlab_id",
                                    column("code", table=species_table),
                                    Cast(
                                        this=Extract(
                                            this="YEAR",
                                            expression=column(
                                                "confirmed_at",
                                                table=order_table,
                                            ),
                                        ),
                                        to=DataType(
                                            this=DataType.Type.INT, nested=False
                                        ),
                                    ),
                                ),
                                alias="genlab_id",
                            ),
                        )
                        .join(
                            extraction_order_table,
                            on=EQ(
                                this=column(
                                    "order_id",
                                    table=samples_table,
                                ),
                                expression=column(
                                    "order_ptr_id",
                                    table=extraction_order_table,
                                ),
                            ),
                        )
                        .join(
                            order_table,
                            on=EQ(
                                this=column(
                                    "order_ptr_id",
                                    table=extraction_order_table,
                                ),
                                expression=column(
                                    "id",
                                    table=order_table,
                                ),
                            ),
                        )
                        .from_(samples_table)
                        .join(
                            species_table,
                            on=EQ(
                                this=column(
                                    "species_id",
                                    table=samples_table,
                                ),
                                expression=column(
                                    "id",
                                    table=species_table,
                                ),
                            ),
                        )
                        .where(
                            and_(
                                EQ(
                                    this=column(col="order_id"),
                                    expression=Literal.number(order_id),
                                ),
                                column(col="genlab_id").is_(None),
                            )
                        )
                        .order_by(*order_by_columns)
                    ),
                ),
                alias="order_samples",
            )
        ),
    ).sql(dialect="postgres")
