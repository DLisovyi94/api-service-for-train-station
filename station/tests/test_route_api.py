from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from station.models import Station, Route


ROUTE_URL = reverse("station:route-list")


def sample_station(name=None, **params):
    """Create and return a unique Station"""
    import uuid
    name = name or f"Station-{uuid.uuid4()}"
    defaults = {
        "name": name,
        "latitude": 50.0,
        "longitude": 30.0,
    }
    defaults.update(params)
    return Station.objects.create(**defaults)


class AdminRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@admin.com",
            password="adminpass"
        )
        self.client.force_authenticate(self.admin)

    def test_create_route_success(self):
        source = sample_station(name="Source City")
        destination = sample_station(name="Destination City")

        payload = {
            "source_id": source.id,
            "destination_id": destination.id,
            "distance": 290
        }

        response = self.client.post(ROUTE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        route = Route.objects.get(id=response.data["id"])
        self.assertEqual(route.source, source)
        self.assertEqual(route.destination, destination)
        self.assertEqual(route.distance, 290)
