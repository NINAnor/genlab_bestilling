from django.db import connection


def assert_is_in_atomic_block() -> None:
    assert (  # noqa: S101
        connection.in_atomic_block
    ), "This function must be run inside of a DB transaction."
