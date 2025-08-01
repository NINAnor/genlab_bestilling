from typing import Self

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from capps.users.models import User
from genlab_bestilling.libs.load_csv_fixture import (
    sample_types_from_tsv,
    species_from_tsv,
)
from genlab_bestilling.models import Area, IsolationMethod


class Command(BaseCommand):
    def handle(self: Self, **options) -> None:
        if not Area.objects.all().exists():
            call_command("loaddata", "bestilling.json")
            call_command("loaddata", "locations.json")
            call_command("loaddata", "groups.json")

        if User.objects.all().first() is None:
            call_command("loaddata", "users.json")

        if not Area.objects.all().exists():
            call_command("loaddata", "nina.json")

            species_from_tsv(settings.SRC_DIR / "fixtures" / "species.tsv")
            sample_types_from_tsv(settings.SRC_DIR / "fixtures" / "sample_types.tsv")

            call_command("loaddata", "test.json")

        if not IsolationMethod.objects.all().exists():
            call_command("loaddata", "isolation_methods.json")
