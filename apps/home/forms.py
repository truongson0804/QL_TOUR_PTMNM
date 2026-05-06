from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control bg-light border-0", "placeholder": "Tên của bạn"}),
            "email": forms.EmailInput(attrs={"class": "form-control bg-light border-0", "placeholder": "Địa chỉ Email"}),
            "subject": forms.TextInput(attrs={"class": "form-control bg-light border-0", "placeholder": "Tiêu đề (tuỳ chọn)"}),
            "message": forms.Textarea(attrs={"class": "form-control bg-light border-0", "rows": 4, "placeholder": "Nội dung tin nhắn..."}),
        }
