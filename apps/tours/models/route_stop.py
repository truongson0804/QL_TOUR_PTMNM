from django.db import models
from .tour_stop import TourStop
from .tours import Tour

class RouteStop(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    stop = models.ForeignKey(TourStop, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    stay_minutes = models.PositiveIntegerField(null=True)
