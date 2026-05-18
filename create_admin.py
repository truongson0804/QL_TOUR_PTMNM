import os
import django

os.environ.setdefault('DJANGO_SETTINGS_SETTINGS_MODULE', 'tên_thư_mục_chứa_settings.settings') # Thay bằng đường dẫn settings của bạn
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Lấy thông tin Admin từ biến môi trường (Bảo mật, không lo lộ pass trên GitHub)
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'MậtKhẩuAdminCủaBạn123')

if not User.objects.filter(username=username).exists():
    print(f"Đang tạo tài khoản siêu admin: {username}")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print(f"Tài khoản admin '{username}' đã tồn tại.")