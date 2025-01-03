from django.contrib.postgres.fields.ranges import DateRangeField
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel
from procrastinate.contrib.django import app
from rest_framework.exceptions import ValidationError
from taggit.managers import TaggableManager

from . import managers
from .libs.helpers import position_to_coordinates


class Organization(models.Model):
    name = models.CharField(max_length=255)

    # TODO: unique name
    def __str__(self) -> str:
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=255)
    location_mandatory = models.BooleanField(default=False)

    # TODO: unique name
    def __str__(self) -> str:
        return self.name


class Marker(models.Model):
    name = models.CharField(primary_key=True)
    analysis_type = models.ForeignKey("AnalysisType", on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return self.name


class Species(models.Model):
    name = models.CharField(max_length=255)
    area = models.ForeignKey("Area", on_delete=models.CASCADE)
    markers = models.ManyToManyField("Marker")
    location_type = models.ForeignKey(
        "LocationType", null=True, blank=True, on_delete=models.CASCADE
    )
    code = models.CharField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = "Species"
        constraints = [
            models.UniqueConstraint(name="unique species code", fields=["code"])
        ]


class SampleType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    areas = models.ManyToManyField("Area", blank=True)

    def __str__(self) -> str:
        return self.name


class AnalysisType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class LocationType(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self) -> str:
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=250)
    type = models.ForeignKey(
        "LocationType", null=True, blank=True, on_delete=models.CASCADE
    )
    river_id = models.CharField(max_length=250, null=True, blank=True)
    code = models.CharField(max_length=20, null=True, blank=True)
    fylke = models.CharField(null=True, blank=True)

    def __str__(self):
        if self.river_id:
            return f"{self.river_id} {self.name}"

        return self.name


class Genrequest(models.Model):
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
        "Organization",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="genrequests_created",
    )
    area = models.ForeignKey("Area", on_delete=models.PROTECT)
    species = models.ManyToManyField("Species", blank=True, related_name="genrequests")
    sample_types = models.ManyToManyField(
        "SampleType",
        blank=True,
        help_text="samples you plan to deliver, you can choose more than one. "
        + "ONLY sample types selected here will be available later",
    )
    markers = models.ManyToManyField("Marker", blank=True)
    analysis_timerange = DateRangeField(
        null=True,
        blank=True,
        help_text="This helps the Lab estimating the workload, "
        + "provide the timeframe for the analysis",
    )
    expected_total_samples = models.IntegerField(
        null=True,
        blank=True,
        help_text="This helps the Lab estimating the workload, "
        + "provide how many samples you're going to deliver",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    objects = managers.GenrequestQuerySet.as_manager()
    tags = TaggableManager(blank=True)

    def __str__(self):
        return f"#GEN_{self.id}"

    def get_absolute_url(self):
        return reverse(
            "genrequest-detail",
            kwargs={"pk": self.pk},
        )

    class Meta:
        verbose_name = "Genetic Request"


class Order(PolymorphicModel):
    class CannotConfirm(ValidationError):
        pass

    class OrderStatus(models.TextChoices):
        DRAFT = "draft", _("Draft")
        CONFIRMED = "confirmed", _("Confirmed")
        PROCESSING = "processing", _("Processing")
        COMPLETED = "completed", _("Completed")

    name = models.CharField(null=True, blank=True)
    genrequest = models.ForeignKey(
        "Genrequest", on_delete=models.CASCADE, related_name="orders"
    )
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(default=OrderStatus.DRAFT, choices=OrderStatus)
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    tags = TaggableManager(blank=True)
    objects = managers.OrderManager()

    def confirm_order(self):
        self.status = Order.OrderStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.save()

    def clone(self):
        self.id = None
        self.pk = None
        self.status = self.OrderStatus.DRAFT
        self.save()

    def to_draft(self):
        self.status = Order.OrderStatus.DRAFT
        self.confirmed_at = None
        self.save()

    def get_type(self):
        return "order"

    def __str__(self):
        return f"#ORD_{self.id}"


class EquipmentType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    unit = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f"{self.name} ({self.unit})" if self.unit else self.name


class EquimentOrderQuantity(models.Model):
    equipment = models.ForeignKey(
        "EquipmentType", on_delete=models.CASCADE, related_name="orders"
    )
    order = models.ForeignKey(
        "EquipmentOrder", on_delete=models.CASCADE, related_name="equipments"
    )
    quantity = models.DecimalField(decimal_places=4, max_digits=14)

    objects = managers.EquipmentOrderQuantityQuerySet.as_manager()


class EquipmentOrder(Order):
    needs_guid = models.BooleanField()  # TODO: default?
    sample_types = models.ManyToManyField("SampleType", blank=True)

    def __str__(self) -> str:
        return f"#EQP_{self.id}"

    def get_absolute_url(self):
        return reverse(
            "genrequest-equipment-detail",
            kwargs={"pk": self.pk, "genrequest_id": self.genrequest_id},
        )

    def confirm_order(self):
        if not EquimentOrderQuantity.objects.filter(order=self).exists():
            raise Order.CannotConfirm(_("No equipments found"))
        return super().confirm_order()

    def get_type(self):
        return "equipment"


class ExtractionOrder(Order):
    class Status(models.TextChoices):
        TO_CHECK = "needs_check", _("Needs check")
        CHECKED = "checked", _("Checked")

    internal_status = models.CharField(default=Status.TO_CHECK, choices=Status)
    species = models.ManyToManyField("Species", blank=True)
    sample_types = models.ManyToManyField("SampleType", blank=True)
    needs_guid = models.BooleanField(default=False)  # TODO: default?
    return_samples = models.BooleanField()  # TODO: default?

    def __str__(self) -> str:
        return f"#EXT_{self.id}"

    def get_type(self):
        return "extraction"

    def get_absolute_url(self):
        return reverse(
            "genrequest-analysis-detail",
            kwargs={"pk": self.pk, "genrequest_id": self.genrequest_id},
        )

    def confirm_order(self, persist=True):
        with transaction.atomic():
            if not self.samples.all().exists():
                raise ValidationError(_("No samples found"))

            invalid = 0
            for sample in self.samples.all():
                try:
                    sample.has_error  # noqa: B018
                except ValidationError:
                    invalid += 1

            if invalid > 0:
                raise Order.CannotConfirm(
                    f"Found {invalid} invalid or incompleted samples"
                )

            if persist:
                super().confirm_order()

    def order_manually_checked(self):
        super().order_manually_checked()
        app.configure_task(name="generate-genlab-ids").defer(order_id=self.id)


class AnalysisOrder(Order):
    samples = models.ManyToManyField(
        "Sample", blank=True, through="SampleMarkerAnalysis"
    )

    def __str__(self) -> str:
        return f"#ANL_{self.id}"

    def get_absolute_url(self):
        return reverse(
            "genrequest-analysis-detail",
            kwargs={"pk": self.pk, "genrequest_id": self.genrequest_id},
        )

    def get_type(self):
        return "analysis"

    def confirm_order(self, persist=True):
        with transaction.atomic():
            if not self.samples.all().exists():
                raise ValidationError(_("No samples found"))

            if persist:
                super().confirm_order()


class SampleMarkerAnalysis(models.Model):
    sample = models.ForeignKey("Sample", on_delete=models.CASCADE)
    analysis = models.ForeignKey("AnalysisOrder", on_delete=models.CASCADE)
    markers = models.ManyToManyField("Marker", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sample", "analysis"], name="unique_sample_per_analysis"
            )
        ]


