from .models import Booking
from django.contrib.auth import get_user_model
from ..tours.models.tour_schedules import TourSchedule
from django.db import transaction
from django.db.models import F

User = get_user_model()


def create_booking(user_id, tour_schedule_id, total_people, total_price, note=None, payment_method=None): 
    """Tạo booking và trừ `total_slots` của TourSchedule một cách nguyên tử.

    Nếu không đủ chỗ, hàm sẽ ném `ValueError` với thông báo phù hợp.
    """
    user = User.objects.get(id=user_id)

    with transaction.atomic():
        # Khóa hàng để tránh race-condition khi nhiều booking cùng lúc
        tour_schedule = TourSchedule.objects.select_for_update().get(id=tour_schedule_id)

        if total_people > tour_schedule.total_slots:
            raise ValueError(f'Chỉ còn {tour_schedule.total_slots} chỗ trống')

        # Trừ số ghế bằng F expression để an toàn trong transaction
        tour_schedule.total_slots = F('total_slots') - total_people
        tour_schedule.save(update_fields=['total_slots'])
        tour_schedule.refresh_from_db()

        booking = Booking.objects.create(
            user=user,
            tour_schedule=tour_schedule,
            total_people=total_people,
            total_price=total_price,
            note=note,
            payment_method=payment_method
        )

    return booking