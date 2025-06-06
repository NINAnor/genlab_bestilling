import csv
import pathlib

from django.db import transaction

from ..models import AnalysisType, Area, Marker, SampleType, Species


def species_from_tsv(path: pathlib.Path):
    """
    read a TSV file and create Area, Species, Analysis Type and Markers dynamically
    """
    with path.open(mode="r") as csv_file:
        reader = csv.DictReader(csv_file, dialect="excel-tab")
        with transaction.atomic():
            created = 0
            for line in reader:
                area, c = Area.objects.get_or_create(name=line["Area"])
                created += int(c)
                species, c = Species.objects.get_or_create(
                    area=area, name=line["Species"], code=line["Code"]
                )
                created += int(c)
                analysis, _ = AnalysisType.objects.get_or_create(
                    name=line["Analysis method"]
                )
                created += int(c)
                marker, _ = Marker.objects.get_or_create(
                    name=line["Marker"], analysis_type=analysis
                )
                created += int(c)
                species.markers.add(marker)

        print(f"Installed {created} objects from {str(path)}")


def sample_types_from_tsv(path: pathlib.Path):
    """
    read a TSV file and create Area, SampleType dynamically
    """
    with path.open(mode="r") as csv_file:
        reader = csv.DictReader(csv_file, dialect="excel-tab")
        with transaction.atomic():
            created = 0
            for line in reader:
                area, c = Area.objects.get_or_create(name=line["Area"])
                created += int(c)
                sample_type, c = SampleType.objects.get_or_create(
                    name=line["Sample type"]
                )
                sample_type.areas.add(area)
                created += int(c)

        print(f"Installed {created} objects from {str(path)}")
