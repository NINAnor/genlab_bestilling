from django.forms import ModelForm

from ..models import ExtractionPlate


class ExtractionPlateForm(ModelForm):
    class Meta:
        model = ExtractionPlate
        fields = ("name",)
