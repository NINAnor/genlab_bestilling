import re

_MILJODNA_ID_RE = re.compile(r"^G(\d{2})[A-Z]+(.+)$")


def miljodna_id(pop_id: str | None, genlab_id: str | None) -> str | None:
    """
    Generate a miljoDNA ID synonym for a sample.

    Format: {pop_id_segment}_{year_segment}_{genlab_id_segment}
    - pop_id_segment: the first 5 characters of pop_id, as stored.
    - year_segment: the last two digits of the year, parsed from genlab_id.
    - genlab_id_segment: genlab_id with its leading G{YY}{species_code}
      prefix stripped, kept unmodified (including any replicate suffix).

    Example: if pop_id is 'MELFJ' and genlab_id is 'G26ABC01413', returns
    'MELFJ_26_01413'.
    """
    if not pop_id or not genlab_id:
        return None

    match = _MILJODNA_ID_RE.match(genlab_id)
    if not match:
        return None

    pop_id_segment = pop_id[:5]
    year_segment = match.group(1)
    genlab_id_segment = match.group(2)

    return f"{pop_id_segment}_{year_segment}_{genlab_id_segment}"
