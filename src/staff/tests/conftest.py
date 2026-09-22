"""Re-export shared fixtures from `genlab_bestilling.tests.conftest`.

`extraction` (and its `genlab_setup` dependency) are defined there but not
visible outside that app's own `tests/` directory, since pytest only
auto-discovers fixtures from `conftest.py` files in the current directory
and its ancestors. Import and re-export them here so `staff/tests/` can use
the same fixtures instead of duplicating fixture setup.
"""

from genlab_bestilling.tests.conftest import extraction, genlab_setup

__all__ = ["extraction", "genlab_setup"]
