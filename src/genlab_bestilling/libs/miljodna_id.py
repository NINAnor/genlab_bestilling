def miljodna_id(
    pop_id: str | None,
    year: int | None,
    genlab_id: str | None,
    species_code: str | None,
) -> str | None:
    """
    Generate a miljoDNA ID synonym for a sample.

    Format: {pop_id_segment}_{year_segment}_{genlab_id_segment}
    Example: if pop_id is 'Melfjord', year is 2026 and genlab_id is
    'G26ABC01413', returns 'MELFJ_26_01413'
    """
    if not pop_id or not year or not genlab_id or not species_code:
        return None

    pop_id_segment = pop_id[:5]
    year_segment = str(year)[-2:]

    prefix_len = 1 + 2 + len(species_code)  # "G" + YY + species_code
    genlab_id_segment = genlab_id[prefix_len:]
    if not genlab_id_segment:
        return None

    return f"{pop_id_segment}_{year_segment}_{genlab_id_segment}"
