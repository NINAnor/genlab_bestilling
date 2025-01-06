from typing import Self

from apps.users.models import User
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from genlab_bestilling.libs.load_csv_fixture import (
    sample_types_from_tsv,
    species_from_tsv,
)


class Command(BaseCommand):
    def handle(self: Self, **options) -> None:
        if User.objects.all().first() is None:
            call_command("loaddata", "users.json")

        call_command("loaddata", "bestilling.json")
        call_command("loaddata", "locations.json")
        call_command("loaddata", "groups.json")
        call_command("loaddata", "nina.json")

        species_from_tsv(settings.SRC_DIR / "fixtures" / "species.tsv")
        sample_types_from_tsv(settings.SRC_DIR / "fixtures" / "sample_types.tsv")

        call_command("loaddata", "test.json")
