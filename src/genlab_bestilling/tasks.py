from procrastinate.contrib.django import app

from .libs.genlabid import generate as generate_genlab_id


@app.task(name="generate-genlab-ids")
def generate_ids(order_id):
    generate_genlab_id(order_id)
