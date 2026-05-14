from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.response import Response
from apps.tours.models.tours import Tour
from apps.tours.models.tour_schedules import TourSchedule
from .servers import create_booking

def booking_confirm(request, id):
    tour_schedule = get_object_or_404(TourSchedule, id=id)
    
    # Bảo vệ bổ sung: kiểm tra nếu hết chỗ
    if tour_schedule.total_slots <= 0:
        messages.error(request, 'Tour này đã hết chỗ!')
        return redirect('tour_detail', id=tour_schedule.tour.id)
    
    context = {
        'tour_schedule': tour_schedule,
        'tour': tour_schedule.tour
    }
    return render(request, 'booking.html', context)

@login_required(login_url='login')
def booking(request):
    if request.method == 'POST':
        user = request.user
        tour_schedule_id = request.POST.get('tour_schedule_id')
        quantity_raw = request.POST.get('quantity')
        payment_method = request.POST.get('payment')
        notes = request.POST.get('notes')

        # Lấy tour schedule
        try:
            tour_schedule = TourSchedule.objects.get(id=tour_schedule_id)
        except TourSchedule.DoesNotExist:
            messages.error(request, 'Tour không tồn tại')
            return redirect('tour_list')

        # Parse số lượng
        try:
            quantity = int(quantity_raw)
        except (TypeError, ValueError):
            messages.error(request, 'Dữ liệu không hợp lệ')
            return redirect('booking_confirm', id=tour_schedule_id)

        if quantity <= 0:
            messages.error(request, 'Số lượng phải lớn hơn 0')
            return redirect('booking_confirm', id=tour_schedule_id)

        # Kiểm tra số ghế còn (kiểm tra nhanh, create_booking vẫn đảm bảo nguyên tử)
        if quantity > tour_schedule.total_slots:
            messages.error(request, f'Chỉ còn {tour_schedule.total_slots} chỗ trống')
            return redirect('booking_confirm', id=tour_schedule_id)

        # Calculate total price
        total_price = tour_schedule.tour.price * quantity

        # Tạo booking (create_booking sẽ xử lý trừ ghế nguyên tử và ném ValueError nếu thiếu chỗ)
        try:
            booking = create_booking(
                user_id=user.id,
                tour_schedule_id=tour_schedule_id,
                total_people=quantity,
                total_price=total_price,
                note=notes,
                payment_method=payment_method
            )
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('booking_confirm', id=tour_schedule_id)

        messages.success(request, 'Đặt tour thành công!')
        return redirect('tour_detail', id=tour_schedule.tour.id)

    return redirect('tour_list')

