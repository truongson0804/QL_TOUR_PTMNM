from django.db import models
from .continent import Continent

class Country(models.Model):
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=255)
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.name}"