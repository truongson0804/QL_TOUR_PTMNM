from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
import string

def user_avatar_path(instance, filename):
    return f"avatars/user_{instance.id}/{filename}"

class User(AbstractUser):
    avatar = models.ImageField(upload_to=user_avatar_path, default='avatars/default.jpg', blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_expires_at = models.DateTimeField(blank=True, null=True)
    
    # Password reset fields
    password_reset_token = models.CharField(max_length=100, blank=True, null=True, unique=True)
    password_reset_token_expires_at = models.DateTimeField(blank=True, null=True)
    
    def generate_verification_code(self):
        """Generate a 6-digit verification code"""
        code = ''.join(secrets.choice(string.digits) for _ in range(6))
        self.email_verification_code = code
        self.verification_code_expires_at = timezone.now() + timedelta(minutes=15)
        self.save()
        return code
    
    def verify_email(self, code):
        """Verify email with code"""
        if not self.email_verification_code:
            return False, "Không có mã xác thực"
        
        if self.verification_code_expires_at and timezone.now() > self.verification_code_expires_at:
            self.email_verification_code = None
            self.save()
            return False, "Mã xác thực đã hết hạn"
        
        if self.email_verification_code == code:
            self.email_verified = True
            self.email_verification_code = None
            self.verification_code_expires_at = None
            self.save()
            return True, "Xác thực email thành công"
        
        return False, "Mã xác thực không chính xác"
    
    def is_verification_code_expired(self):
        """Check if verification code is expired"""
        if not self.verification_code_expires_at:
            return True
        return timezone.now() > self.verification_code_expires_at
    
    def generate_password_reset_token(self):
        """Generate a random password reset token"""
        token = secrets.token_urlsafe(50)
        self.password_reset_token = token
        self.password_reset_token_expires_at = timezone.now() + timedelta(hours=1)
        self.save()
        return token
    
    def verify_password_reset_token(self, token):
        """Verify password reset token"""
        if not self.password_reset_token:
            return False, "Không có token reset mật khẩu"
        
        if self.password_reset_token_expires_at and timezone.now() > self.password_reset_token_expires_at:
            self.password_reset_token = None
            self.password_reset_token_expires_at = None
            self.save()
            return False, "Token reset mật khẩu đã hết hạn"
        
        if self.password_reset_token == token:
            return True, "Token hợp lệ"
        
        return False, "Token không hợp lệ"
    
    def is_password_reset_token_expired(self):
        """Check if password reset token is expired"""
        if not self.password_reset_token_expires_at:
            return True
        return timezone.now() > self.password_reset_token_expires_at

    # Role field: manage simple role assignment across the app.
    ROLE_USER = 'user'
    ROLE_STAFF = 'staff'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_USER, 'Người dùng'),
        (ROLE_STAFF, 'Nhân viên'),
        (ROLE_ADMIN, 'Quản trị'),
    ]

    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=ROLE_USER)

    def apply_role_flags(self):
        """Sync `is_staff`/`is_superuser` flags from the `role` value.

        Call this before saving when role may have changed.
        """
        if getattr(self, 'role', None) == self.ROLE_ADMIN:
            self.is_superuser = True
            self.is_staff = True
        elif getattr(self, 'role', None) == self.ROLE_STAFF:
            self.is_superuser = False
            self.is_staff = True
        else:
            self.is_superuser = False
            self.is_staff = False
