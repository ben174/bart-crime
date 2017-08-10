# -*- coding: utf-8 -*-
"""Import Atom feeds with BPD log data."""
from __future__ import unicode_literals
import logging
import os
import datetime
import re
import feedparser
import pytz
import six
from bs4 import BeautifulSoup

from django.utils import timezone

from reports.models import Incident
from crime import settings

TIME_REGEX = r'^(\d+)\/(\d+)\/(\d+)[\s,]+(\d{1,2}):?(\d{2})(?:\s[Hh]ours)?.?'
CASE_ID_REGEX = r'(\d{4}-\d{4})(?:\W+)?([SL]\d{0,2})?$'
BPD_ID_REGEX = r'\d+'
TZ = pytz.timezone('America/Los_Angeles')
logging.basicConfig()
_LOGGER = logging.getLogger(__name__)


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


def scrape(local=False, skip_existing=True,
           wipe=False, log_level=logging.WARNING):
    """Begin Atom work."""
    _LOGGER.setLevel(log_level)
    html_parser = six.moves.html_parser.HTMLParser()

    if wipe:
        _LOGGER.warning('Wiping existing incidents data')
        Incident.objects.all().delete()

    def iter_entries(feed):
        """Import the given feedparser feed."""
        total_failures = 0
        total_inserts = 0
        total_skipped = 0
        for entry in feed['entries']:
            bpd_id = re.search(BPD_ID_REGEX, entry['id']).group(0)
            if skip_existing:
                if Incident.objects.filter(bpd_id=bpd_id).exists():
                    _LOGGER.debug('Skipping import of log: %s', bpd_id)
                    total_skipped += 1
                    continue
                else:
                    _LOGGER.debug('Attempting import of log: %s', bpd_id)
            raw_title = entry['title']
            raw_body = entry['content'][0]['value']
            body = None
            soup = BeautifulSoup(raw_body, 'html.parser')
            p_tags = soup.findAll('p')

            if len(p_tags) == 1:
                body = p_tags[0].text
            elif len(p_tags) == 2:
                body = p_tags[1].text
            elif len(p_tags) > 2:
                p_tags.pop(0)
                combined_body = list()
                for line in p_tags:
                    combined_body.append(line.text)
                body = ' '.join(combined_body)
            if body is None:
                total_failures += 1
                _LOGGER.error('Unable to parse log: %s (%d) \n\n%s\n\n',
                              bpd_id, len(p_tags), raw_body)

            if body is not None:
                body = body.strip()
                location, incident_dt, incident_date = None, None, None
                case_id, location_id = None, None
                parsed_time, parsed_case = False, False
                tags = set()
                for tag in entry['tags']:
                    term = tag['term']
                    if term.islower():
                        term = term.title()
                    tags.add(term)
                case_id_matches = re.search(CASE_ID_REGEX, body)
                if case_id_matches is not None:
                    case_id = case_id_matches.group(1)
                    location_id = case_id_matches.group(2)
                    parsed_case = True

                incident_dt = parse_time(entry['published_parsed'])
                incident_date = incident_dt.date()
                match = re.match(TIME_REGEX, p_tags[0].text)
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
                    except BaseException:
                        _LOGGER.error('Error when parsing time on log: %s',
                                      bpd_id)

                title = raw_title.replace('–', '-')

                if title.isupper():
                    title = title.title()

                if ' - ' in title:
                    title_split = title.split(' - ')
                    title = title_split[0]
                    location = html_parser.unescape(title_split[1])
                elif ' -- ' in title:
                    title_split = title.split(' -- ')
                    title = title_split[0]
                    location = html_parser.unescape(title_split[1])
                elif ' at ' in title.lower():
                    title_split = title.split(' at ')
                    if len(title_split) == 1:
                        title_split = title.split(' At ')
                    title = title_split[0]
                    location = html_parser.unescape(title_split[1])

                if title.isupper():
                    title = title.title()

                if location is not None and location.isupper():
                    location = location.title()

                cleaned_body = re.sub(TIME_REGEX, '', body)
                cleaned_body = re.sub(CASE_ID_REGEX, '', cleaned_body)

                incident = Incident.objects.create(
                    title=html_parser.unescape(title),
                    body=html_parser.unescape(cleaned_body),
                    location=location,
                    incident_dt=incident_dt,
                    incident_date=incident_date,
                    published_at=parse_time(entry['published_parsed']),
                    updated_at=parse_time(entry['updated_parsed']),
                    case=case_id,
                    location_id=location_id,
                    parsed_time=parsed_time,
                    parsed_case=parsed_case,
                    bpd_id=bpd_id,
                    raw_title=raw_title,
                    raw_body=raw_body,
                    source=('atom_local' if local else 'atom_remote')
                )
                incident.tags.set(*tags)
                total_inserts += 1
        return (total_inserts, total_failures, total_skipped)

    results = None

    if local is True:
        _LOGGER.debug('Importing local Atom data')
        total_failures = 0
        total_inserts = 0
        total_skipped = 0
        for data_file in os.listdir('data/'):
            feed = feedparser.parse('data/{}'.format(data_file))
            file_results = iter_entries(feed)
            total_inserts += file_results[0]
            total_failures += file_results[1]
            total_skipped += file_results[2]
            results = (total_failures, total_inserts, total_skipped)
    else:
        _LOGGER.debug('Importing remote Atom data')
        feed = feedparser.parse(settings.get_secret('BPDLOG_ATOM'))
        results = iter_entries(feed)

    _LOGGER.info('Total inserted entries %d', results[0])
    _LOGGER.info('Total failed entries %d', results[1])
    _LOGGER.info('Total skipped entries %d', results[2])

    return results
