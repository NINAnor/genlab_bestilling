from django.contrib.postgres.fields.ranges import DateRangeField
from django.db import models, transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel
from rest_framework.exceptions import ValidationError
from taggit.managers import TaggableManager


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

    # TODO: unique name
    def __str__(self) -> str:
        return self.name


class Species(models.Model):
    # TODO: use IDs from Artsdatabanken?
    name = models.CharField(max_length=255)
    area = models.ForeignKey("Area", on_delete=models.CASCADE)
    markers = models.ManyToManyField("Marker")
    location_type = models.ForeignKey(
        "LocationType", null=True, blank=True, on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return self.name


# TODO: better understand "other" case. should the user be able to insert new orws?
# if yes, he may input a species that is already present
# at least the area of interest should be "fixed" or
#   species could have more than just one area of interest


class SampleType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class AnalysisType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class LocationType(models.Model):
    name = models.CharField(max_length=250)


class Location(models.Model):
    name = models.CharField(max_length=250)
    type = models.ForeignKey(
        "LocationType", null=True, blank=True, on_delete=models.CASCADE
    )
    river_id = models.CharField(max_length=250, null=True, blank=True)
    station_id = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        if self.river_id:
            return f"{self.river_id} {self.station_id} {self.name}"

        return self.name


class Project(models.Model):
    """
    A GenLab project, multiple GenLab projects can have the same NINA project code
    """

    name = models.CharField(max_length=255, null=True, blank=True)
    # external projects without project code? how to handle them?
    number = models.CharField(verbose_name=_("Project number"))
    verified = models.BooleanField(default=False)
    samples_owner = models.ForeignKey(
        "Organization", on_delete=models.PROTECT, blank=True, null=True
    )
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_owned",
    )
    creator = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects_created",
    )
    members = models.ManyToManyField(
        "users.User", blank=True, related_name="projects_member"
    )
    area = models.ForeignKey("Area", on_delete=models.PROTECT)
    species = models.ManyToManyField("Species", blank=True, related_name="projects")
    sample_types = models.ManyToManyField("SampleType", blank=True)
    analysis_types = models.ManyToManyField("AnalysisType", blank=True)
    expected_total_samples = models.IntegerField(null=True, blank=True)
    analysis_timerange = DateRangeField(null=True, blank=True)

    def __str__(self):
        return str(self.name or self.number)

    def get_absolute_url(self):
        return reverse(
            "project-detail",
            kwargs={"pk": self.pk},
        )


class Order(PolymorphicModel):
    class CannotConfirm(Exception):
        pass

    class OrderStatus(models.TextChoices):
        DRAFT = "draft", _("Draft")
        CONFIRMED = "confirmed", _("Confirmed")
        PROCESSING = "processing", _("Processing")
        COMPLETED = "completed", _("Completed")

    name = models.CharField(null=True, blank=True)
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="orders"
    )
    species = models.ManyToManyField("Species", related_name="orders")
    sample_types = models.ManyToManyField("SampleType", related_name="orders")
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(default=OrderStatus.DRAFT, choices=OrderStatus)

    tags = TaggableManager(blank=True)

    def confirm_order(self):
        self.status = Order.OrderStatus.CONFIRMED
        self.save()


class EquipmentType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    unit = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class EquimentOrderQuantity(models.Model):
    equipment = models.ForeignKey(
        "EquipmentType", on_delete=models.CASCADE, related_name="orders"
    )
    order = models.ForeignKey(
        "EquipmentOrder", on_delete=models.CASCADE, related_name="equipments"
    )
    quantity = models.DecimalField(decimal_places=4, max_digits=14)


class EquipmentOrder(Order):
    needs_guid = models.BooleanField()  # TODO: default?

    def get_absolute_url(self):
        return reverse(
            "project-equipment-detail",
            kwargs={"pk": self.pk, "project_id": self.project_id},
        )

    def confirm_order(self):
        if not EquimentOrderQuantity.objects.filter(order=self).exists():
            raise Order.CannotConfirm(_("No equipments found"))
        return super().confirm_order()


class AnalysisOrder(Order):
    needs_guid = models.BooleanField(default=False)  # TODO: default?
    isolate_samples = models.BooleanField()  # TODO: default?
    markers = models.ManyToManyField("Marker", blank=True, related_name="orders")
    return_samples = models.BooleanField()  # TODO: default?

    def get_absolute_url(self):
        return reverse(
            "project-analysis-detail",
            kwargs={"pk": self.pk, "project_id": self.project_id},
        )

    def confirm_order(self):
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
                raise ValidationError(f"Found {invalid} invalid or incompleted samples")

            return super().confirm_order()


class Sample(models.Model):
    order = models.ForeignKey(
        "AnalysisOrder", on_delete=models.CASCADE, related_name="samples"
    )
    guid = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(null=True, blank=True)
    type = models.ForeignKey(
        "SampleType", on_delete=models.PROTECT, null=True, blank=True
    )
    species = models.ForeignKey("Species", on_delete=models.PROTECT)
    markers = models.ManyToManyField("Marker", blank=True)
    date = models.DateField()
    notes = models.TextField(null=True, blank=True)
    pop_id = models.CharField(max_length=150, null=True, blank=True)
    location = models.ForeignKey(
        "Location", on_delete=models.PROTECT, null=True, blank=True
    )
    volume = models.FloatField(null=True, blank=True)

    @property
    def has_error(self):
        if not all(
            [
                self.name,
                self.type,
                self.guid,
                self.species,
                self.date,
            ]
        ):
            raise ValidationError(
                "GUID, Name, Sample Type, Species and Date are required"
            )

        if (
            self.species.location_type
            and self.species.location_type_id == self.location.type_id
        ):
            # Check if the selected species has a specific location type
            raise ValidationError("Location is required")
        elif self.order.project.area.location_mandatory:
            # Check if the project area requires a location
            raise ValidationError("Location is required")
        else:
            return False

    # plate
    # coordinates on plate


# class Analysis(models.Model):
# type =
# sample =
# plate
# coordinates on plate
# result
# status
# assignee (one or plus?)
