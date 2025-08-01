# Generated by Django 5.2.3 on 2025-07-22 13:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "genlab_bestilling",
            "0029_alter_order_contact_email_alter_order_contact_person",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="samplemarkeranalysis",
            name="has_pcr",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="samplemarkeranalysis",
            name="is_analysed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="samplemarkeranalysis",
            name="is_outputted",
            field=models.BooleanField(default=False),
        ),
    ]
