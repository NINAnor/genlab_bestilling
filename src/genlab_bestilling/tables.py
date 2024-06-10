import django_tables2 as tables

from .models import Order


class OrderTable(tables.Table):
    class Meta:
        model = Order
        fields = ("name", "species", "sample_types")
