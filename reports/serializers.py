from django.contrib.auth.models import User
from reports.models import Report, Incident, Comment, Station
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'first_name', 'last_name')

class StationSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Station
        fields = ('__all__')

class ReportSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    incidents = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Report
        fields = ('__all__')

class IncidentSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Incident
        fields = ('__all__')

class CommentSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Comment
        fields = ('__all__')
