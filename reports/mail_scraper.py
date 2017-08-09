from calendar import timegm
from datetime import datetime, timedelta, tzinfo
from email.utils import mktime_tz, parsedate_tz

import requests

from crime import settings
from reports.models import Report


def parse_mail_date(date_str):
    ZERO = timedelta(0)

    class FixedOffset(tzinfo):
        """Fixed UTC offset: `time = utc_time + utc_offset`."""
        def __init__(self, offset, name=None):
            self.__offset = offset
            if name is None:
                seconds = abs(offset).seconds
                assert abs(offset).days == 0
                hours, seconds = divmod(seconds, 3600)
                if offset < ZERO:
                    hours = -hours
                minutes, seconds = divmod(seconds, 60)
                assert seconds == 0
                # NOTE: the last part is to remind about deprecated POSIX
                # GMT+h timezones that have the opposite sign in the
                # name; the corresponding numeric value is not used e.g.,
                # no minutes
                self.__name = '<%+03d%02d>GMT%+d' % (hours, minutes, -hours)
            else:
                self.__name = name

        def utcoffset(self, dt=None):
            return self.__offset

        def tzname(self, dt=None):
            return self.__name

        def dst(self, dt=None):
            return ZERO

        def __repr__(self):
            return 'FixedOffset(%r, %r)' % (self.utcoffset(), self.tzname())

    tt = parsedate_tz(date_str)
    timestamp = timegm(tt) - tt[9]  # local time - utc offset == utc time
    naive_utc_dt = datetime(1970, 1, 1) + timedelta(seconds=timestamp)
    aware_utc_dt = naive_utc_dt.replace(tzinfo=FixedOffset(ZERO, 'UTC'))
    return aware_utc_dt.astimezone(FixedOffset(timedelta(seconds=tt[9])))


def scrape():
    events_url = "https://api.mailgun.net/v3/{}/events".format(settings.get_secret('MAILGUN_DOMAIN'))
    auth = ("api", settings.get_secret('MAILGUN_KEY'))
    events = requests.get(
            events_url,
            auth=auth,
            params={"event": "stored"}).json()
    for event in events['items']:
        message = requests.get(
            event['storage']['url'],
            auth=auth)

        if message.status_code != 200:
            print 'Message referenced in event was not found, continuing'
            continue

        message_json = message.json()

        if Report.objects.filter(email_id=message_json['Message-Id']).exists():
            print 'Skipping email: {}'.format(message_json['Message-Id'])
            continue

        report = Report.objects.create(
            report_dt=parse_mail_date(message_json['Date']),
            email_id=message_json['Message-Id'],
            body=message_json['body-html'],
        )
        print 'Creating incidents...'
        report.create_incidents()
