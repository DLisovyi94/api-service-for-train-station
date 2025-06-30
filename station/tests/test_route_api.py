import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from station.models import Station, Route
from station.serializers import RouteListSerializer, RouteDetailSerializer


ROUTE_URL = reverse("station:route-list")


def detail_url(route_id):
    return reverse("station:route-detail", args=[route_id])


def sample_station(**params):
    defaults = {
        "name": f"Station-{uuid.uuid4()}",
        "latitude": 50.0,
        "longitude": 30.0
    }
    defaults.update(params)
    return Station.objects.create(**defaults)


def sample_route(**params):
    source = params.pop("source", sample_station(name=f"Source-{uuid.uuid4()}"))
    destination = params.pop("destination", sample_station(name=f"Destination-{uuid.uuid4()}"))
    distance = params.pop("distance", 100)
    return Route.objects.create(source=source, destination=destination, distance=distance)


class UnauthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_routes_requires_auth(self):
        res = self.client.get(ROUTE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_route_forbidden(self):
        s1 = sample_station()
        s2 = sample_station()
        payload = {
            "source_id": s1.id,
            "destination_id": s2.id,
            "distance": 150
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpass"
        )
        self.client.force_authenticate(self.user)

    def test_list_routes(self):
        r1 = sample_route()
        r2 = sample_route()

        res = self.client.get(ROUTE_URL)

        routes = Route.objects.order_by("id")
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_route_forbidden(self):
        s1 = sample_station()
        s2 = sample_station()
        payload = {
            "source_id": s1.id,
            "destination_id": s2.id,
            "distance": 200
        }
        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_routes_by_source_and_destination(self):
        source1 = sample_station(name="Kyiv")
        destination1 = sample_station(name="Lviv")
        route1 = sample_route(source=source1, destination=destination1)

        sample_route(source=sample_station(name="Odesa"), destination=sample_station(name="Kharkiv"))

        res = self.client.get(ROUTE_URL, {
            "source": "Kyiv",
            "destination": "Lviv"
        })

        serializer = RouteListSerializer(route1)
        self.assertIn(serializer.data, res.data)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpass"
        )
        self.client.force_authenticate(self.admin)

    def test_create_route_success(self):
        s1 = sample_station()
        s2 = sample_station()
        payload = {
            "source_id": s1.id,
            "destination_id": s2.id,
            "distance": 300
        }

        res = self.client.post(ROUTE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        route = Route.objects.get(id=res.data["id"])
        self.assertEqual(route.source.id, s1.id)
        self.assertEqual(route.destination.id, s2.id)
        self.assertEqual(route.distance, 300)

    def test_retrieve_route_detail(self):
        route = sample_route()
        res = self.client.get(detail_url(route.id))

        serializer = RouteDetailSerializer(route)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["distance"], serializer.data["distance"])
