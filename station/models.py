from django.conf import settings
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


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self):
        return self.first_name + " " + self.last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


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
    crew = models.ManyToManyField(Crew, related_name="journeys")

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


class Ticket(models.Model):
    cargo = models.IntegerField()
    seat = models.IntegerField()
    journey = models.ForeignKey(
        Journey,
        related_name="tickets",
        on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        "Order",
        related_name="tickets",
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("cargo", "seat", "journey")
        verbose_name_plural = "Tickets"

    def __str__(self):
        return (
            f"Ticket - {self.journey.train.name} ,"
            f"cargo: {self.cargo}, seat: {self.seat},"
            f"order: {self.order.user}"
        )

    @staticmethod
    def validate_ticket(cargo, seat, journey, error_to_raise):
        train = journey.train
        if not (1 <= cargo <= train.cargo_num):
            raise error_to_raise({
                "cargo": f"Cargo number must be in range 1–{train.cargo_num}"
            })
        if not (1 <= seat <= train.places_in_cargo):
            raise error_to_raise({
                "seat": f"Seat number must be in range 1–{train.places_in_cargo}"
            })

        if Ticket.objects.filter(
            journey=journey,
            cargo=cargo,
            seat=seat
        ).exists():
            raise error_to_raise({
                "seat": "This seat is already taken in this journey"
            })

    def clean(self):
        Ticket.validate_ticket(
            self.cargo,
            self.seat,
            self.journey,
            ValidationError,
        )

    def save(
        self,
        *args,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    class Meta:
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order by {self.user} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
