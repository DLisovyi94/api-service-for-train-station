from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from station.models import Station, Route, Train, Journey, TrainType

JOURNEY_URL = reverse("station:journey-list")

def create_user(email="user@example.com", password="testpass123"):
    return get_user_model().objects.create_user(email=email, password=password)

class PublicJourneyApiTests(APITestCase):
    def test_auth_required(self):
        res = self.client.get(JOURNEY_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_journey_unauthorized(self):
        res = self.client.post(JOURNEY_URL, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateJourneyApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.user.is_staff = True  # 🔑 щоб мати права на створення
        self.user.save()
        self.client.force_authenticate(self.user)

        self.station1 = Station.objects.create(name="Kyiv", latitude=50.45, longitude=30.52)
        self.station2 = Station.objects.create(name="Lviv", latitude=49.84, longitude=24.03)

        self.route = Route.objects.create(source=self.station1, destination=self.station2, distance=500)

        self.train_type = TrainType.objects.create(name="Passenger")
        self.train = Train.objects.create(
            name="Express",
            cargo_num=10,
            places_in_cargo=50,
            train_type=self.train_type
        )

    def test_list_journeys(self):
        Journey.objects.create(
            route=self.route,
            train=self.train,
            departure_time=make_aware(datetime.now() + timedelta(days=1)),
            arrival_time=make_aware(datetime.now() + timedelta(days=1, hours=6))
        )

        res = self.client.get(JOURNEY_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        journey_data = res.data[0]
        self.assertIn("available_places", journey_data)
        self.assertEqual(journey_data["train"], self.train.name)
        self.assertEqual(journey_data["route"], f"{self.route.source.name} → {self.route.destination.name}")

    def test_create_journey_success(self):
        payload = {
            "route_id": self.route.id,
            "train_id": self.train.id,
            "departure_time": make_aware(datetime.now() + timedelta(days=1)).isoformat(),
            "arrival_time": make_aware(datetime.now() + timedelta(days=1, hours=5)).isoformat(),
        }

        res = self.client.post(JOURNEY_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Journey.objects.count(), 1)

        journey = Journey.objects.first()
        self.assertEqual(journey.route, self.route)
        self.assertEqual(journey.train, self.train)
