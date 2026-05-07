from django.db import models
from .tours import Tour

class TourImage(models.Model):
    image = models.ImageField(upload_to='tour_images/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    tour = models.ForeignKey(Tour, related_name='images', on_delete=models.CASCADE)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.caption or f"Image for {self.tour_id}"
