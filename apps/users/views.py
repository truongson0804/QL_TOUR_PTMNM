from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from . import forms
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.bookings.models import Booking
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.contrib.auth import get_user_model

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

            # Gửi mã xác thực email tự động
            success, message = send_verification_email(user)
            if success:
                messages.success(request, 'Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản.')
                # Login người dùng tự động sau khi đăng ký
                from django.contrib.auth import authenticate, login as auth_login
                authenticated_user = authenticate(username=user.username, password=password)
                if authenticated_user:
                    auth_login(request, authenticated_user)
                return redirect('verify_email')
            else:
                messages.warning(request, f'Đăng ký thành công nhưng lỗi gửi email xác thực: {message}')
                return redirect('verify_email')
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


def send_verification_email(user):
    """Send verification code to user's email"""
    try:
        code = user.generate_verification_code()
        subject = 'Mã xác thực email QL Tours'
        message = f"""
Xin chào {user.first_name or user.username},

Mã xác thực email của bạn là: {code}

Mã này sẽ hết hạn sau 15 phút.

Nếu bạn không yêu cầu xác thực email, vui lòng bỏ qua tin nhắn này.

Trân trọng,
QL Tours Team
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True, "Mã xác thực đã được gửi đến email của bạn"
    except Exception as e:
        return False, f"Lỗi khi gửi email: {str(e)}"


@login_required(login_url='login')
def send_verification_code(request):
    """Send verification code to logged-in user's email"""
    user = request.user
    
    if user.email_verified:
        messages.info(request, 'Email của bạn đã được xác thực.')
        return redirect('user_profile', username=user.username)
    
    if request.method == 'POST':
        success, message = send_verification_email(user)
        if success:
            messages.success(request, message)
            return redirect('verify_email')
        else:
            messages.error(request, message)
    
    return render(request, 'send_verification_code.html', {'user': user})


@login_required(login_url='login')
def verify_email(request):
    """Verify email with code"""
    user = request.user
    
    if user.email_verified:
        messages.info(request, 'Email của bạn đã được xác thực.')
        return redirect('user_profile', username=user.username)
    
    if request.method == 'POST':
        form = forms.EmailVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            success, message = user.verify_email(code)
            
            if success:
                messages.success(request, message)
                return redirect('user_profile', username=user.username)
            else:
                messages.error(request, message)
                form.add_error('code', message)
    else:
        form = forms.EmailVerificationForm()
    
    # Kiểm tra xem mã đã được gửi chưa
    has_code = user.email_verification_code is not None
    code_expired = user.is_verification_code_expired() if has_code else True
    
    context = {
        'form': form,
        'email': user.email,
        'has_code': has_code,
        'code_expired': code_expired,
    }
    
    return render(request, 'verify_email.html', context)


@login_required(login_url='login')
def resend_verification_code(request):
    """Resend verification code"""
    user = request.user
    
    if user.email_verified:
        messages.info(request, 'Email của bạn đã được xác thực.')
        return redirect('user_profile', username=user.username)
    
    # Check if user can resend (not too frequently)
    if not user.is_verification_code_expired():
        remaining = (user.verification_code_expires_at - timezone.now()).seconds // 60
        messages.warning(request, f'Vui lòng chờ {remaining} phút trước khi yêu cầu gửi lại.')
        return redirect('verify_email')
    
    success, message = send_verification_email(user)
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('verify_email')


def send_password_reset_email(user):
    """Send password reset link to user's email"""
    try:
        token = user.generate_password_reset_token()
        reset_url = f"http://localhost:8000/auth/reset-password/{token}/"  # TODO: Thay bằng domain thực
        
        subject = 'Link Đặt Lại Mật Khẩu - QL Tours'
        message = f"""
Xin chào {user.first_name or user.username},

Bạn đã yêu cầu đặt lại mật khẩu cho tài khoản của mình.

Vui lòng bấm vào link dưới đây để đặt lại mật khẩu:
{reset_url}

Link này sẽ hết hạn sau 1 giờ.

Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua tin nhắn này.

Trân trọng,
QL Tours Team
"""
        # Use Mailtrap for forgot-password emails if explicitly enabled and configured
        if getattr(settings, 'FORGOT_PASSWORD_USE_MAILTRAP', False) and getattr(settings, 'MAILTRAP_USER', '') and getattr(settings, 'MAILTRAP_PASSWORD', ''):
            conn = get_connection(
                host=settings.MAILTRAP_HOST,
                port=settings.MAILTRAP_PORT,
                username=settings.MAILTRAP_USER,
                password=settings.MAILTRAP_PASSWORD,
                use_tls=getattr(settings, 'MAILTRAP_USE_TLS', False),
                fail_silently=False,
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                connection=conn,
            )
        else:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        return True, "Link đặt lại mật khẩu đã được gửi đến email của bạn"
    except Exception as e:
        return False, f"Lỗi khi gửi email: {str(e)}"


def forgot_password(request):
    """Request password reset"""
    # Nếu người dùng đã login, redirect về profile
    if request.user.is_authenticated:
        messages.info(request, 'Bạn đã đăng nhập rồi.')
        return redirect('user_profile', username=request.user.username)
    
    if request.method == 'POST':
        form = forms.ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                User = get_user_model()
                user = User.objects.get(email=email)
                success, message = send_password_reset_email(user)
                if success:
                    messages.success(request, message)
                    return redirect('login')
                else:
                    messages.error(request, message)
            except User.DoesNotExist:
                # Không tiết lộ rằng email không tồn tại vì lý do bảo mật
                messages.success(request, 'Nếu email tồn tại, link đặt lại mật khẩu sẽ được gửi.')
                return redirect('login')
    else:
        form = forms.ForgotPasswordForm()
    
    return render(request, 'forgot_password.html', {'form': form})


def reset_password_confirm(request, token):
    """Reset password with token"""
    # Nếu người dùng đã login, logout trước
    if request.user.is_authenticated:
        logout(request)
    
    try:
        User = get_user_model()
        user = User.objects.get(password_reset_token=token)
    except User.DoesNotExist:
        messages.error(request, 'Token không hợp lệ hoặc không tồn tại.')
        return redirect('login')
    
    # Kiểm tra token
    valid, message = user.verify_password_reset_token(token)
    if not valid:
        messages.error(request, message)
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = forms.ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password1']
            user.set_password(password)
            user.password_reset_token = None
            user.password_reset_token_expires_at = None
            user.save()
            
            messages.success(request, 'Mật khẩu đã được đặt lại thành công. Vui lòng đăng nhập lại.')
            return redirect('login')
    else:
        form = forms.ResetPasswordForm()
    
    return render(request, 'reset_password_confirm.html', {'form': form, 'token': token})


