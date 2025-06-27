from django.db import transaction
from rest_framework import serializers

from station.models import (
    Station, Route)


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude")


class StationListSerializer(StationSerializer):
    class Meta:
        model = Station
        fields = ("id", "name")

class StationDetailSerializer(StationSerializer):
    routes_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Station
        fields = ("id", "name", "latitude", "longitude", "routes_count")


class RouteSerializer(serializers.ModelSerializer):
    source = serializers.SlugRelatedField(read_only=True, slug_field="name")
    destination = serializers.SlugRelatedField(read_only=True, slug_field="name")
    class Meta:
        model = Route
        fields = ("source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    class Meta:
        model = Route
        fields = ("source", "destination", "distance")

class RouteDetailSerializer(RouteSerializer):
    trains = serializers.SerializerMethodField()
    class Meta:
        model = Route
        fields = ("source", "destination", "distance", "trains")

    def get_trains(self, obj):
        return list(
            obj.journeys.select_related("train")
            .values_list("train__name", flat=True)
            .distinct()
        )
