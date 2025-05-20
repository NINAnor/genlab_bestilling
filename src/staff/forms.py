from django.forms import ModelForm
from genlab_bestilling.models import ExtractionPlate


class ExtractionPlateForm(ModelForm):
    class Meta:
        model = ExtractionPlate
        fields = ("name",)
