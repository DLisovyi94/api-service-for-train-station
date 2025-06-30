import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from station.models import Station
from station.serializers import StationListSerializer, StationDetailSerializer


STATION_URL = reverse("station:station-list")


def detail_url(station_id):
    return reverse("station:station-detail", args=[station_id])


def sample_station(**params):
    defaults = {
        "name": f"Station-{uuid.uuid4()}",
        "latitude": 50.0,
        "longitude": 30.0
    }
    defaults.update(params)
    return Station.objects.create(**defaults)


class UnauthenticatedStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_stations_requires_auth(self):
        """GET /stations/ should return 401 if user is not authenticated"""
        res = self.client.get(STATION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_station_forbidden(self):
        payload = {
            "name": "Unauthorized Station",
            "latitude": 50.0,
            "longitude": 30.0
        }
        res = self.client.post(STATION_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpass"
        )
        self.client.force_authenticate(self.user)

    def test_list_stations(self):
        sample_station(name="Kyiv")
        sample_station(name="Lviv")

        res = self.client.get(STATION_URL)

        stations = Station.objects.order_by("id")
        serializer = StationListSerializer(stations, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_station_detail(self):
        station = sample_station(name="Odessa", latitude=46.47, longitude=30.73)

        url = detail_url(station.id)
        res = self.client.get(url)

        serializer = StationDetailSerializer(station)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], serializer.data["name"])

    def test_create_station_forbidden(self):
        payload = {
            "name": "User Station",
            "latitude": 48.92,
            "longitude": 24.71
        }
        res = self.client.post(STATION_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminStationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpass"
        )
        self.client.force_authenticate(self.admin)

    def test_create_station_success(self):
        payload = {
            "name": f"Admin Station {uuid.uuid4()}",
            "latitude": 49.0,
            "longitude": 32.0
        }
        res = self.client.post(STATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        station = Station.objects.get(id=res.data["id"])
        for key in payload:
            self.assertEqual(payload[key], getattr(station, key))
