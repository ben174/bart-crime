# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-10 00:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0020_auto_20170808_1443'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='incident',
            name='report',
        ),
        migrations.DeleteModel(
            name='Report',
        ),
    ]
