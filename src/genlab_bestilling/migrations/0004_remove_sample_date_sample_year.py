# Generated by Django 5.1.1 on 2024-09-10 12:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("genlab_bestilling", "0003_remove_sample_markers"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sample",
            name="date",
        ),
        migrations.AddField(
            model_name="sample",
            name="year",
            field=models.IntegerField(default=2024),
            preserve_default=False,
        ),
    ]
