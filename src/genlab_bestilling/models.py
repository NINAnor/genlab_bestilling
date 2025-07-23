import uuid
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel
from rest_framework.exceptions import ValidationError
from taggit.managers import TaggableManager

from shared.db import assert_is_in_atomic_block

from . import managers
from .libs.helpers import position_to_coordinates

an = "genlab_bestilling"  # Short alias for app name.


class Organization(models.Model):
    # TODO: unique name
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=255)
    location_mandatory = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    # TODO: unique name
    def __str__(self) -> str:
        return self.name


class Marker(models.Model):
    name = models.CharField(primary_key=True)
    analysis_type = models.ForeignKey(f"{an}.AnalysisType", on_delete=models.DO_NOTHING)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Species(models.Model):
    name = models.CharField(max_length=255)
    area = models.ForeignKey(f"{an}.Area", on_delete=models.CASCADE)
    markers = models.ManyToManyField(f"{an}.Marker", related_name="species")
    location_type = models.ForeignKey(
        f"{an}.LocationType",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="species",
    )
    code = models.CharField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Species"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(name="unique species code", fields=["code"])
        ]

    def __str__(self) -> str:
        return self.name


class SampleType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    areas = models.ManyToManyField(f"{an}.Area", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name or ""

    @property
    def konciv_id(self) -> str:
        return f"ST_{self.id}"

    @property
    def konciv_type(self) -> str:
        return "SAMPLE_TYPE"


class AnalysisType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name or ""

    @property
    def konciv_id(self) -> str:
        return f"AT_{self.id}"

    @property
    def konciv_type(self) -> str:
        return "ANALYSIS_TYPE"


class LocationType(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self) -> str:
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=250)
    types = models.ManyToManyField(
        f"{an}.LocationType",
        blank=True,
    )
    river_id = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        unique=True,
        help_text="Unique river ID. If the id is taken, a dotted suffix can be utilised. This could be useful for sub locations within the main river. For example, if the main river ID is '1234', a sub location can be '1234.2'.",  # noqa: E501
    )
    code = models.CharField(max_length=20, null=True, blank=True)
    fylke = models.CharField(null=True, blank=True)
    comment = models.TextField(
        null=False,
        blank=True,
        default="",
        help_text="This field can be used to store additional information about the location, such as the species in focus or other relevant details.",  # noqa: E501
    )

    def __str__(self):
        if self.river_id:
            return f"{self.river_id} {self.name}"

        return self.name


