ROWS = "ABCDEFGH"
COLUMNS = 12


def position_to_coordinates(index):
    row_label = ROWS[index // COLUMNS]
    column_label = (index % COLUMNS) + 1
    return f"{row_label}{column_label}"
