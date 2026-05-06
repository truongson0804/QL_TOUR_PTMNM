from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class TourSchedule(models.Model):
    tour = models.ForeignKey('Tour', on_delete=models.CASCADE)
    start_day = models.DateTimeField()
    end_day = models.DateTimeField()
    # total_slots must be non-negative
    total_slots = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def clean(self):
        # Model-level validation to ensure non-negative slot count.
        if self.total_slots is not None and self.total_slots < 0:
            raise ValidationError({'total_slots': 'Số chỗ phải là một số không âm.'})

    def __str__(self):
        return f"{self.tour.title} from {self.start_day} to {self.end_day}"