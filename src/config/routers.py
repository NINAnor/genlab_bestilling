from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from genlab_bestilling.api.views import (
    AnalysisTypeViewset,
    ExtractionOrderViewset,
    LocationViewset,
    MarkerViewset,
    SampleTypeViewset,
    SampleViewset,
    SpeciesViewset,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register("samples", SampleViewset, basename="samples")
router.register("species", SpeciesViewset, basename="species")
router.register("markers", MarkerViewset, basename="markers")
router.register("sample-types", SampleTypeViewset, basename="sample_types")
router.register("analysis-types", AnalysisTypeViewset, basename="analysis_types")
router.register("locations", LocationViewset, basename="locations")
router.register("extraction-order", ExtractionOrderViewset, basename="extraction-order")


urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
] + router.urls
