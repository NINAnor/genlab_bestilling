# Generated by Django 5.1.4 on 2025-01-15 10:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("genlab_bestilling", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="analysisresult",
            name="order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="genlab_bestilling.analysisorder",
            ),
        ),
        migrations.AlterField(
            model_name="species",
            name="markers",
            field=models.ManyToManyField(
                related_name="species", to="genlab_bestilling.marker"
            ),
        ),
    ]
