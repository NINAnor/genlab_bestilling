from dal import autocomplete
from django.db.models import QuerySet

from .models import User


class UserAutocomplete(autocomplete.Select2QuerySetView):
    model = User
    search_fields = ["email", "first_name", "last_name"]


class StaffUserAutocomplete(autocomplete.Select2QuerySetView):
    model = User
    search_fields = ["email", "first_name", "last_name"]

    def get_queryset(self) -> "QuerySet":
        if not self.request.user.is_authenticated:
            return User.objects.none()

        return User.objects.filter(groups__name="genlab")
