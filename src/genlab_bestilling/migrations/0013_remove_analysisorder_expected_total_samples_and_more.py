# Generated by Django 5.1.3 on 2024-12-13 08:23

import django.contrib.postgres.fields.ranges
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("genlab_bestilling", "0012_sample_unique_genlab_id"),
        ("nina", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="analysisorder",
            name="expected_total_samples",
        ),
        migrations.AddField(
            model_name="genrequest",
            name="expected_total_samples",
            field=models.IntegerField(
                blank=True,
                help_text="This helps the Lab estimating the workload, provide how many samples you're going to deliver",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="genrequest",
            name="analysis_timerange",
            field=django.contrib.postgres.fields.ranges.DateRangeField(
                blank=True,
                help_text="This helps the Lab estimating the workload, provide the timeframe for the analysis",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="genrequest",
            name="name",
            field=models.CharField(
                blank=True, max_length=255, null=True, verbose_name="Description"
            ),
        ),
        migrations.AlterField(
            model_name="genrequest",
            name="project",
            field=models.ForeignKey(
                help_text="Choose the UBW NINA Project for billing",
                on_delete=django.db.models.deletion.PROTECT,
                to="nina.project",
                verbose_name="UBW Project Name",
            ),
        ),
        migrations.AlterField(
            model_name="genrequest",
            name="sample_types",
            field=models.ManyToManyField(
                blank=True,
                help_text="samples you plan to deliver, you can choose more than one. ONLY sample types selected here will be available later",
                to="genlab_bestilling.sampletype",
            ),
        ),
    ]
