from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import AnalysisType, Area, EquipmentType, Marker, SampleType, Species


@admin.register(Area)
class AreaAdmin(ModelAdmin):
    pass


@admin.register(Marker)
class MarkerAdmin(ModelAdmin):
    pass


@admin.register(Species)
class SpeciesAdmin(ModelAdmin):
    pass


@admin.register(SampleType)
class SampleTypeAdmin(ModelAdmin):
    pass


@admin.register(AnalysisType)
class AnalysisTypeAdmin(ModelAdmin):
    pass


@admin.register(EquipmentType)
class EquipmentTypeAdmin(ModelAdmin):
    pass
