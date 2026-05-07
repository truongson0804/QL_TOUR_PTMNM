#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QL_tour.settings')
import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from apps.users.views import send_password_reset_email

print('EMAIL_BACKEND=', getattr(settings, 'EMAIL_BACKEND', None))
print('EMAIL_HOST=', getattr(settings, 'EMAIL_HOST', None))
print('EMAIL_PORT=', getattr(settings, 'EMAIL_PORT', None))
print('EMAIL_HOST_USER=', getattr(settings, 'EMAIL_HOST_USER', None))

User = get_user_model()
u = User.objects.filter().first()
print('found user:', bool(u))
if not u:
    print('No user in DB to test')
else:
    res = send_password_reset_email(u)
    print('send_password_reset_email ->', res)
