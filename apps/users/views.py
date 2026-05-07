from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import View
from . import forms
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, update_session_auth_hash, get_user_model
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.bookings.models import Booking
from django.contrib import messages
from django.views.decorators.http import require_POST

class Register(View):
    def get(self, request):
        form = forms.RegisterForm()

        return render(request, 'register.html', {'form': form})
    
    def post(self, request):
        form = forms.RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save(commit=False)  # Chưa lưu vào DB
            user.is_active = True
            
            # Mã hóa mật khẩu
            password = form.cleaned_data.get('password1')
            if password:
                user.set_password(password)
            
            # Lấy avatar từ request.FILES
            avatar = request.FILES.get("avatar")
            if avatar:
                user.avatar = avatar

            user.save()  # Lưu một lần duy nhất

            # Add Group
            try:
                customer_group = Group.objects.get(name="Customer")
                user.groups.add(customer_group)
            except Group.DoesNotExist:
                pass

            # Login người dùng tự động sau khi đăng ký
            from django.contrib.auth import authenticate, login as auth_login
            authenticated_user = authenticate(username=user.username, password=password)
            if authenticated_user:
                auth_login(request, authenticated_user)
            messages.success(request, 'Đăng ký thành công!')
            return redirect('home')
        else:
            # In lỗi ra Terminal để debug
            print("=== LỖI ĐĂNG KÝ ===")
            print(form.errors)
            print("===================")
        return render(request, 'register.html', {'form': form}) 

class Login(LoginView):
    template_name= 'login.html'

    def get_success_url(self) -> str:
        return reverse_lazy('home')

class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect(reverse('login'))


class ProfileView(View):
    """Show user profile with booking history."""
    def get(self, request, username):
        # Load the user by username
        from django.contrib.auth import get_user_model
        User = get_user_model()
        profile_user = get_object_or_404(User, username=username)

        # User's bookings, newest first
        bookings = Booking.objects.filter(user=profile_user).select_related('tour_schedule', 'tour_schedule__tour').order_by('-create_at')

        # Determine if each booking can be cancelled from the UI (start time in future and not already cancelled)
        now = timezone.now()
        for b in bookings:
            try:
                start = b.tour_schedule.start_day
            except Exception:
                start = None
            # can cancel only if not already cancelled and start exists and is in the future
            b.can_cancel = (b.status != 'CANCELLED') and (start is not None and start > now)

        # Count confirmed bookings for the profile user
        try:
            confirmed_count = bookings.filter(status='CONFIRMED').count()
        except Exception:
            confirmed_count = 0

        return render(request, 'profile.html', {
            'profile_user': profile_user,
            'bookings': bookings,
            'confirmed_count': confirmed_count,
        })


@login_required(login_url='login')
def edit_profile(request, username):
    # Only allow users to edit their own profile
    if request.user.username != username:
        messages.error(request, 'Bạn không có quyền sửa profile này.')
        return redirect('user_profile', username=username)

    if request.method == 'POST':
        form = forms.ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cập nhật thông tin tài khoản thành công.')
            return redirect('user_profile', username=user.username)
    else:
        form = forms.ProfileForm(instance=request.user)

    return render(request, 'profile_edit.html', {'form': form})


@login_required(login_url='login')
def change_password(request, username):
    # Only allow profile owner to change password
    if request.user.username != username:
        messages.error(request, 'Bạn không có quyền thay đổi mật khẩu cho tài khoản này.')
        return redirect('user_profile', username=username)

    if request.method == 'POST':
        form = forms.PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user authenticated after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Đã đổi mật khẩu thành công.')
            return redirect('user_profile', username=user.username)
    else:
        form = forms.PasswordChangeForm(user=request.user)

    return render(request, 'password_change_form.html', {'form': form})


@login_required(login_url='login')
@require_POST
def cancel_booking(request, username, booking_id):
    # Only allow the profile owner to cancel their bookings
    if request.user.username != username:
        messages.error(request, 'Bạn không có quyền hủy booking này.')
        return redirect('user_profile', username=username)

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Only cancel if not already cancelled
    if booking.status == 'CANCELLED':
        messages.info(request, 'Booking đã được hủy trước đó.')
        return redirect('user_profile', username=username)

    # Optional guard: don't allow cancelling bookings that already started (start_day in past)
    now = timezone.now()
    try:
        start = booking.tour_schedule.start_day
        if start and start <= now:
            messages.error(request, 'Không thể hủy booking đã bắt đầu hoặc đã kết thúc.')
            return redirect('user_profile', username=username)
    except Exception:
        pass

    booking.status = 'CANCELLED'
    booking.save()
    messages.success(request, 'Đã hủy booking thành công.')
    return redirect('user_profile', username=username)





