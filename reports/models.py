# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import re

from django.db import models
from bs4 import BeautifulSoup


class Report(models.Model):
    report_dt = models.DateTimeField(null=True, blank=True)
    body = models.TextField()
    processed = models.BooleanField(default=False)
    email_id = models.CharField(max_length=100, null=True, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True)

    @property
    def fixed_body(self):
        # their class names are all preceeded with some random garbage, clean that up
        return re.sub(r'(<div class=")(.*)(rss_)(.+?")', r'\1\3\4', self.body)

    def create_incidents(self):
        soup = BeautifulSoup(self.fixed_body, 'html.parser')

        for incident_html in soup.find_all('div', class_='rss_item'):
            title = incident_html.find(class_='rss_title').a.text.replace('–', '-')
            location, incident_dt, incident_date = None, None, None
            body = incident_html.find(class_='rss_description').text
            match = re.match(r'^(\d+)\/(\d+)\/(\d+)[\s,]+(\d{1,2}):?(\d{2})', body)
            if match:
                month, day, year, hour, minute = [int(m) for m in match.groups()]
                if year < 2000:
                    year += 2000
                body = '\r\n'.join(body.split('\r\n')[1:])
                incident_dt = datetime.datetime(year, month, day, hour, minute)
                incident_date = datetime.date(year, month, day)

            if ' - ' in title:
                title_split = title.split(' - ')
                title = title_split[0]
                location = title_split[1]
            incident = Incident.objects.create(
                title=title,
                body=body,
                location=location,
                report=self,
                incident_dt=incident_dt,
                incident_date=incident_date,
            )
            print 'Created incident: {}'.format(incident)

        self.processed = True
        self.save()

    def __unicode__(self):
        return '{} - {} incident(s)'.format(self.report_dt, self.incident_set.all().count())


class Station(models.Model):
    name = models.CharField(max_length=100)


class Incident(models.Model):
    incident_dt = models.DateTimeField(null=True, blank=True)
    incident_date = models.DateField(null=True, blank=True)
    report = models.ForeignKey(Report)
    station = models.ForeignKey(Station, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    case = models.CharField(max_length=50, null=True, blank=True)
    title = models.CharField(max_length=255)
    body = models.CharField(max_length=5000)
    arrested = models.BooleanField(default=False)

    def __unicode__(self):
        return self.title
