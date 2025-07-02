from django.contrib import admin
from .models import (Station,
                     Route,
                     Train,
                     TrainType,
                     Crew,
                     Journey,
                     Ticket,
                     Order)

admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Train)
admin.site.register(TrainType)
admin.site.register(Crew)
admin.site.register(Journey)
admin.site.register(Ticket)
admin.site.register(Order)