class Genrequest(models.Model):  # type: ignore[django-manager-missing]
    """
    A GenLab genrequest, multiple GenLab requests can have the same NINA project number
    """

    name = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Description"
    )
    project = models.ForeignKey(
        "nina.Project",
        on_delete=models.PROTECT,
        verbose_name="UBW Project Name",
        help_text="Choose the UBW NINA Project for billing",
    )
    samples_owner = models.ForeignKey(
        f"{an}.Organization",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="genrequests_created",
    )
    area = models.ForeignKey(f"{an}.Area", on_delete=models.PROTECT)
    expected_samples_delivery_date = models.DateField(
        help_text="When you plan to start delivering the samples"
    )
    expected_analysis_delivery_date = models.DateField(
        help_text="When you need to get the results"
    )
    expected_total_samples = models.IntegerField(
        null=True,
        blank=True,
        help_text="This helps the Lab estimating the workload, "
        "provide how many samples you're going to deliver",
    )
    species = models.ManyToManyField(
        f"{an}.Species", blank=True, related_name="genrequests"
    )
    sample_types = models.ManyToManyField(
        f"{an}.SampleType",
        blank=True,
        help_text="samples you plan to deliver, you can choose more than one. "
        "ONLY sample types selected here will be available later",
    )
    responsible_staff = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="responsible_genrequest",
        verbose_name="Responsible staff",
        help_text="Staff members responsible for this order",
        blank=True,
    )
    markers = models.ManyToManyField(f"{an}.Marker", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    objects = managers.GenrequestQuerySet.as_manager()
    tags = TaggableManager(blank=True)

    class Meta:
        verbose_name = "Genetic Project"

    def __str__(self):
        return f"#GEN_{self.id} ({self.project})"

    def get_absolute_url(self) -> str:
        return reverse(
            "genrequest-detail",
            kwargs={"pk": self.pk},
        )

    def display_id(self) -> str:
        return f"#GEN_{self.id}"

    def get_type(self) -> str:
        return "genrequest"

    @property
    def short_timeframe(self) -> bool:
        return (
            self.expected_analysis_delivery_date - self.expected_samples_delivery_date
        ) < timedelta(days=30)


class Order(PolymorphicModel):
    class CannotConfirm(ValidationError):
        pass

    class OrderStatus(models.TextChoices):
        # DRAFT: External researcher has created the order, and is currently working on it before having it delivered for processing.  # noqa: E501
        DRAFT = "draft", _("Draft")
        # DELIVERED: Order has been delivered from researcher to the NINA staff.
        # NOTE: # The old value `confirmed` was preserved during a name change to avoid migration issues. The primary goal is to have a more descriptive name for staff users in the GUI.  # noqa: E501
        DELIVERED = "confirmed", _("Delivered")
        # PROCESSING: NINA staff has begun processing the order.
        PROCESSING = "processing", _("Processing")
        # COMPLETED: Order has been completed, and results are available.
        COMPLETED = "completed", _("Completed")

    class OrderPriority:
        URGENT = 3
        PRIORITIZED = 2
        NORMAL = 1

    STATUS_ORDER = (
        OrderStatus.DRAFT,
        OrderStatus.DELIVERED,
        OrderStatus.PROCESSING,
        OrderStatus.COMPLETED,
    )

    name = models.CharField(null=True, blank=True)
    genrequest = models.ForeignKey(
        f"{an}.Genrequest",
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Genetic Project",
    )
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(default=OrderStatus.DRAFT, choices=OrderStatus)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    is_urgent = models.BooleanField(
        default=False, help_text="Check this box if the order is urgent"
    )
    contact_person = models.CharField(
        null=True,
        blank=False,
        help_text="Person to contact with questions about this order",
    )
    contact_email = models.EmailField(
        null=True,
        blank=False,
        help_text="Email to contact with questions about this order",
    )
    responsible_staff = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="responsible_orders",
        verbose_name="Responsible staff",
        help_text="Staff members responsible for this order",
        blank=True,
    )
    is_seen = models.BooleanField(
        default=False, help_text="If an order has been seen by a staff"
    )
    is_prioritized = models.BooleanField(
        default=False, help_text="If an order should be prioritized internally"
    )

    tags = TaggableManager(blank=True)
    objects = managers.OrderManager()

    def confirm_order(self) -> None:
        self.status = Order.OrderStatus.DELIVERED
        self.confirmed_at = timezone.now()
        if self.is_urgent:
            self.is_seen = True
        self.save()

    def clone(self) -> None:
        self.id = None
        self.pk = None
        self.status = self.OrderStatus.DRAFT
        self.confirmed_at = None
        self.save()

    def to_draft(self) -> None:
        self.status = Order.OrderStatus.DRAFT
        self.is_seen = False
        self.confirmed_at = None
        self.save()

    def to_processing(self) -> None:
        self.status = Order.OrderStatus.PROCESSING
        self.save()

    def toggle_seen(self) -> None:
        self.is_seen = not self.is_seen
        self.save()

    def toggle_prioritized(self) -> None:
        self.is_prioritized = not self.is_prioritized
        self.save()

    def get_type(self) -> str:
        return "order"

    @property
    def filled_genlab_count(self) -> int:
        return self.samples.filter(genlab_id__isnull=False).count()

    @property
    def next_status(self) -> OrderStatus | None:
        current_index = self.STATUS_ORDER.index(self.status)
        if current_index + 1 < len(self.STATUS_ORDER):
            return self.STATUS_ORDER[current_index + 1]
        return None

    def to_next_status(self) -> None:
        if status := self.next_status:
            self.status = status
            self.save()

    def __str__(self):
        return f"#ORD_{self.id}"


