from django.contrib.postgres.fields.ranges import DateRangeField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel
from taggit.managers import TaggableManager


class Organization(models.Model):
    name = models.CharField(max_length=255)

    # TODO: unique name
    def __str__(self) -> str:
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=255)

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


class Location(models.Model):
    name = models.CharField(max_length=250)
    river_id = models.CharField(max_length=250)
    station_id = models.CharField(max_length=20)


class Project(models.Model):
    """
    A GenLab project, multiple GenLab projects can have the same NINA project code
    """

    name = models.CharField(max_length=255, null=True, blank=True)
    # external projects without project code? how to handle them?
    number = models.BigIntegerField(verbose_name=_("Project number"))
    verified = models.BooleanField(default=False)
    samples_owner = models.ForeignKey(
        "Organization", on_delete=models.PROTECT, blank=True, null=True
    )
    area = models.ForeignKey("Area", on_delete=models.PROTECT)
    species = models.ManyToManyField("Species", blank=True, related_name="projects")
    sample_types = models.ManyToManyField("SampleType", blank=True)
    analysis_types = models.ManyToManyField("AnalysisType", blank=True)
    expected_total_samples = models.IntegerField(null=True, blank=True)
    analysis_timerange = DateRangeField(null=True, blank=True)

    def __str__(self):
        return self.name

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
    use_guid = models.BooleanField()  # TODO: default?

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
    has_guid = models.BooleanField()  # TODO: default?
    isolate_samples = models.BooleanField()  # TODO: default?
    markers = models.ManyToManyField("Marker", blank=True, related_name="orders")
    return_samples = models.BooleanField()  # TODO: default?

    def get_absolute_url(self):
        return reverse(
            "project-analysis-detail",
            kwargs={"pk": self.pk, "project_id": self.project_id},
        )

    def confirm_order(self):
        if not self.samples.all().exists():
            raise Order.CannotConfirm(_("No samples found"))
        return super().confirm_order()


class Sample(models.Model):
    order = models.ForeignKey(
        "AnalysisOrder", on_delete=models.CASCADE, related_name="samples"
    )
    guid = models.CharField(max_length=200, null=True, blank=True)
    type = models.ForeignKey(
        "SampleType", on_delete=models.PROTECT, null=True, blank=True
    )
    species = models.ForeignKey("Species", on_delete=models.PROTECT)
    markers = models.ManyToManyField("Marker", blank=True)
    date = models.DateField()
    notes = models.TextField(null=True, blank=True)
    pop_id = models.CharField(max_length=150, null=True, blank=True)
    # area = models.ForeignKey("Area", on_delete=models.PROTECT)
    location = models.ForeignKey(
        "Location", on_delete=models.PROTECT, null=True, blank=True
    )
    volume = models.FloatField(null=True, blank=True)

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
