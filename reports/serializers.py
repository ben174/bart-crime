from django.contrib.auth.models import User
from reports.models import Report, Incident, Comment
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'first_name', 'last_name')

class ReportSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Report
        fields = ('__all__')


class IncidentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Incident
        fields = ('__all__')

class CommentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Comment
        fields = ('__all__')
