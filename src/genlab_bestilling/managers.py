from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models, transaction
from django.db.models import Case, IntegerField, QuerySet, Value, When
from django.db.models.functions import Cast
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
        sorting_order: list[str] | None = None,
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

        # if we are defaulting, set to name as of now
        if not sorting_order:
            sorting_order = ["name"]

        # able to sort on nullable fields
        if any("type" in field for field in sorting_order):
            samples = samples.filter(type__isnull=False)

        # handle name based on its type
        if sorting_order and any(f.lstrip("-") == "name" for f in sorting_order):
            samples = samples.annotate(
                name_as_int=Case(
                    When(name__regex=r"^\d+$", then=Cast("name", IntegerField())),
                    default=Value(None),
                    output_field=IntegerField(),
                )
            )

            # Replace "name" with "name_as_int" (and optionally fallback to "name")
            new_sorting_order = []
            for field in sorting_order:
                is_desc = field.startswith("-")
                base = field.lstrip("-")

                if base == "name":
                    # Sort numerically first
                    name_as_int = "-name_as_int" if is_desc else "name_as_int"
                    name_fallback = "-name" if is_desc else "name"
                    new_sorting_order.extend([name_as_int, name_fallback])
                else:
                    new_sorting_order.append(field)

            sorting_order = new_sorting_order

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