class EquipmentType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    unit = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.name} ({self.unit})" if self.unit else f"{self.name}"


class EquipmentBuffer(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    unit = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.name} ({self.unit or 'uL'})"


class EquimentOrderQuantity(models.Model):
    equipment = models.ForeignKey(
        f"{an}.EquipmentType",
        on_delete=models.CASCADE,
        related_name="orders",
        null=True,
        blank=True,
    )
    order = models.ForeignKey(
        f"{an}.EquipmentOrder",
        on_delete=models.CASCADE,
        related_name="equipments",
    )
    buffer = models.ForeignKey(
        f"{an}.EquipmentBuffer",
        on_delete=models.CASCADE,
        related_name="order_quantities",
        null=True,
        blank=True,
    )
    buffer_quantity = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        null=True,
        blank=True,
        help_text="How much buffer do you need? the value should be in uL",
        verbose_name="Buffer volume",
    )
    quantity = models.DecimalField(decimal_places=4, max_digits=14, default=1)

    objects = managers.EquipmentOrderQuantityQuerySet.as_manager()

    class Meta:
        verbose_name_plural = "Equipment order quantities"

    def __str__(self) -> str:
        return f"{self.quantity}"


class EquipmentOrder(Order):
    needs_guid = models.BooleanField()  # TODO: default?
    sample_types = models.ManyToManyField(f"{an}.SampleType", blank=True)

    def __str__(self) -> str:
        return f"#EQP_{self.id}"

    def get_absolute_url(self) -> str:
        return reverse(
            "genrequest-equipment-detail",
            kwargs={"pk": self.pk, "genrequest_id": self.genrequest_id},
        )

    def get_absolute_staff_url(self) -> str:
        return reverse("staff:order-equipment-detail", kwargs={"pk": self.pk})

    def confirm_order(self) -> Any:
        if not EquimentOrderQuantity.objects.filter(order=self).exists():
            raise Order.CannotConfirm(_("No equipments found"))
        return super().confirm_order()

    def get_type(self) -> str:
        return "equipment"

    def clone(self) -> None:
        sample_types = self.sample_types.all()
        super().clone()
        self.sample_types.add(*sample_types)


class ExtractionOrder(Order):
    class Status(models.TextChoices):
        TO_CHECK = "needs_check", _("Needs check")
        CHECKED = "checked", _("Checked")

    internal_status = models.CharField(default=Status.TO_CHECK, choices=Status)
    species = models.ManyToManyField(f"{an}.Species")
    sample_types = models.ManyToManyField(f"{an}.SampleType")
    needs_guid = models.BooleanField(default=False)  # TODO: default?
    return_samples = models.BooleanField()  # TODO: default?
    pre_isolated = models.BooleanField(verbose_name="Are samples already isolated?")

    def __str__(self) -> str:
        return f"#EXT_{self.id}"

    def get_type(self) -> str:
        return "extraction"

    def get_absolute_url(self) -> str:
        return reverse(
            "genrequest-extraction-detail",
            kwargs={"pk": self.pk, "genrequest_id": self.genrequest_id},
        )

    def get_absolute_staff_url(self) -> str:
        return reverse("staff:order-extraction-detail", kwargs={"pk": self.pk})

    def clone(self) -> None:
        """
        Generates a clone of the model, with a different ID
        """
        species = self.species.all()
        sample_types = self.sample_types.all()

        super().clone()

        self.species.add(*species)
        self.sample_types.add(*sample_types)

    def confirm_order(self, persist: bool = True) -> None:
        with transaction.atomic():
            if not self.samples.all().exists():
                raise ValidationError(_("No samples found"))

            invalid = 0
            for sample in self.samples.all():
                try:
                    sample.has_error  # noqa: B018
                except ValidationError:  # noqa: PERF203
                    invalid += 1

            if invalid > 0:
                msg = f"Found {invalid} invalid or incompleted samples"
                raise Order.CannotConfirm(msg)

            if persist:
                super().confirm_order()

    @transaction.atomic
    def order_selected_checked(
        self,
        selected_samples: list[int] | None = None,
    ) -> None:
        """
        Partially set the order as checked by the lab staff,
        generate a genlab id for the samples selected
        """
        self.internal_status = self.Status.CHECKED
        self.status = self.OrderStatus.PROCESSING
        self.save(update_fields=["internal_status", "status"])

        if not selected_samples:
            return

        Sample.objects.generate_genlab_ids(
            order_id=self.id,
            selected_samples=selected_samples,
        )


