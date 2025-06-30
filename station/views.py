from datetime import datetime

from django.shortcuts import render
from rest_framework import viewsets, mixins
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from station.models import Station, Route, Journey, Train, Order
from station.permissions import IsAdminOrIfAuthenticatedReadOnly
from station.serializers import (StationSerializer,
                                 StationListSerializer,
                                 StationDetailSerializer,
                                 RouteSerializer,
                                 RouteDetailSerializer,
                                 RouteListSerializer,
                                 JourneySerializer,
                                 JourneyListSerializer,
                                 JourneyDetailSerializer,
                                 TrainSerializer,
                                 TrainListSerializer,
                                 TrainDetailSerializer,
                                 OrderSerializer,
                                 OrderListSerializer)


from django.db.models import Count, F, ExpressionWrapper, IntegerField
from django_filters.rest_framework import DjangoFilterBackend

class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        return self.queryset.annotate(
            routes_count=Count("routes_from")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return StationListSerializer
        if self.action == "retrieve":
            return StationDetailSerializer
        return StationSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source", "destination")
    serializer_class = RouteSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["route__source__name", "route__destination__name"]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteDetailSerializer
        return RouteSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.select_related(
        "route__source", "route__destination", "train"
    ).prefetch_related("crew", "tickets")
    serializer_class = JourneySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["route__source__name", "route__destination__name"]

    def get_queryset(self):
        queryset = self.queryset.annotate(
            taken_places_count=Count("tickets"),
        )

        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")
        date = self.request.query_params.get("date")
        train_id = self.request.query_params.get("train")

        if source:
            queryset = queryset.filter(route__source__name__icontains=source)
        if destination:
            queryset = queryset.filter(route__destination__name__icontains=destination)
        if date:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time__date=parsed_date)

        if train_id:
            queryset = queryset.filter(train_id=train_id)

        return (
        Journey.objects
        .select_related("route__source", "route__destination", "train")
        .prefetch_related("crew", "tickets")
        .annotate(
            available_places=ExpressionWrapper(
                F("train__cargo_num") * F("train__places_in_cargo") - Count("tickets"),
                output_field=IntegerField()
            )
        )
    )

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action == "retrieve":
            return JourneyDetailSerializer
        return JourneySerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainDetailSerializer
        return TrainSerializer


class OrderPagination(PageNumberPagination):
    page_size = 5
    max_page_size = 100


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "tickets",
                "tickets__journey__route__source",
                "tickets__journey__route__destination",
                "tickets__journey__train"
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Create your views here.
