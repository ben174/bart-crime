# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import re

from django.db import models


class Report(models.Model):
    report_dt = models.DateTimeField(auto_now_add=True)
    body = models.TextField()
    processed = models.BooleanField(default=False)

    def create_incidents(self):
        body = self.body.replace('=20', '').replace('=\r\n', '').replace('\r\n', '|')
        matches = re.findall(r'(\d+/\d+/\d+), (\d+) hours (.+?)\|', body)

        prev_title = re.match(r'^.+?\|+(.+?)\|\d+/\d+/\d+.*$', body).groups()[0]

        for match in matches:
            m, d, y = match[0].split('/')
            y = '20' + y
            body, case, next_title = re.match(r'^(.*)\s(\d+-\d+\s[A-Z]+\d+)\s?(.*)?$', match[2]).groups()
            year, month, day, hour, minute = int(y), int(m), int(d), int(match[1][0:2]), int(match[1][2:4])
            incident_dt = datetime.datetime(year, month, day, hour, minute)
            title, location = re.match(r'^(.*)\s-\s(.*)$', prev_title).groups()
            Incident.objects.create(
                report=self,
                case=case,
                title=title,
                location=location,
                incident_dt=incident_dt,
                body=body,
            )
            prev_title = next_title
        self.processed = True
        self.save()


class Station(models.Model):
    name = models.CharField(max_length=100)


class Incident(models.Model):
    incident_dt = models.DateTimeField()
    report = models.ForeignKey(Report)
    station = models.ForeignKey(Station, null=True)
    location = models.CharField(max_length=255)
    case = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    body = models.CharField(max_length=5000)
