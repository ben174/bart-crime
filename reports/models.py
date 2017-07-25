# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Report(models.Model):
    report_dt = models.DateTimeField()
    body = models.TextField()


class Station(models.Model):
    name = models.CharField(max_length=100)


class Incident(models.Model):
    incident_dt = models.DateTimeField()
    report = models.ForeignKey(Report)
    station = models.ForeignKey(Station)
    location = models.CharField(max_length=255)
    case = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    body = models.CharField(max_length=5000)
