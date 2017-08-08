# -*- coding: utf-8 -*-
"""Import Atom feeds with BPD log data."""
from __future__ import unicode_literals
from six.moves.html_parser import HTMLParser
import argparse
import os
import feedparser
import datetime
import re
import pytz
from django.utils import timezone

from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand
from reports.models import Incident
from crime import settings

time_regex = r'^(\d+)\/(\d+)\/(\d+)[\s,]+(\d{1,2}):?(\d{2})(?:\s[Hh]ours).?'
case_id_regex = r'(\d{4}-\d{4})(?:\W+)?([SL]\d{0,2})?'
bpd_id_regex = r'\d+'
TZ = pytz.timezone('America/Los_Angeles')


def parse_time(input_time):
    """Parse an Atom time stamp."""
    parsed = None
    try:
        parsed = timezone.make_aware(timezone.datetime(*input_time[:-3]),
                                     timezone.utc)
    except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
        added_hour = (timezone.datetime(*input_time[:-3]) +
                      datetime.timedelta(hours=1))
        parsed = timezone.make_aware(added_hour, timezone.utc)
    return parsed.astimezone(TZ)


class Command(BaseCommand):
    """The Django command."""

    help = 'Import historical data from Atom XML'

    def add_arguments(self, parser):
        """Add optional command arguments."""
        def str2bool(v):
            if v.lower() in ('yes', 'true', 't', 'y', '1'):
                return True
            elif v.lower() in ('no', 'false', 'f', 'n', '0'):
                return False
            else:
                raise argparse.ArgumentTypeError('Boolean value expected.')

        parser.add_argument('--local', type=str2bool, nargs='?',
                            const=True, default='no',
                            help='Import from local data.', dest='local')

    def handle(self, *args, **options):
        """Handle the command."""
        h = HTMLParser()

        def iter_entries(feed):
            """Import the given feedparser feed."""
            total_rejects = 0
            total_inserts = 0
            for entry in feed['entries']:
                bpd_id = re.search(bpd_id_regex, entry['id']).group(0)
                if Incident.objects.filter(bpd_id=bpd_id).exists():
                    print 'Skipping import of log: {}'.format(bpd_id)
                    continue
                else:
                    print 'Attempting import of log: {}'.format(bpd_id)
                raw_title = entry['title']
                raw_body = entry['content'][0]['value']
                title = raw_title.replace('–', '-')
                location, incident_dt, incident_date = None, None, None
                case_id, location_id, body = None, None, None
                parsed_time, parsed_case = False, False
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
                            print month, day, year, hour, minute
                            incident_dt = parse_time(entry['published_parsed'])
                            incident_date = incident_dt.date()

                    if title.isupper():
                        title = title.title()

                    if ' - ' in title:
                        title_split = title.split(' - ')
                        title = title_split[0]
                        location = h.unescape(title_split[1])
                    elif ' at ' in title.lower():
                        title_split = title.split(' at ')
                        if len(title_split) == 1:
                            title_split = title.split(' At ')
                        title = title_split[0]
                        location = h.unescape(title_split[1])

                    arrest_check = ('arrest' in raw_body.lower() or
                                    'booked' in raw_body.lower() or
                                    'detain' in raw_body.lower() or
                                    'arrest' in raw_title.lower() or
                                    'booked' in raw_title.lower() or
                                    'detain' in raw_title.lower())

                    prohibition_check = ('prohibition' in raw_body.lower() or
                                         'prohibition' in raw_title.lower() or
                                         'stay away' in raw_body.lower() or
                                         'stay away' in raw_title.lower())

                    warrant = ('warrant' in raw_body.lower() or
                               'warrant' in raw_title.lower())

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
                        bpd_id=bpd_id
                    )
                    incident.tags.set(*tags)
                    total_inserts += 1
            return (total_rejects, total_inserts)

        results = None

        if options['local']:
            print 'Importing local data'
            for fn in os.listdir('data/'):
                feed = feedparser.parse('data/{}'.format(fn))
                results = iter_entries(feed)
        else:
            print 'Importing from remote data'
            feed = feedparser.parse(settings.get_secret('BPDLOG_ATOM'))
            results = iter_entries(feed)

        print 'Total inserted entries {}'.format(results[1])
        print 'Total rejected entries {}'.format(results[0])
