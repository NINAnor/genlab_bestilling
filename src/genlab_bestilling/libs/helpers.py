ROWS = "ABCDEFGH"
COLUMNS = 12


def position_to_coordinates(index: int) -> str:
    """
    return the plate coordinate of a certain index
    """
    row_label = ROWS[index // COLUMNS]
    column_label = (index % COLUMNS) + 1
    return f"{row_label}{column_label}"
