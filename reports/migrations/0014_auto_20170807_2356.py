# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-08 06:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0013_incident_location_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='incident',
            name='parsed_case',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='incident',
            name='parsed_time',
            field=models.BooleanField(default=False),
        ),
    ]