class AnalysisOrder(Order):
    samples = models.ManyToManyField(
        f"{an}.Sample", blank=True, through="SampleMarkerAnalysis"
    )
    markers = models.ManyToManyField(f"{an}.Marker", blank=True)
    from_order = models.ForeignKey(
        f"{an}.ExtractionOrder",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="analysis_orders",
        verbose_name="Use samples extracted in the following order",
    )
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Requested analysis result deadline",
        help_text="When you need to get the results",
    )

    @property
    def short_timeframe(self) -> bool:
        if not self.expected_delivery_date:
            return False
        return (self.expected_delivery_date - self.created_at.date()) < timedelta(
            days=30
        )

    def __str__(self) -> str:
        return f"#ANL_{self.id}"

    def get_absolute_url(self) -> str:
        return reverse(
            "genrequest-analysis-detail",
            kwargs={"pk": self.pk, "genrequest_id": self.genrequest_id},
        )

    def get_absolute_staff_url(self) -> str:
        return reverse("staff:order-analysis-detail", kwargs={"pk": self.pk})

    def get_type(self) -> str:
        return "analysis"

    def confirm_order(self, persist: bool = True) -> None:
        with transaction.atomic():
            if not self.samples.all().exists():
                raise ValidationError(_("No samples found"))

            if persist:
                super().confirm_order()

    def populate_from_order(self) -> None:
        """
        Create the list of markers per sample to analyze
        based on a previous extraction order
        """
        if not self.from_order_id:
            return

        with transaction.atomic():
            transaction_code = uuid.uuid4()

            for marker in self.markers.all():
                for sample in self.from_order.samples.filter(
                    species__in=marker.species.all()
                ):
                    SampleMarkerAnalysis.objects.update_or_create(
                        sample=sample,
                        order=self,
                        marker=marker,
                        defaults={"transaction": transaction_code},
                    )

            # delete samples that are not generated in this transaction
            self.sample_markers.exclude(transaction=transaction_code).delete()


class SampleMarkerAnalysis(models.Model):
    sample = models.ForeignKey(f"{an}.Sample", on_delete=models.CASCADE)
    order = models.ForeignKey(
        f"{an}.AnalysisOrder",
        on_delete=models.CASCADE,
        related_name="sample_markers",
    )
    marker = models.ForeignKey(f"{an}.Marker", on_delete=models.PROTECT)
    transaction = models.UUIDField(blank=True, null=True)

    # Fields for status tracking
    has_pcr = models.BooleanField(default=False)
    is_analysed = models.BooleanField(default=False)
    is_outputted = models.BooleanField(default=False)

    objects = managers.SampleAnalysisMarkerQuerySet.as_manager()

    class Meta:
        verbose_name_plural = "Sample marker analyses"
        constraints = [
            models.UniqueConstraint(
                fields=["sample", "order", "marker"],
                name="unique_sample_per_analysis",
            )
        ]

    def __str__(self):
        return f"{str(self.sample)} {str(self.marker)} @ {str(self.order)}"


