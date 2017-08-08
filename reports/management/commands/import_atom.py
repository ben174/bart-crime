# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import feedparser
import datetime
import re
import difflib
import pytz
from django.utils import timezone
import time

from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand, CommandError
from reports.models import Incident, Report

body_regex = r'^(\d+)\/(\d+)\/(\d+)[\s,]+(\d{1,2}):?(\d{2})'
TZ = pytz.timezone('America/Los_Angeles')


def parse_time(input_time):
    parsed = None
    try:
        parsed = timezone.make_aware(timezone.datetime(*input_time[:-3]),
                                     TZ)
    except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
        added_hour = (timezone.datetime(*input_time[:-3]) + datetime.timedelta(hours=1))
        parsed = timezone.make_aware(added_hour, TZ)
    return parsed


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
                tags = set()
                for tag in entry['tags']:
                    tags.add(tag['term'])
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
                            incident_dt = TZ.localize(incident_dt)
                        except:
                            print 'Error when parsing time'
                            print body
                            print month, day, year, hour, minute
                            incident_dt = parse_time(entry['published_parsed'])
                            incident_date = incident_dt.date()

                    if ' - ' in title:
                        title_split = title.split(' - ')
                        title = title_split[0]
                        location = title_split[1]
                    incident = Incident.objects.create(
                        title=title,
                        body=body,
                        location=location,
                        incident_dt=incident_dt,
                        incident_date=incident_date,
                        published_at=parse_time(entry['published_parsed']),
                        updated_at=parse_time(entry['updated_parsed'])
                    )
                    incident.tags.set(*tags)
                    total_inserts += 1
        print "Total inserted entries {}".format(total_inserts)
        print "Total rejected entries {}".format(total_rejects)
