from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models, transaction
from django.db.models import BigIntegerField, Case, IntegerField, QuerySet, Value, When
from django.db.models.functions import Cast
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet

from shared.db import assert_is_in_atomic_block

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.db.models import QuerySet

    from capps.users.models import User

    from .models import GIDSequence, Species


class GenrequestQuerySet(models.QuerySet):
    def filter_allowed(self, user: User) -> QuerySet:
        """
        Get only requests of projects that the user is part of
        """
        return self.filter(project__memberships=user)


class OrderQuerySet(PolymorphicQuerySet):
    def filter_allowed(self, user: User) -> QuerySet:
        """
        Get only orders of projects that the user is part of
        """
        return self.filter(genrequest__project__memberships=user)

    def filter_in_draft(self) -> QuerySet:
        """
        Get only orders in draft
        """
        return self.filter(status=self.model.OrderStatus.DRAFT)

    def annotate_priority_order(self) -> QuerySet:
        """
        Annotate the queryset with a priority order based on urgency and prioritization.
        Order should be: urgent > prioritized > normal.
        """
        return self.annotate(
            priority_order=Case(
                When(is_urgent=True, then=self.model.OrderPriority.URGENT),
                When(
                    is_prioritized=True,
                    then=Value(self.model.OrderPriority.PRIORITIZED),
                ),
                default=Value(self.model.OrderPriority.NORMAL),
                output_field=IntegerField(),
            )
        )


OrderManager = PolymorphicManager.from_queryset(OrderQuerySet)


class EquipmentOrderQuantityQuerySet(models.QuerySet):
    def filter_allowed(self, user: User) -> QuerySet:
        """
        Get only orders of projects that the user is part of
        """
        return self.filter(order__genrequest__project__memberships=user)

    def filter_in_draft(self) -> QuerySet:
        """
        Get only orders in draft
        """
        return self.select_related("order").filter(
            order__status=self.model.OrderStatus.DRAFT
        )


class SampleQuerySet(models.QuerySet):
    def filter_allowed(self, user: User) -> QuerySet:
        """
        Get only samples of projects that the user is part of
        """
        return self.filter(order__genrequest__project__memberships=user)

    def filter_in_draft(self) -> QuerySet:
        """
        Get only samples of orders in draft
        """
        return self.select_related("order").filter(
            order__status=self.model.OrderStatus.DRAFT
        )

    def annotate_numeric_name(self) -> QuerySet:
        """
        Create a new column with the numeric version of the name.
        Only if the name is a valid integer, and up to 18 digits, so it fit in a
        BigIntegerField.
        """

        return self.annotate(
            name_as_int=Case(
                When(
                    name__regex=r"^\d{1,18}$",
                    then=Cast("name", BigIntegerField()),
                ),
                default=Value(None),
                output_field=BigIntegerField(),
            )
        )

    @transaction.atomic
    def generate_genlab_ids(
        self,
        order_id: int,
        selected_samples: Sequence[int | str] | None = None,
    ) -> None:
        """
        genlab ids given a certain order_id, sorting order and sample ids
        """
        assert_is_in_atomic_block()

        selected_samples = selected_samples or []
        selected_sample_ids = [int(s) for s in selected_samples]

        samples = list(
            (
                self.select_related("species", "order")
                .filter(
                    order_id=order_id,
                    genlab_id__isnull=True,
                    id__in=selected_sample_ids,
                )
                .only("id", "genlab_id", "order__confirmed_at", "species__code")
                .select_for_update()
            ).all()
        )

        # Sort samples in the order of selected_samples
        id_pos = {id_: i for i, id_ in enumerate(selected_sample_ids)}
        samples.sort(key=lambda sample: id_pos.get(sample.id, 99999))  # Safe fallback

        updates = []
        for sample in samples:
            sample.generate_genlab_id(commit=False)
            updates.append(sample)

        self.bulk_update(updates, ["genlab_id"])


class SampleAnalysisMarkerQuerySet(models.QuerySet):
    def filter_allowed(self, user: User) -> QuerySet:
        """
        Get only samples of projects that the user is part of
        """
        return self.filter(order__genrequest__project__memberships=user)

    def filter_in_draft(self) -> QuerySet:
        """
        Get only samples of orders in draft
        """
        return self.select_related("order").filter(
            order__status=self.model.OrderStatus.DRAFT
        )


class GIDSequenceQuerySet(models.QuerySet):
    def get_sequence_for_species_year(
        self, species: Species, year: int, lock: bool = False
    ) -> GIDSequence:
        """
        Get or creates an ID sequence based on the sample year and species
        """
        s = self.select_for_update() if lock else self

        sequence_id, _ = s.get_or_create(
            year=year,
            species=species,
            defaults={"id": f"G{year % 100}{species.code}"},
        )
        return sequence_id
