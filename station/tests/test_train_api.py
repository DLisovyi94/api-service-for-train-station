import uuid
import tempfile
import os
from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from station.models import Train, TrainType
from station.serializers import TrainListSerializer, TrainDetailSerializer


TRAIN_URL = reverse("station:train-list")


def detail_url(train_id):
    return reverse("station:train-detail", args=[train_id])


def image_upload_url(train_id):
    return reverse("station:train-upload-image", args=[train_id])


def sample_train_type():
    return TrainType.objects.create(name=f"Type-{uuid.uuid4()}")


def sample_train(**params):
    defaults = {
        "name": f"Train-{uuid.uuid4()}",
        "cargo_num": 3,
        "places_in_cargo": 40,
        "train_type": sample_train_type(),
    }
    defaults.update(params)
    return Train.objects.create(**defaults)


class UnauthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_trains_requires_auth(self):
        res = self.client.get(TRAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_train_unauthenticated(self):
        ttype = sample_train_type()
        payload = {
            "name": "Test Train",
            "cargo_num": 2,
            "places_in_cargo": 50,
            "train_type": ttype.id
        }
        res = self.client.post(TRAIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com", "password123"
        )
        self.client.force_authenticate(self.user)

    def test_list_trains(self):
        train1 = sample_train(name="Express")
        train2 = sample_train(name="Regional")

        res = self.client.get(TRAIN_URL)

        trains = Train.objects.order_by("id")
        serializer = TrainListSerializer(trains, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_forbidden(self):
        ttype = sample_train_type()
        payload = {
            "name": "Forbidden Train",
            "cargo_num": 1,
            "places_in_cargo": 30,
            "train_type": ttype.id
        }
        res = self.client.post(TRAIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            "admin@test.com", "adminpass"
        )
        self.client.force_authenticate(self.admin)

    def test_create_train_success(self):
        ttype = sample_train_type()
        payload = {
            "name": f"Train-{uuid.uuid4()}",
            "cargo_num": 5,
            "places_in_cargo": 100,
            "train_type": ttype.id
        }

        res = self.client.post(TRAIN_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        train = Train.objects.get(id=res.data["id"])
        self.assertEqual(train.name, payload["name"])
        self.assertEqual(train.cargo_num, payload["cargo_num"])
        self.assertEqual(train.places_in_cargo, payload["places_in_cargo"])
        self.assertEqual(train.train_type.id, ttype.id)

    def test_retrieve_train_detail(self):
        train = sample_train()
        res = self.client.get(detail_url(train.id))

        serializer = TrainDetailSerializer(train)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], serializer.data["name"])

    def test_upload_image_to_train(self):
        train = sample_train()
        url = image_upload_url(train.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (100, 100))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            res = self.client.post(url, {"image": ntf}, format="multipart")

        train.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(train.image.path))

    def tearDown(self):
        for train in Train.objects.all():
            if train.image:
                train.image.delete()
