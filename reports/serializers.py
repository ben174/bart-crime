from django.contrib.auth.models import User
from reports.models import Incident, Comment, Station
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'first_name', 'last_name')

class StationSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    info_url = serializers.ReadOnlyField()
    incidents = serializers.ReadOnlyField(source='incidents_info')

    class Meta:
        model = Station
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
