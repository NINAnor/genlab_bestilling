# from .libs.isolation import isolate
from django.db.utils import OperationalError
from procrastinate import RetryStrategy
from procrastinate.contrib.django import app

from .libs.genlabid import generate as generate_genlab_id


@app.task(
    name="generate-genlab-ids",
    retry=RetryStrategy(
        max_attempts=5, linear_wait=5, retry_exceptions={OperationalError}
    ),
)
def generate_ids(order_id):
    generate_genlab_id(order_id=order_id)
    # isolate(order_id=order_id)
