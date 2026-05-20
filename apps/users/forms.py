from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm

User = get_user_model()

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mật khẩu'
        }),
        required=True,
    )
    password2 = forms.CharField(
        label='Xác nhận mật khẩu',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Xác nhận mật khẩu'
        }),
        required=True,
    )
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))

    class Meta:
        model = User
        fields = ("username", "email", "avatar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Tên đăng nhập'})
        # Translate label/help text to Vietnamese
        try:
            self.fields['username'].label = 'Tên đăng nhập'
            self.fields['username'].help_text = 'Bắt buộc. Tối đa 150 ký tự. Chỉ gồm chữ cái, chữ số và các ký tự @/./+/-/_.'
        except Exception:
            pass

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Mật khẩu và xác nhận mật khẩu không khớp.')
        return password2


class ProfileForm(forms.ModelForm):
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "avatar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add bootstrap classes
        for name, field in self.fields.items():
            if name == 'avatar':
                continue
            widget = field.widget
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = ' '.join([existing, 'form-control']).strip()
 
        # Ensure username label/help_text localized
        if 'username' in self.fields:
            try:
                self.fields['username'].label = 'Tên đăng nhập'
                self.fields['username'].help_text = 'Bắt buộc. Tối đa 150 ký tự. Chỉ gồm chữ cái, chữ số và các ký tự @/./+/-/_.'
            except Exception:
                pass


class PasswordChangeForm(DjangoPasswordChangeForm):
    """Custom password change form with Bootstrap styling"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = ' '.join([existing, 'form-control']).strip()
