# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from six.moves.html_parser import HTMLParser
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

time_regex = r'^(\d+)\/(\d+)\/(\d+)[\s,]+(\d{1,2}):?(\d{2})'
case_id_regex = r'(\d{4}-\d{4})\W+(L\d{0,2})'
TZ = pytz.timezone('America/Los_Angeles')


def parse_time(input_time):
    parsed = None
    try:
        parsed = timezone.make_aware(timezone.datetime(*input_time[:-3]),
                                     TZ)
    except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
        added_hour = (timezone.datetime(*input_time[:-3]) +
                      datetime.timedelta(hours=1))
        parsed = timezone.make_aware(added_hour, TZ)
    return parsed


class Command(BaseCommand):
    help = 'Import historical data from downloaded Atom XML'

    def handle(self, *args, **options):
        total_rejects = 0
        total_inserts = 0
        h = HTMLParser()
        for fn in os.listdir('data/'):
            d = feedparser.parse("data/{}".format(fn))
            for entry in d['entries']:
                # print entry
                title = entry['title'].replace('–', '-')
                location, incident_dt, incident_date, case_id, location_id, body = None, None, None, None, None, None
                parsed_time, parsed_case = False, False
                raw_body = entry['content'][0]['value']
                soup = BeautifulSoup(raw_body, 'html.parser')
                allPTags = soup.findAll('p')

                tags = set()
                for tag in entry['tags']:
                    tags.add(tag['term'])
                case_id_matches = re.search(case_id_regex,
                                            raw_body)
                if case_id_matches is not None:
                    case_id = case_id_matches.group(1)
                    location_id = case_id_matches.group(2)
                    parsed_case = True
                if len(allPTags) == 1:
                    body = allPTags[0].text
                elif len(allPTags) == 2:
                    body = allPTags[1].text
                elif len(allPTags) > 2:
                    allPTags.pop(0)
                    combined_body = list()
                    for line in allPTags:
                        combined_body.append(line.text)
                    body = ' '.join(combined_body)
                if body is None:
                    total_rejects += 1
                    print 'REJECTED ({}) \n\n{}\n\n'.format(len(allPTags),
                                                            raw_body)
                if body is not None:
                    match = re.match(time_regex, allPTags[0].text)
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
                            parsed_time = True
                        except:
                            print 'Error when parsing time'
                            print body
                            print month, day, year, hour, minute
                            incident_dt = parse_time(entry['published_parsed'])
                            incident_date = incident_dt.date()

                    if ' - ' in title:
                        title_split = title.split(' - ')
                        title = title_split[0]
                        location = h.unescape(title_split[1])

                    arrest_check = ('arrest' in raw_body.lower() or
                                    'booked' in raw_body.lower() or
                                    'detain' in raw_body.lower() or
                                    'arrest' in entry['title'].lower() or
                                    'booked' in entry['title'].lower() or
                                    'detain' in entry['title'].lower())

                    prohibition_check = ('prohibition' in raw_body.lower() or
                                         'prohibition' in entry['title'].lower() or
                                         'stay away' in raw_body.lower() or
                                         'stay away' in entry['title'].lower())

                    warrant = ('warrant' in raw_body.lower() or
                               'warrant' in entry['title'].lower())

                    cleaned_body = re.sub(time_regex, '', body)
                    cleaned_body = re.sub(case_id_regex, '', cleaned_body)

                    incident = Incident.objects.create(
                        title=h.unescape(title),
                        body=h.unescape(cleaned_body),
                        location=location,
                        incident_dt=incident_dt,
                        incident_date=incident_date,
                        published_at=parse_time(entry['published_parsed']),
                        updated_at=parse_time(entry['updated_parsed']),
                        arrested=arrest_check,
                        prohibition_order=prohibition_check,
                        warrant=warrant,
                        case=case_id,
                        location_id=location_id,
                        parsed_time=parsed_time,
                        parsed_case=parsed_case,
                    )
                    incident.tags.set(*tags)
                    total_inserts += 1
        print "Total inserted entries {}".format(total_inserts)
        print "Total rejected entries {}".format(total_rejects)
