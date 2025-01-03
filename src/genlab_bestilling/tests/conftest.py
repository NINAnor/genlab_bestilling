import os

import pytest

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture(scope="session")
def live_server_url():
    return os.environ.get("LIVE_SERVER_URL")
