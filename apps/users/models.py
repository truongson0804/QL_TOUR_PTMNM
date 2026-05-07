from django.contrib.auth.models import AbstractUser
from django.db import models

def user_avatar_path(instance, filename):
    return f"avatars/user_{instance.id}/{filename}"

class User(AbstractUser):
    avatar = models.ImageField(upload_to=user_avatar_path, default='avatars/default.jpg', blank=True)

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
