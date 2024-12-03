import sqlglot
import sqlglot.expressions
from django.db import connection, transaction
from sqlglot.expressions import (
    EQ,
    Alias,
    From,
    Literal,
    Subquery,
    and_,
    column,
)

from ..models import Sample, Species


def get_current_sequences(order_id):
    samples = (
        Sample.objects.select_related("species")
        .filter(order=order_id)
        .values("year", "species__code")
        .distinct()
    )

    with connection.cursor() as cursor:
        sequences = {}
        for sample in samples:
            query = sqlglot.select(
                sqlglot.expressions.func(
                    "get_genlab_sequence_name",
                    sqlglot.expressions.Literal.string(sample["species__code"]),
                    sqlglot.expressions.Literal.number(sample["year"]),
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


def generate(order_id):
    sequences = get_current_sequences(order_id)
    print(sequences)

    with connection.cursor() as cursor:
        try:
            with transaction.atomic():
                cursor.execute(update_genlab_id_query(order_id))
        except Exception:
            # if there is an error, reset the sequence
            # NOTE: this is unsafe unless this function is execute in a queue
            # by just one worker to prevent concurrency
            with connection.cursor() as cursor:
                for k, v in sequences.items():
                    cursor.execute("SELECT setval(%s, %s)", [k, v])

    sequences = get_current_sequences(order_id)
    print(sequences)


def update_genlab_id_query(order_id):
    samples_table = Sample._meta.db_table
    species_table = Species._meta.db_table

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
                                    column("code", table=Species._meta.db_table),
                                    column(
                                        "year",
                                        table=samples_table,
                                    ),
                                ),
                                alias="genlab_id",
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
                        .order_by(column("name", table=samples_table))
                    ),
                ),
                alias="order_samples",
            )
        ),
    ).sql(dialect="postgres")
