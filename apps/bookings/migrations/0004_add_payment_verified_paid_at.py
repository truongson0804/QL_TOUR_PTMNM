"""Generated migration to add payment verification fields to Booking."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0003_booking_note_booking_payment_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="payment_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="booking",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
