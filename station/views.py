from django.shortcuts import render
from rest_framework import viewsets, mixins
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import GenericViewSet

from station.models import Station, Route, Journey, Train, Order
from station.serializers import (StationSerializer,
                                 StationListSerializer,
                                 StationDetailSerializer, RouteSerializer, RouteDetailSerializer, RouteListSerializer,
                                 JourneySerializer, JourneyListSerializer, JourneyDetailSerializer, TrainSerializer,
                                 TrainListSerializer, TrainDetailSerializer, OrderSerializer, OrderListSerializer)


from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend

class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
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
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["source__name", "destination__name"]

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteDetailSerializer
        return RouteSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    serializer_class = JourneySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["route__name"]

    def get_serializer_class(self):
        if self.action == "list":
            return JourneyListSerializer
        if self.action == "retrieve":
            return JourneyDetailSerializer
        return JourneySerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer
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
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Create your views here.
