from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models, transaction
from django.db.models import QuerySet
from django.db.models.expressions import RawSQL
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet

from capps.users.models import User

if TYPE_CHECKING:
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


DEFAULT_SORTING_FIELDS = ["name_as_int", "name"]


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

    @transaction.atomic
    def generate_genlab_ids(
        self,
        order_id: int,
        sorting_order: list[str] | None = DEFAULT_SORTING_FIELDS,
        selected_samples: list[int] | None = None,
    ) -> None:
        """
        genlab ids given a certain order_id, sorting order and sample ids

        """

        # Lock the samples
        samples = (
            self.select_related("species")
            .filter(order_id=order_id, genlab_id__isnull=True)
            .select_for_update()
        )

        if selected_samples:
            samples = samples.filter(id__in=selected_samples)

        if sorting_order == DEFAULT_SORTING_FIELDS:
            # create an annotation containg all integer values
            # of "name", so that it's possible to sort numerically and alphabetically
            samples = samples.annotate(
                name_as_int=RawSQL(
                    r"substring(%s from '^\d+$')::int",
                    params=["name"],
                    output_field=models.IntegerField(),
                )
            ).order_by(*sorting_order)
        else:
            samples = samples.order_by(*sorting_order)

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
        if lock:
            s = self.select_for_update()
        else:
            s = self

        sequence_id, _ = s.get_or_create(
            year=year,
            species=species,
            defaults={"id": f"G{year % 100}{species.code}"},
        )
        return sequence_id
