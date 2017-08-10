# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-08 21:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0019_auto_20170808_1434'),
    ]

    operations = [
        migrations.AddField(
            model_name='incident',
            name='parsed_location',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='incident',
            name='source',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]