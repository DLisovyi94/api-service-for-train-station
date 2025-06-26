from django.core.exceptions import ValidationError
from django.db import models

class Station(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        verbose_name_plural = "Stations"

    def __str__(self):
        return (f"Station: {self.name},"
                f"Latitude: {self.latitude},"
                f"Longitude: {self.longitude}"
        )


class Route(models.Model):
    source = models.ForeignKey(
        Station,
        related_name="routes_from",
        on_delete=models.CASCADE)
    destination = models.ForeignKey(
        Station,
        related_name="routes_to",
        on_delete=models.CASCADE)
    distance = models.IntegerField()

    class Meta:
        verbose_name_plural = "Routes"

    def __str__(self):
        return (f"Route: {self.source} - {self.destination},"
                f"distance: {self.distance}")


class Train(models.Model):
    name = models.CharField(max_length=255)
    cargo_num = models.IntegerField()
    places_in_cargo = models.IntegerField()
    train_type = models.ForeignKey(
        "TrainType",
        related_name="trains",
        on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Trains"

    @property
    def capacity_train(self) -> int:
        return self.cargo_num * self.places_in_cargo

    def __str__(self):
        return f"Train: {self.name}"


class TrainType(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "TrainTypes"

    def __str__(self):
        return f"TrainType: {self.name}"


class Journey(models.Model):
    route = models.ForeignKey(
        "Route",
        related_name="journeys",
        on_delete=models.CASCADE)
    train = models.ForeignKey(
        Train,
        related_name="journeys",
        on_delete=models.CASCADE)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        verbose_name_plural = "Journeys"

    def clean(self):
        if self.arrival_time <= self.departure_time:
            raise ValidationError("Arrival time must be after departure time.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (f"Journey from {self.route.source.name} "
                f"to {self.route.destination.name} "
                f"at {self.departure_time.strftime('%Y-%m-%d %H:%M')}")
