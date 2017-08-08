# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import feedparser
import datetime
import re
import difflib
import pytz

from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand, CommandError
from reports.models import Incident, Report

body_regex = r'^(\d+)\/(\d+)\/(\d+)[\s,]+(\d{1,2}):?(\d{2})'
TZ = 'America/Los_Angeles'


class Command(BaseCommand):
    help = 'Import historical data from downloaded Atom XML'

    def handle(self, *args, **options):
        total_rejects = 0
        total_inserts = 0
        for fn in os.listdir('data/'):
            d = feedparser.parse("data/{}".format(fn))
            for entry in d['entries']:
                # print entry
                title = entry['title'].replace('–', '-')
                location, incident_dt, incident_date = None, None, None
                soup = BeautifulSoup(entry['content'][0]['value'],
                                     'html.parser')
                allPTags = soup.findAll('p')
                body = None
                if len(allPTags) == 1:
                    body = allPTags[0].text
                elif len(allPTags) == 2:
                    body = allPTags[1].text
                if body is None:
                    total_rejects += 1
                    print 'REJECTED'
                    # print entry
                if body is not None:
                    match = re.match(body_regex, allPTags[0].text)
                    if match:
                        month, day, year, hour, minute = [int(m) for m in
                                                          match.groups()]
                        if year < 2000:
                            year += 2000
                        try:
                            incident_dt = datetime.datetime(year, month, day,
                                                            hour, minute)
                            incident_date = datetime.date(year, month, day)
                            incident_dt = pytz.timezone(TZ).localize(incident_dt)
                        except:
                            print 'Error when parsing time'
                            print body
                            print month, day, year, hour, minute

                    if ' - ' in title:
                        title_split = title.split(' - ')
                        title = title_split[0]
                        location = title_split[1]
                    incident = Incident.objects.create(
                        title=title,
                        body=body,
                        report=Report.objects.get(pk=74),
                        location=location,
                        incident_dt=incident_dt,
                        incident_date=incident_date,
                    )
                    total_inserts += 1
        print "Total inserted entries {}".format(total_inserts)
        print "Total rejected entries {}".format(total_rejects)
