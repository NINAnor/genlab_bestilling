from dal import autocomplete

from .models import Project


class ProjectAutocomplete(autocomplete.Select2QuerySetView):
    model = Project
    search_fields = ["name", "number"]
