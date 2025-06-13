from dal import autocomplete

from .models import User


class UserAutocomplete(autocomplete.Select2QuerySetView):
    model = User
    search_fields = ["email", "first_name", "last_name"]