class Sample(models.Model):
    extraction_order = models.ForeignKey(
        "ExtractionOrder", on_delete=models.CASCADE, related_name="samples"
    )
    guid = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(null=True, blank=True)
    type = models.ForeignKey(
        "SampleType", on_delete=models.PROTECT, null=True, blank=True
    )
    species = models.ForeignKey("Species", on_delete=models.PROTECT)
    year = models.IntegerField()
    notes = models.TextField(null=True, blank=True)
    pop_id = models.CharField(max_length=150, null=True, blank=True)
    location = models.ForeignKey(
        "Location", on_delete=models.PROTECT, null=True, blank=True
    )
    volume = models.FloatField(null=True, blank=True)
    genlab_id = models.CharField(null=True, blank=True)

    extractions = models.ManyToManyField("ExtractionPlate", blank=True)
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)

    objects = managers.SampleQuerySet.as_manager()

    def __str__(self) -> str:
        return self.genlab_id or f"#SMP_{self.id}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["genlab_id"], name="unique_genlab_id")
        ]

    @property
    def has_error(self):
        if not all(
            [
                self.name,
                self.type,
                self.guid,
                self.species,
                self.year,
            ]
        ):
            raise ValidationError(
                "GUID, Sample Name, Sample Type, Species and Year are required"
            )

        if (
            self.species.location_type
            and self.species.location_type_id == self.location.type_id
        ):
            # Check if the selected species has a specific location type
            raise ValidationError("Location is required")
        elif self.order.genrequest.area.location_mandatory:
            # Check if the genrequest area requires a location
            raise ValidationError("Location is required")
        else:
            return False


# class Analysis(models.Model):
# type =
# sample =
# plate
# coordinates on plate
# result
# status
# assignee (one or plus?)


# Some extracts can be placed in multiple wells
class ExtractPlatePosition(models.Model):
    plate = models.ForeignKey(
        "ExtractionPlate", on_delete=models.DO_NOTHING, related_name="sample_positions"
    )
    sample = models.ForeignKey(
        "Sample",
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


class Analysis(models.Model):
    name = models.CharField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    analysis_date = models.DateTimeField(null=True, blank=True)
    marker = models.ForeignKey("Marker", on_delete=models.DO_NOTHING)
    result_file = models.FileField(null=True, blank=True)
    samples = models.ManyToManyField("Sample", blank=True)
    extra = models.JSONField(null=True, blank=True)
