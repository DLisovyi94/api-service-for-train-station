from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from station.models import Station, Route
from station.serializers import (StationSerializer,
                                 StationListSerializer,
                                 StationDetailSerializer, RouteSerializer, RouteDetailSerializer, RouteListSerializer)


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



# Create your views here.
