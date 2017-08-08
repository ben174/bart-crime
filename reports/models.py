# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import re
import difflib

from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.db import models
import pytz
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from taggit.managers import TaggableManager

from reports.tweet import Twitter


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

    @property
    def incidents_count(self):
        return self.incidents.all().count()

    def create_incidents(self):
        soup = BeautifulSoup(self.fixed_body, 'html.parser')
        other_soup = BeautifulSoup(self.fixed_body, 'html.parser')

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
                incident_dt = pytz.timezone('America/Los_Angeles').localize(incident_dt)

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

        self.processed = True
        self.save()

    def __unicode__(self):
        return '{} - {} incident(s)'.format(self.report_dt,
                                            self.incidents_count)


class Station(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=5)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.IntegerField()

    def __unicode__(self):
        return "{} ({})".format(self.name, self.abbreviation)

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
    report = models.ForeignKey(Report, null=True, blank=True,
                               related_name='incidents')
    station = models.ForeignKey(Station, null=True, blank=True,
                                related_name='incidents')
    location = models.CharField(max_length=255, null=True, blank=True)
    case = models.CharField(max_length=50, null=True, blank=True)
    location_id = models.CharField(max_length=50, null=True, blank=True)
    title = models.CharField(max_length=255)
    body = models.CharField(max_length=5000)
    arrested = models.BooleanField(default=False)
    prohibition_order = models.BooleanField(default=False)
    warrant = models.BooleanField(default=False)
    tweeted = models.BooleanField(default=False)
    parsed_time = models.BooleanField(default=False)
    parsed_case = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    bpd_id = models.IntegerField(null=True, blank=True)

    tags = TaggableManager()

    twitter = None

    def get_url(self):
        return '{}/incident/{}'.format('https://www.bartcrimes.com', self.pk)

    def tweet(self):
        if not Incident.twitter:
            Incident.twitter = Twitter()
            Incident.twitter.connect()
        Incident.twitter.post_incident(self)
        self.tweeted = True
        self.save()

    @property
    def tweet_text(self):
        return ''

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
def fill_station(sender, instance, **kwargs):
    guessed_station = instance.station_best_guess
    if guessed_station is not None:
        instance.station = guessed_station

# @receiver(post_save, sender=Incident)
def tweet_incident(sender, instance, **kwargs):
    try:
        instance.tweet()
    except Exception as e:
        print 'Exception while tweeting incident: {}'.format(str(e))



class Comment(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    incident = models.ForeignKey(Incident)
    text = models.TextField()