class Sample(models.Model):
    order = models.ForeignKey(
        f"{an}.ExtractionOrder",
        on_delete=models.CASCADE,
        related_name="samples",
        null=True,
        blank=True,
    )
    guid = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(null=True, blank=True)
    type = models.ForeignKey(
        f"{an}.SampleType", on_delete=models.PROTECT, null=True, blank=True
    )
    species = models.ForeignKey(f"{an}.Species", on_delete=models.PROTECT)
    year = models.IntegerField()
    notes = models.TextField(null=True, blank=True)

    is_marked = models.BooleanField(default=False)
    is_plucked = models.BooleanField(default=False)
    is_isolated = models.BooleanField(default=False)

    # "Merknad" in the Excel sheet.
    internal_note = models.TextField(null=True, blank=True)
    pop_id = models.CharField(max_length=150, null=True, blank=True)
    location = models.ForeignKey(
        f"{an}.Location", on_delete=models.PROTECT, null=True, blank=True
    )
    volume = models.FloatField(null=True, blank=True)
    genlab_id = models.CharField(null=True, blank=True)

    extractions = models.ManyToManyField(f"{an}.ExtractionPlate", blank=True)
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)

    isolation_method = models.ManyToManyField(
        f"{an}.IsolationMethod",
        related_name="samples",
        through=f"{an}.SampleIsolationMethod",
        blank=True,
        help_text="The isolation method used for this sample",
    )

    is_prioritised = models.BooleanField(
        default=False,
        help_text="Check this box if the sample is prioritised for processing",
    )
    objects = managers.SampleQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["genlab_id"], name="unique_genlab_id")
        ]

    def __str__(self) -> str:
        return self.genlab_id or f"#SMP_{self.id}"

    def create_replica(self) -> None:
        pk = self.id
        self.id = None
        self.genlab_id = None
        self.parent_id = pk
        self.save()

    @property
    def fish_id(self) -> str | None:
        """
        Generate a unique fish ID for the sample.

        NOTE:
        Only relevant for aquatic projects.
        This function does not check if the sample is connected to an aquatic project
        to prevent unnecessary database queries.
        It is the responsibility of the caller to ensure that this is the case.
        """
        if not (self.location and self.location.code and self.name and self.year):
            return None
        format_year = str(self.year)[-2:]  # Get the last two digits.
        format_name = str(self.name).zfill(4)  # Fill from left with zeros.
        return f"{self.location.code}_{format_year}_{format_name}"

    @property
    def has_error(self) -> bool:
        """
        Check if all the fields are filled correctly depending on several factors.

        NOTE:
        This cannot be done inside a clean_ method because each sample is always
        a valid row in the database, but in certain contexts it might be invalid.
        """
        if not all(
            [
                self.name,
                self.type,
                self.guid,
                self.species,
                self.year,
            ]
        ):
            msg = "GUID, Sample Name, Sample Type, Species and Year are required"
            raise ValidationError(msg)

        if self.order.genrequest.area.location_mandatory:  # type: ignore[union-attr] # FIXME: Order can be None.
            if not self.location_id:
                msg = "Location is required"
                raise ValidationError(msg)
            # ensure that location is correct for the selected species
            if (
                self.species.location_type
                and self.species.location_type_id
                not in self.location.types.values_list("id", flat=True)  # type: ignore[union-attr] # FIXME: Order can be None.
            ):
                msg = "Invalid location for the selected species"
                raise ValidationError(msg)
        elif self.location_id and self.species.location_type_id:
            # if the location is optional, but it's provided,
            # check it is compatible with the species
            if self.species.location_type_id not in self.location.types.values_list(
                "id", flat=True
            ):
                msg = "Selected location not compatible with the selected species"
                raise ValidationError(msg)

        return False

    def generate_genlab_id(self, commit: bool = True) -> str:
        assert_is_in_atomic_block()

        if self.genlab_id:
            return self.genlab_id
        species = self.species
        year = self.order.confirmed_at.year

        sequence = GIDSequence.objects.get_sequence_for_species_year(
            year=year, species=species, lock=True
        )
        self.genlab_id = sequence.next_value()

        if commit:
            self.save(update_fields=["genlab_id"])

        return self.genlab_id


