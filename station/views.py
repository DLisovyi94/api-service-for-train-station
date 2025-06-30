from datetime import datetime

from django.shortcuts import render
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
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
                                 OrderListSerializer, TrainImageSerializer)


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
    ).prefetch_related("tickets", "tickets__journey__route__source", "tickets__journey__route__destination")

    serializer_class = JourneySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["route__source__name", "route__destination__name"]

    def get_queryset(self):
        queryset = (
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

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainDetailSerializer

        return TrainSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "source",
                OpenApiTypes.STR,
                description="Filter by name of source station (e.g. ?source=Kyiv)",
            ),
            OpenApiParameter(
                "destination",
                OpenApiTypes.STR,
                description="Filter by name of destination station (e.g. ?destination=Lviv)",
            ),
            OpenApiParameter(
                "date",
                OpenApiTypes.DATE,
                description="Filter by date of departure (e.g. ?date=2025-06-30)",
            ),
            OpenApiParameter(
                "train",
                OpenApiTypes.INT,
                description="Filter by train ID (e.g. ?train=5)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name"]

    @extend_schema(
        request=TrainImageSerializer,
        responses={200: TrainImageSerializer},
        methods=["POST"],
        description="Upload image to a specific train. Only admin users allowed.",
    )
    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser],
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific train"""
        train = self.get_object()
        serializer = self.get_serializer(train, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.action == "list":
            return TrainListSerializer
        if self.action == "retrieve":
            return TrainDetailSerializer
        if self.action == "upload_image":
            return TrainImageSerializer
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

    @extend_schema(
        summary="Get user's orders",
        description="Returns list of orders with tickets and "
                    "related journey, route and train data."
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

# Create your views here.
