from django.contrib.postgres.fields.ranges import DateRangeField
from django.db import models
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel


class NINAProject(models.Model):
    """
    A NINA project, is unique, manages permissions
    """

    name = models.CharField(max_length=255, null=True, blank=True)
    id = models.BigIntegerField(primary_key=True, verbose_name=_("Project number"))


class Organization(models.Model):
    name = models.CharField(max_length=255)
    # TODO: unique name


class Area(models.Model):
    name = models.CharField(max_length=255)
    # TODO: unique name


class Marker(models.Model):
    name = models.CharField()
    # TODO: unique name


class Species(models.Model):
    # TODO: use IDs from Artsdatabanken?
    name = models.CharField(max_length=255)
    area = models.ForeignKey("Area", on_delete=models.CASCADE)
    markers = models.ManyToManyField("Marker")


# TODO: better understand "other" case. should the user be able to insert new orws?
# if yes, he may input a species that is already present
# at least the area of interest should be "fixed" or
#   species could have more than just one area of interest


class SampleType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)


class AnalysisType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)


class Location(models.Model):
    name = models.CharField(max_length=250)
    river_id = models.CharField(max_length=250)
    station_id = models.CharField(max_length=20)


class GenLabProject(models.Model):
    """
    A GenLab project, multiple GenLab projects can have the same NINA project code
    """

    name = models.CharField(max_length=255, null=True, blank=True)
    # external projects without project code? how to handle them?
    project = models.ForeignKey("NINAProject", on_delete=models.DO_NOTHING, null=True)
    verified = models.BooleanField(default=False)
    samples_owner = models.ForeignKey("Organization", on_delete=models.PROTECT)
    area = models.ForeignKey("Area", on_delete=models.PROTECT)
    species = models.ManyToManyField("Species")
    sample_types = models.ManyToManyField("SampleType")
    analysis_types = models.ManyToManyField("AnalysisType")
    expected_total_samples = models.IntegerField(null=True)
    analysis_timerange = DateRangeField(null=True, blank=True)


class Order(PolymorphicModel):
    project = models.ForeignKey("GenLabProject", on_delete=models.CASCADE)
    species = models.ManyToManyField("Species")
    sample_types = models.ManyToManyField("SampleType")
    notes = models.TextField()


class EquipmentType(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    unit = models.CharField(max_length=50)


class EquimentOrderQuantity(models.Model):
    equipment = models.ForeignKey("EquipmentType", on_delete=models.CASCADE)
    order = models.ForeignKey("EquipmentOrder", on_delete=models.CASCADE)
    quantity = models.DecimalField(decimal_places=4, max_digits=14)


class EquipmentOrder(Order):
    use_guid = models.BooleanField()  # TODO: default?


class AnalysisOrder(Order):
    has_guid = models.BooleanField()  # TODO: default?
    isolate_samples = models.BooleanField()  # TODO: default?
    markers = models.ManyToManyField("Marker", blank=True)
    return_samples = models.BooleanField()  # TODO: default?


class Sample(models.Model):
    order = models.ForeignKey("AnalysisOrder", on_delete=models.CASCADE)
    guid = models.CharField(max_length=200, null=True, blank=True)
    type = models.ForeignKey("SampleType", on_delete=models.PROTECT)
    species = models.ForeignKey("Species", on_delete=models.PROTECT)
    markers = models.ManyToManyField("Marker")
    date = models.DateField()
    notes = models.TextField()
    pop_id = models.CharField(max_length=150)
    area = models.ForeignKey("Area", on_delete=models.PROTECT)
    location = models.ForeignKey("Location", on_delete=models.PROTECT)
    volume = models.FloatField(null=True, blank=True)
