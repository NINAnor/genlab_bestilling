from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from django.db import models, transaction
from django.db.models import BigIntegerField, Case, Q, QuerySet, Value, When
from django.db.models.functions import Cast
from polymorphic.managers import PolymorphicManager, PolymorphicQuerySet

from shared.db import assert_is_in_atomic_block

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.db.models import QuerySet

    from capps.users.models import User

    from .models import GIDSequence, Sample, Species


class VisibleManager(models.Manager):
    """Manager that excludes records marked as hidden (is_hidden=True)."""

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(is_hidden=False)


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

    def filter_by_sample_id(self, value: str) -> QuerySet:
        """
        Filter orders by sample genlab_id, name, or guid.

        Searches for samples where genlab_id, name, or guid contains the
        given value.
        """
        if not value:
            return self

        return self.filter(
            Q(samples__genlab_id__icontains=value)
            | Q(samples__name__icontains=value)
            | Q(samples__guid__icontains=value)
        ).distinct()


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

    def filter_by_search(self, value: str) -> QuerySet:
        """
        Filter samples by genlab_id, name, or guid.

        Searches for samples where genlab_id, name, or guid contains the
        given value.
        """
        if not value:
            return self

        return self.filter(
            Q(genlab_id__icontains=value)
            | Q(name__icontains=value)
            | Q(guid__icontains=value)
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


class ExtractionPlateQuerySet(PolymorphicQuerySet):
    def filter_by_search(self, value: str) -> QuerySet:
        """
        Filter extraction plates by sample genlab_id or name.

        Searches for plates with a sample position whose genlab_id or name
        contains the given value.
        """
        if not value:
            return self

        return self.filter(
            Q(positions__sample_raw__genlab_id__icontains=value)
            | Q(positions__sample_raw__name__icontains=value)
        ).distinct()


class AnalysisStatus(StrEnum):
    """Status of a sample marker analysis based on plate positions."""

    NOT_STARTED = "not_started"
    PCR = "pcr"
    ANALYZING = "analyzing"
    RESULTS = "results"
    INVALID = "invalid"


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

    def filter_by_search(self, value: str) -> QuerySet:
        """
        Filter sample markers by related sample genlab_id, name, or guid.

        Searches for sample markers whose sample genlab_id, name, or guid
        contains the given value.
        """
        if not value:
            return self

        return self.filter(
            Q(sample__genlab_id__icontains=value)
            | Q(sample__name__icontains=value)
            | Q(sample__guid__icontains=value)
        ).distinct()

    def filter_status_not_started(self) -> QuerySet:
        """Filter sample markers with no positions on analysis plates and no PCR."""
        return self.filter(
            positions__isnull=True, has_pcr=False, is_analysed=False, is_outputted=False
        )

    def filter_status_pcr(self) -> QuerySet:
        """Filter markers with PCR or positions, none on plates with analysis_date."""
        return (
            self.filter(Q(has_pcr=True, is_analysed=False) | Q(positions__isnull=False))
            .exclude(positions__plate__analysisplate__analysis_date__isnull=False)
            .distinct()
        )

    def filter_status_analyzing(self) -> QuerySet:
        """Filter sample markers on plates with analysis_date but no result_file,
        and that are analysed but not yet outputted.
        """
        return self.filter(
            Q(
                positions__plate__analysisplate__analysis_date__isnull=False,
                positions__plate__analysisplate__result_file="",
            )
            | Q(is_analysed=True, is_outputted=False)
        ).distinct()

    def filter_status_results(self) -> QuerySet:
        """Filter sample markers on plates with result_file or outputted."""
        return self.filter(
            Q(positions__plate__analysisplate__result_file__isnull=False)
            & ~Q(positions__plate__analysisplate__result_file="")
            | Q(is_outputted=True)
        ).distinct()

    def filter_status_invalid(self) -> QuerySet:
        """Filter sample markers with at least one invalid position."""
        return self.filter(positions__is_invalid=True).distinct()

    def filter_by_status(self, status: str | AnalysisStatus) -> QuerySet:
        """Filter by analysis status.

        Status is determined by sample marker fields and plate positions:
        - not_started: No positions on analysis plates and no PCR
        - pcr: Has PCR or positions, but none on plates with analysis_date
        - analyzing: On plate with analysis_date (no result_file), is_analysed,
            not outputted
        - results: Has positions on plates with result_file OR is_outputted=True
        - invalid: Has at least one invalid position
        """
        if status == AnalysisStatus.NOT_STARTED:
            return self.filter_status_not_started()
        if status == AnalysisStatus.PCR:
            return self.filter_status_pcr()
        if status == AnalysisStatus.ANALYZING:
            return self.filter_status_analyzing()
        if status == AnalysisStatus.RESULTS:
            return self.filter_status_results()
        if status == AnalysisStatus.INVALID:
            return self.filter_status_invalid()
        return self


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
            sample=None,
            defaults={"id": f"G{year % 100}{species.code}"},
        )
        return sequence_id

    def get_sequence_for_replication(
        self, sample: Sample, lock: bool = False
    ) -> GIDSequence:
        """
        Get or creates an ID sequence based on the sample year and species
        """
        if not sample.genlab_id:
            error_text = "Cannot replicate a sample without genlab id"
            raise ValueError(error_text)
        if not sample.order or not sample.order.confirmed_at:
            error_text = "Cannot replicate a sample without a confirmed order"
            raise ValueError(error_text)
        s = self.select_for_update() if lock else self

        sequence_id, _ = s.get_or_create(
            year=sample.order.confirmed_at.year,
            species=sample.species,
            sample=sample,
            defaults={"id": f"{sample.genlab_id}-", "last_value": 1},
        )
        return sequence_id
