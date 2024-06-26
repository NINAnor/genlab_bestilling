from rest_framework.viewsets import ModelViewSet

from ..filters import SampleFilter
from ..models import Sample
from .serializers import SampleSerializer


class SampleViewset(ModelViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    filterset_class = SampleFilter
