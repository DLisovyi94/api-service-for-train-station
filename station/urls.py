from django.urls import path, include
from rest_framework import routers

from station.views import (StationViewSet,
                           RouteViewSet, JourneyViewSet)

router = routers.DefaultRouter()
router.register("stations", StationViewSet)
router.register("routes", RouteViewSet)
router.register("journeys", JourneyViewSet)

urlpatterns = [path("", include(router.urls))]

app_name = "station"