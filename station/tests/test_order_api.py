from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from station.models import (
    Station, Route, TrainType, Train,
    Journey, Ticket, Order
)

ORDER_URL = reverse("station:order-list")


def create_user(email="user@example.com", password="pass1234"):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicOrderApiTests(APITestCase):
    def test_auth_required(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateOrderApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

        self.station1 = Station.objects.create(name="Kyiv", latitude=50.45, longitude=30.52)
        self.station2 = Station.objects.create(name="Lviv", latitude=49.84, longitude=24.03)
        self.route = Route.objects.create(source=self.station1, destination=self.station2, distance=500)
        self.train_type = TrainType.objects.create(name="Passenger")
        self.train = Train.objects.create(
            name="Fast Train",
            cargo_num=5,
            places_in_cargo=20,
            train_type=self.train_type
        )
        self.journey = Journey.objects.create(
            route=self.route,
            train=self.train,
            departure_time=make_aware(datetime.now() + timedelta(days=1)),
            arrival_time=make_aware(datetime.now() + timedelta(days=1, hours=5))
        )

    def test_list_orders(self):
        order = Order.objects.create(user=self.user)
        Ticket.objects.create(order=order, cargo=1, seat=1, journey=self.journey)

        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], order.id)
        self.assertEqual(len(res.data["results"][0]["tickets"]), 1)

    def test_create_order_with_tickets(self):
        payload = {
            "tickets": [
                {
                    "cargo": 2,
                    "seat": 5,
                    "journey": self.journey.id
                },
                {
                    "cargo": 3,
                    "seat": 1,
                    "journey": self.journey.id
                }
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(id=res.data["id"])
        self.assertEqual(order.tickets.count(), 2)
        self.assertEqual(order.user, self.user)

    def test_user_sees_only_their_orders(self):
        other_user = create_user(email="other@example.com")
        Order.objects.create(user=other_user)
        Order.objects.create(user=self.user)

        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
