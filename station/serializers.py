from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from station.models import (
    Station, Route, Journey, Train, Ticket, Order)


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
    source_id = serializers.PrimaryKeyRelatedField(
        queryset=Station.objects.all(), source="source", write_only=True
    )
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Station.objects.all(), source="destination", write_only=True
    )
    source = serializers.StringRelatedField(read_only=True)
    destination = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "source_id", "destination_id", "distance")



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
    available_places = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = ("route", "train", "available_places")

    def get_route(self, obj):
        return f"{obj.route.source.name} → {obj.route.destination.name}"

    def get_train(self, obj):
        return obj.train.name


class JourneyListSerializer(JourneySerializer):
    class Meta:
        model = Journey
        fields = ("id", "route", "train", "departure_time", "arrival_time", "available_places")



class TrainSerializer(serializers.ModelSerializer):
    total_spaces = serializers.SerializerMethodField()

    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
            "total_spaces"
        )

    def get_total_spaces(self, obj):
        return obj.capacity_train


class TrainListSerializer(TrainSerializer):
    class Meta:
        model = Train
        fields = (
            "id",
            "name",
            "cargo_num",
            "places_in_cargo",
            "train_type",
            "total_spaces"
        )


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
                  "total_spaces",
                  "image")

    def get_train_type(self, obj):
        return obj.train_type.name


class TrainImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ("id", "image")


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["cargo"],
            attrs["seat"],
            attrs["journey"],
            ValidationError
        )
        return data

    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey")


class JourneyTicketInfoSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="route.source.name", read_only=True)
    destination = serializers.CharField(source="route.destination.name", read_only=True)
    departure = serializers.DateTimeField(source="departure_time", format="%Y-%m-%dT%H:%M:%S%z")
    train = serializers.CharField(source="train.name", read_only=True)

    class Meta:
        model = Journey
        fields = ("id", "source", "destination", "departure", "train")

class TicketListSerializer(serializers.ModelSerializer):
    journey = JourneyTicketInfoSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "cargo", "seat", "journey")


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("cargo", "seat")


class JourneyDetailSerializer(JourneySerializer):
    crew = serializers.SerializerMethodField()
    departure_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    arrival_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    taken_places = TicketSeatsSerializer(source="tickets", many=True, read_only=True)
    taken_places_count = serializers.SerializerMethodField()

    class Meta:
        model = Journey
        fields = (
            "id",
            "route",
            "train",
            "taken_places",
            "taken_places_count",
            "available_places",
            "departure_time",
            "arrival_time",
            "crew",
        )

    def get_crew(self, obj):
        return [member.full_name for member in obj.crew.all()]

    def get_taken_places_count(self, obj):
        return obj.tickets.count()


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
