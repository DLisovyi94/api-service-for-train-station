from django.db import transaction
from rest_framework import serializers

from station.models import (
    Station, Route, Journey, Train)


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

class JourneySerializer(serializers.ModelSerializer):
    route = serializers.SerializerMethodField()
    train = serializers.SerializerMethodField()
    class Meta:
        model = Journey
        fields = ("route", "train")

    def get_route(self, obj):
        return f"{obj.route.source.name} → {obj.route.destination.name}"

    def get_train(self, obj):
        return obj.train.name


class JourneyListSerializer(JourneySerializer):
    class Meta:
        model = Journey
        fields = ("id", "route", "train")


class JourneyDetailSerializer(JourneySerializer):
    crew = serializers.SerializerMethodField()
    departure_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Journey
        fields = ("id", "route", "train", "departure_time", "arrival_time", "crew")

    def get_crew(self, obj):
        return [member.full_name for member in obj.crew.all()]


class TrainSerializer(serializers.ModelSerializer):
    total_spaces = serializers.SerializerMethodField()
    class Meta:
        model = Train
        fields = ("id", "name", "total_spaces")

    def get_total_spaces(self, obj):
        return obj.capacity_train

class TrainListSerializer(TrainSerializer):
    class Meta:
        model = Train
        fields = ("id", "name", "total_spaces")


class TrainDetailSerializer(TrainSerializer):
    train_type = serializers.CharField(
        source="train_type.name",
        read_only=True)

    class Meta:
        model = Train
        fields = ("name",
                  "train_type",
                  "cargo_num",
                  "places_in_cargo",
                  "total_spaces")

        def get_train_type(self, obj):
            return obj.train_type.name