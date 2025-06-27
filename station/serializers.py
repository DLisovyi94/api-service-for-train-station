from django.db import transaction
from rest_framework import serializers

from station.models import (
    Station)


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class StationListSerializer(StationSerializer):
    routes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Station
        fields = ("id", "name", "routes_count")

class StationDetailSerializer(StationSerializer):
    routes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude", "routes_count")