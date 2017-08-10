# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import difflib

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from taggit.managers import TaggableManager

from reports.tweet import Twitter


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
        Incident.twitter.post_incident(self)
        self.tweeted = True
        self.save()

    @property
    def tweet_text(self):
        location = self.location
        if self.station is not None:
            location = self.station.abbreviation
        return '{} @ {}'.format(self.title, location)

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
            if '12th' in cleaned_location.lower():
                return Station.objects.get(abbreviation='12TH')
            if '16th' in cleaned_location.lower():
                return Station.objects.get(abbreviation='16TH')
            if '19th' in cleaned_location.lower():
                return Station.objects.get(abbreviation='19TH')
            if '24th' in cleaned_location.lower():
                return Station.objects.get(abbreviation='24TH')
            if 'east dublin' in cleaned_location.lower():
                return Station.objects.get(abbreviation='DUBL')
            if 'pleasant hill' in cleaned_location.lower():
                return Station.objects.get(abbreviation='PHIL')
            if 'del norte' in cleaned_location.lower():
                return Station.objects.get(abbreviation='DELN')
        return None

    @property
    def icon(self):
        lower_title = self.title.lower()
        if ('auto' in lower_title or
                'vehicle' in lower_title or 'car' in lower_title):
            return 'car'
        if 'bicycle' in lower_title or 'bike' in lower_title:
            return 'bicycle'
        if ('intoxicat' in lower_title or
                'alcohol' in lower_title or
                'open container' in lower_title):
            return 'glass'
        if 'warrant' in lower_title:
            return 'user-secret'
        if ('theft' in lower_title or
                'robbery' in lower_title or
                'burglary' in lower_title):
            return 'money'
        if 'person' in lower_title:
            return 'user-secret'
        if ('violation' in lower_title or
                'obstruct' in lower_title or
                'prohibit' in lower_title):
            return 'ban'
        if 'weapon' in lower_title:
            return 'cutlery'
        if 'robbery' in lower_title:
            return 'bank'
        if 'exposure' in lower_title:
            return 'user-secret'
        if 'agency' in lower_title or 'assist' in lower_title:
            return 'shield'
        if 'narcotics' in lower_title:
            return 'medkit'

    def __unicode__(self):
        return self.title


@receiver(pre_save, sender=Incident)
def fill_data(sender, instance, **kwargs):
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
def tweet_incident(sender, instance, **kwargs):
    try:
        instance.tweet()
    except Exception as exc:
        print 'Exception while tweeting incident: {}'.format(str(exc))


class Comment(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    incident = models.ForeignKey(Incident)
    text = models.TextField()

    def __unicode__(self):
        return self.created_dt
