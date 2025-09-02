import re


def bird_id(genlab_id: str | None) -> str | None:
    if not genlab_id:
        return None

    exp = re.compile(r"^G\d{2}([A-Z]{1,3})0*(\d+)(-\d+)?")

    match = exp.match(genlab_id)
    species_code = match.group(1)
    running_number = match.group(2)
    replica = match.group(3) if match.group(3) else ""
    return species_code + running_number + replica
