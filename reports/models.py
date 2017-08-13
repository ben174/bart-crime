# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import difflib
import pytz

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from taggit.managers import TaggableManager

from twitter import TwitterError

from reports.tweet import Twitter, TwitterNotConfigured

HUMAN_TIME = '%a, %b %d %Y %I:%M %p'


class Station(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=5, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.IntegerField()

    incidents_count = 0

    def __unicode__(self):
        return "{} ({})".format(self.name, self.abbreviation)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('station', args=[str(self.abbreviation)])

    @property
    def info_url(self):
        return "http://www.bart.gov/stations/{}".format(self.abbreviation)

    @property
    def incidents_info(self):
        return {
            'total': self.incidents.all().count()
        }


class Incident(models.Model):
    incident_dt = models.DateTimeField(null=True, blank=True)
    incident_date = models.DateField(null=True, blank=True)
    station = models.ForeignKey(Station, null=True, blank=True,
                                related_name='incidents')
    location = models.CharField(max_length=255, null=True, blank=True)
    case = models.CharField(max_length=50, null=True, blank=True)
    location_id = models.CharField(max_length=50, null=True, blank=True)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    arrested = models.BooleanField(default=False)
    prohibition_order = models.BooleanField(default=False)
    warrant = models.BooleanField(default=False)
    tweeted = models.BooleanField(default=False)
    parsed_location = models.BooleanField(default=False)
    parsed_time = models.BooleanField(default=False)
    parsed_case = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    bpd_id = models.IntegerField(null=True, blank=True)
    raw_title = models.CharField(max_length=255)
    raw_body = models.TextField(blank=True)
    source = models.CharField(max_length=50, blank=True)

    tags = TaggableManager()

    twitter = None

    def __unicode__(self):
        location = self.location
        if self.station is not None:
            location = self.station
        return "{} @ {} - {}".format(self.title, location,
                                     self.incident_dt.strftime(HUMAN_TIME))

    @property
    def tweet_text(self):
        location = self.location
        if self.station is not None:
            location = str(self.station.name)

        incident_date = self.incident_dt.strftime(HUMAN_TIME)

        base_text = "{} at {} - {}".format(self.title, location, incident_date)
        if len(base_text) > 120:  # Max tweet length is 140 - 20 for URL
            if len(base_text) - (len(location) - 6) <= 120:
                # If we have station, use abbr instead of name
                if self.station is not None:
                    abbr = self.station.abbreviation
                    base_text = "{} at ({}) - {}".format(self.title, abbr,
                                                         incident_date)
                # If no station, remove date
                else:
                    base_text = "{} at ({})".format(self.title, abbr)

        return base_text

    @property
    def get_url(self):
        return '{}/incident/{}'.format('https://www.bartcrimes.com', self.pk)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('incident', args=[str(self.id)])

    def tweet(self):
        if not Incident.twitter:
            Incident.twitter = Twitter()
            Incident.twitter.connect()
        try:
            Incident.twitter.post_incident(self)
        except TwitterNotConfigured:
            print "Twitter not configured, not attempting to tweet"
            return

        self.tweeted = True
        self.save()

    @property
    def station_best_guess(self):
        if not self.location:
            return None
        station_names = list(Station.objects.all().values_list('name',
                                                               flat=True))
        cleaned_location = self.location.replace(' Station', '')
        answer = difflib.get_close_matches(cleaned_location, station_names)
        if answer:
            return Station.objects.get(name=answer[0])
        else:
            fixed_station = None
            if '12th' in cleaned_location.lower():
                fixed_station = Station.objects.get(abbreviation='12TH')
            elif '16th' in cleaned_location.lower():
                fixed_station = Station.objects.get(abbreviation='16TH')
            elif '19th' in cleaned_location.lower():
                fixed_station = Station.objects.get(abbreviation='19TH')
            elif '24th' in cleaned_location.lower():
                fixed_station = Station.objects.get(abbreviation='24TH')
            elif 'east dublin' in cleaned_location.lower():
                fixed_station = Station.objects.get(abbreviation='DUBL')
            elif 'pleasant hill' in cleaned_location.lower():
                fixed_station = Station.objects.get(abbreviation='PHIL')
            elif 'del norte' in cleaned_location.lower():
                fixed_station = Station.objects.get(abbreviation='DELN')
            return fixed_station
        return None

    @property
    def icon(self):
        lower_title = self.title.lower()
        icon = None
        if ('auto' in lower_title or
                'vehicle' in lower_title or 'car' in lower_title):
            icon = 'car'
        if 'bicycle' in lower_title or 'bike' in lower_title:
            icon = 'bicycle'
        if ('intoxicat' in lower_title or
                'alcohol' in lower_title or
                'open container' in lower_title):
            icon = 'glass'
        if 'warrant' in lower_title:
            icon = 'user-secret'
        if ('theft' in lower_title or
                'robbery' in lower_title or
                'burglary' in lower_title):
            icon = 'money'
        if 'person' in lower_title:
            icon = 'user-secret'
        if ('violation' in lower_title or
                'obstruct' in lower_title or
                'prohibit' in lower_title):
            icon = 'ban'
        if 'weapon' in lower_title:
            icon = 'cutlery'
        if 'robbery' in lower_title:
            icon = 'bank'
        if 'exposure' in lower_title:
            icon = 'user-secret'
        if 'agency' in lower_title or 'assist' in lower_title:
            icon = 'shield'
        if 'narcotics' in lower_title:
            icon = 'medkit'
        return icon

    @property
    def hover_date(self):
        rfc5322 = '%a, %d %b %Y %H:%M:%S %z'
        la_tz = pytz.timezone('America/Los_Angeles')
        incident_dt = self.incident_dt.astimezone(la_tz).strftime(rfc5322)
        published_at = self.published_at.astimezone(la_tz).strftime(rfc5322)
        updated_at = self.updated_at.astimezone(la_tz).strftime(rfc5322)
        if incident_dt != published_at:
            if published_at != updated_at:
                fmt_str = ("Incident occurred at: {}\n"
                           "Incident was published at: {}\n"
                           "Incident was updated at: {}")
                return fmt_str.format(incident_dt, published_at, updated_at)
            fmt_str = "Incident occurred at: {}\nIncident was published at: {}"
            return fmt_str.format(incident_dt, published_at)
        if published_at != updated_at:
            fmt_str = ("Incident was published at: {}\n"
                       "Incident was updated at: {}"
                       "(occurance date not parsed)")
            return fmt_str.format(published_at, updated_at)
        failure = "Incident was published at {} (occurance date not parsed)"
        return failure.format(published_at)


@receiver(pre_save, sender=Incident)
def fill_data(sender, instance, **kwargs):  # pylint: disable=unused-argument
    guessed_station = instance.station_best_guess
    if guessed_station is not None:
        instance.parsed_location = True
        instance.station = guessed_station

    title = instance.title.lower()
    body = instance.body.lower()

    arrest_keywords = ['arrest', 'booked', 'detain']

    instance.arrested = (any(x in body for x in arrest_keywords) or
                         any(x in title for x in arrest_keywords))

    prohibition_keywords = ['prohibition', 'stay away', 'stay-away']

    prohibited_body_check = any(x in body for x in prohibition_keywords)
    prohibited_title_check = any(x in title for x in prohibition_keywords)

    instance.prohibition_order = (prohibited_body_check or
                                  prohibited_title_check)

    instance.warrant = ('warrant' in body or
                        'warrant' in title)


@receiver(post_save, sender=Incident)
# pylint: disable=unused-argument
def tweet_incident(sender, instance, **kwargs):
    try:
        instance.tweet()
    except TwitterError as exc:
        print 'Exception while tweeting incident: {}'.format(str(exc))


class Comment(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    incident = models.ForeignKey(Incident)
    text = models.TextField()

    def __unicode__(self):
        return self.created_dt