# class Analysis(models.Model):
# type =
# sample =
# plate
# coordinates on plate
# result
# status
# assignee (one or plus?)


class SampleIsolationMethod(models.Model):
    sample = models.ForeignKey(
        f"{an}.Sample",
        on_delete=models.CASCADE,
        related_name="isolation_methods",
    )
    isolation_method = models.ForeignKey(
        f"{an}.IsolationMethod",
        on_delete=models.CASCADE,
        related_name="sample_isolation_methods",
    )

    class Meta:
        unique_together = ("sample", "isolation_method")

    def __str__(self) -> str:
        return f"{self.sample} - {self.isolation_method}"


class IsolationMethod(models.Model):
    name = models.CharField(max_length=255, unique=False)
    species = models.ForeignKey(
        f"{an}.Species",
        on_delete=models.CASCADE,
        related_name="species_isolation_methods",
        help_text="The species this isolation method is related to.",
        default=None,
    )

    def __str__(self) -> str:
        return self.name


# Some extracts can be placed in multiple wells
class ExtractPlatePosition(models.Model):
    plate = models.ForeignKey(
        f"{an}.ExtractionPlate",
        on_delete=models.DO_NOTHING,
        related_name="sample_positions",
    )
    sample = models.ForeignKey(
        f"{an}.Sample",
        on_delete=models.PROTECT,
        related_name="plate_positions",
        null=True,
        blank=True,
    )
    position = models.IntegerField()
    extracted_at = models.DateTimeField(auto_now=True)
    notes = models.CharField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plate", "position"], name="unique_positions_in_plate"
            )
        ]

    def __str__(self) -> str:
        return f"#Q{self.plate_id}@{position_to_coordinates(self.position)}"


class ExtractionPlate(models.Model):
    name = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    # freezer
    # shelf

    def __str__(self):
        return f"#P{self.id}" + f" - {self.name}" if self.name else ""


class AnalysisResult(models.Model):
    name = models.CharField()
    analysis_date = models.DateTimeField(null=True, blank=True)
    marker = models.ForeignKey(f"{an}.Marker", on_delete=models.DO_NOTHING)
    order = models.ForeignKey(
        f"{an}.AnalysisOrder",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    result_file = models.FileField(null=True, blank=True)
    samples = models.ManyToManyField(f"{an}.Sample", blank=True)
    extra = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name}"


class GIDSequence(models.Model):
    """
    Represents a sequence of IDs
    This table provides a way to atomically update
    the counter of each combination of (species, year)

    NOTE: this replaces the usage of postgres sequences,
        while probably slower, this table can be atomically updated
    """

    id = models.CharField(primary_key=True)
    last_value = models.IntegerField(default=0)
    year = models.IntegerField()
    species = models.ForeignKey(
        f"{an}.Species", on_delete=models.PROTECT, db_constraint=False
    )
    sample = models.OneToOneField(
        f"{an}.Sample",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="replica_sequence",
    )

    objects = managers.GIDSequenceQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="unique_id_year_species", fields=["year", "species"]
            ),
        ]

    def __str__(self):
        return f"{self.id}@{self.last_value}"

    def next_value(self) -> str:
        """
        Update the last_value transactionally and return the corresponding genlab_id
        """
        assert_is_in_atomic_block()
        self.last_value += 1
        self.save(update_fields=["last_value"])
        return f"{self.id}{self.last_value:05d}"
