from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from station.models import Station
from station.serializers import (StationSerializer,
                                 StationListSerializer,
                                 StationDetailSerializer)


from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend

class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        return Station.objects.annotate(
            routes_count=Count("routes_from")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return StationListSerializer
        if self.action == "retrieve":
            return StationDetailSerializer
        return StationSerializer



# Create your views here.
