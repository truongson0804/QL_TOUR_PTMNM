from django.db import models
from ..bookings.models import Booking

class Status(models.TextChoices):
    UNPAID = 'UNPAID', 'Chưa trả'
    PAID = 'PAID', 'Đã trả'
    FAILED = 'FAILED', 'Thất bại'

class Methods(models.TextChoices):
    COD = 'COD'
    VNPay = 'VNPay'

class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    payment_method = models.CharField(choices=Methods, default=Methods.COD)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=Status, default=Status.UNPAID)
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Booking {self.booking.id}"