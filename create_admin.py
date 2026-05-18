import os
import django
from dotenv import load_dotenv 

load_dotenv() 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QL_tour.settings') 
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gmail.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'TanMeo2005')

if not User.objects.filter(username=username).exists():
    print(f"Đang tạo tài khoản siêu admin: {username}")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print(f"Tài khoản admin '{username}' đã tồn tại.")