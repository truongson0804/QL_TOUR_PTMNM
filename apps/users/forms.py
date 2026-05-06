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
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})

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


class EmailVerificationForm(forms.Form):
    """Form for email verification code"""
    code = forms.CharField(
        label='Mã xác thực',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập 6 chữ số',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric'
        })
    )
    
    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isdigit():
            raise forms.ValidationError('Mã xác thực phải là 6 chữ số')
        return code


class PasswordChangeForm(DjangoPasswordChangeForm):
    """Custom password change form with Bootstrap styling"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = ' '.join([existing, 'form-control']).strip()


class ResendVerificationForm(forms.Form):
    """Form to request resend of verification code"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập email của bạn'
        })
    )


class ForgotPasswordForm(forms.Form):
    """Form for requesting password reset"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập email của bạn'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            # Không tiết lộ rằng email không tồn tại vì lý do bảo mật
            pass
        return email


class ResetPasswordForm(forms.Form):
    """Form for resetting password with new password"""
    password1 = forms.CharField(
        label='Mật khẩu mới',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập mật khẩu mới'
        })
    )
    password2 = forms.CharField(
        label='Xác nhận mật khẩu mới',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Xác nhận mật khẩu mới'
        })
    )
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Mật khẩu không khớp.')
            if len(password1) < 8:
                raise forms.ValidationError('Mật khẩu phải có ít nhất 8 ký tự.')
        return password2
