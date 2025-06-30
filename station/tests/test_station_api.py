from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from station.models import Station

User = get_user_model()


class StationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.station_url = reverse("station:station-list")
        self.user = User.objects.create_user(email="user@test.com", password="testpass123")
        self.admin = User.objects.create_superuser(email="admin@test.com", password="adminpass")

    def test_list_stations_anonymous(self):
        Station.objects.create(name="Kyiv", latitude=50.45, longitude=30.52)
        response = self.client.get(self.station_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_station_anonymous(self):
        payload = {"name": "Odessa", "latitude": 46.47, "longitude": 30.73}
        response = self.client.post(self.station_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_station_authenticated(self):
        self.client.force_authenticate(self.user)
        payload = {"name": "Lviv", "latitude": 49.84, "longitude": 24.02}
        response = self.client.post(self.station_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_station_admin(self):
        self.client.force_authenticate(self.admin)
        payload = {"name": "Dnipro", "latitude": 48.45, "longitude": 34.98}
        response = self.client.post(self.station_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Station.objects.filter(name="Dnipro").exists())
