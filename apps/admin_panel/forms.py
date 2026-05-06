from django import forms
from django.contrib.auth import get_user_model

from apps.tours.models.tours import Tour
from apps.tours.models.tour_schedules import TourSchedule
from datetime import datetime, time

User = get_user_model()

class TourScheduleAdminForm(forms.ModelForm):
    """
    Use datetime-local widgets so UI shows native date/time picker.
    """
    class Meta:
        model = TourSchedule
        fields = "__all__"
        labels = {
            "start_day": "Từ ngày",
            "end_day": "Đến ngày",
        }
        widgets = {
            "start_day": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "end_day": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure numeric input shows Bootstrap styling and prevents negative input client-side
        if "total_slots" in self.fields:
            self.fields["total_slots"].widget = forms.NumberInput(attrs={"class": "form-control", "min": 0})

    def clean_total_slots(self):
        val = self.cleaned_data.get("total_slots")
        if val is None:
            return val
        if val < 0:
            raise forms.ValidationError("Số chỗ phải là một số không âm.")
        return val


class UserAdminForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Mật khẩu"}),
        required=False,
    )
    password2 = forms.CharField(
        label="Xác nhận mật khẩu",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Xác nhận mật khẩu"}),
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "avatar",
            "is_active",
            "groups",
            "role",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Username"})
        self.fields["email"].widget.attrs.update({"class": "form-control", "placeholder": "Email"})
        self.fields["avatar"].widget.attrs.update({"class": "form-control"})
        self.fields["groups"].widget.attrs.update({"class": "form-select"})
        # Role select
        if 'role' in self.fields:
            self.fields['role'].widget.attrs.update({'class': 'form-select'})
            try:
                # show human-friendly label
                self.fields['role'].label = 'Phân quyền'
            except Exception:
                pass

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if self.instance.pk is None and not password1:
            raise forms.ValidationError("Vui lòng nhập mật khẩu.")

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Mật khẩu và xác nhận mật khẩu không khớp.")

        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        # Apply role mapping to is_staff/is_superuser
        role = self.cleaned_data.get('role') if 'role' in self.cleaned_data else getattr(user, 'role', None)
        try:
            if role is not None:
                user.role = role
                if hasattr(user, 'apply_role_flags'):
                    user.apply_role_flags()
        except Exception:
            pass
        if commit:
            user.save()
            self.save_m2m()
        return user


class TourDurationRangeAdminForm(forms.ModelForm):
    """
    Simplified admin form for `Tour`:
    - Expose `duration_days` as a free-text field (e.g. "3 ngày 1 đêm").
    - Do NOT link duration to `TourSchedule` anymore.
    """

    class Meta:
        model = Tour
        fields = "__all__"
        labels = {
            "title": "Tiêu đề",
            "description": "Mô tả",
            "price": "Giá",
            "duration_days": "Thời lượng",
            "max_people": "Số lượng tối đa",
            "category": "Danh mục",
            "country": "Quốc gia",
            "thumbnail": "Ảnh đại diện",
            "status": "Trạng thái",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        # Simple save: duration is a plain text field; no stop-syncing performed.
        tour = super().save(commit=commit)
        return tour


class ExcelUploadForm(forms.Form):
    file = forms.FileField(label="Tệp Excel", help_text="Định dạng .xlsx hoặc .csv")

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if not f:
            raise forms.ValidationError("Vui lòng chọn tệp để tải lên.")
        name = f.name.lower()
        if not (name.endswith('.xlsx') or name.endswith('.xls') or name.endswith('.csv')):
            raise forms.ValidationError("Chỉ chấp nhận tệp .xlsx, .xls hoặc .csv")
        return f

