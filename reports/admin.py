# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from reports.models import Station, Report, Incident

from django.contrib import admin

class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident_dt', 'location', 'station_best_guess', 'body', 'icon', )

class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'city')
    ordering = ('abbreviation',)


admin.site.register(Incident, IncidentAdmin)
admin.site.register(Station, StationAdmin)
admin.site.register([Report])
