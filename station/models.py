from django.db import models

class Station(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        verbose_name_plural = "Stations"

    def __str__(self):
        return (f"Station: {self.name},"
                f"Latitude: {self.latitude},"
                f"Longitude: {self.longitude}"
        )

# Create your models here.
