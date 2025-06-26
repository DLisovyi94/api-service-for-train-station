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
    train_type = models.ForeignKey("TrainType", on_delete=models.CASCADE)

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