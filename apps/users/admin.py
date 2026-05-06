# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    ordering = ('username',)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {
            "fields": ("first_name", "last_name", "email", "avatar")
        }),
        ("Permissions", {
            "fields": (
                "is_active",
                "role",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    def save_model(self, request, obj, form, change):
        # When saving via Django admin, ensure role mapping is applied to flags
        try:
            if hasattr(obj, 'apply_role_flags'):
                obj.apply_role_flags()
        except Exception:
            pass
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj) or [])
        # Non-superuser staff should not be able to change role
        if request.user.is_staff and not request.user.is_superuser:
            ro.append('role')
        return tuple(ro)
