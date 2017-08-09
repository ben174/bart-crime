# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from reports.models import Station, Report, Incident

from django.contrib import admin
from django.forms import TextInput, Textarea, ModelForm
from django.db import models
from django.core import urlresolvers
from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget


class IncidentForm(ModelForm):
    tags = TagField(required=False, widget=LabelWidget)

class IncidentAdmin(admin.ModelAdmin):

    form = IncidentForm

    list_display = ('case', 'tag_list', 'bpd_id', 'title', 'incident_dt',
                    'location', 'station', 'location_id', 'body', 'icon',
                    'published_at', 'updated_at', 'arrested',
                    'prohibition_order', 'warrant', 'parsed_location',
                    'parsed_time', 'parsed_case')
    list_filter = ('station', 'parsed_location', 'parsed_time', 'parsed_case',
                   'source')
    search_fields = ('title', 'case', 'bpd_id')
    ordering = ('-published_at',)

    readonly_fields = ('parsed_location', 'parsed_time', 'parsed_case')

    def get_queryset(self, request):
        return super(IncidentAdmin, self).get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return u", ".join(o.name for o in obj.tags.all())
    tag_list.short_description = 'Tags'

class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'city')
    ordering = ('abbreviation',)

class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_dt', 'incidents_count', 'email_id', 'processed', 'created_dt')

admin.site.register(Incident, IncidentAdmin)
admin.site.register(Station, StationAdmin)
admin.site.register(Report, ReportAdmin)
