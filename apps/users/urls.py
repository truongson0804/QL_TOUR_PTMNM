from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from .views import *

urlpatterns = [
    path('register/', Register.as_view(), name='register'),
    path('login/', Login.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    
    # Email verification
    path('email/send-code/', send_verification_code, name='send_verification_code'),
    path('email/verify/', verify_email, name='verify_email'),
    path('email/resend-code/', resend_verification_code, name='resend_verification_code'),
    
    # Password reset
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', reset_password_confirm, name='reset_password_confirm'),
    
    # Profile
    path('<str:username>/profile/', ProfileView.as_view(), name='user_profile'),
    path('<str:username>/profile/cancel/<int:booking_id>/', cancel_booking, name='cancel_booking'),
    path('<str:username>/profile/edit/', edit_profile, name='edit_profile'),
    path('<str:username>/profile/change-password/', change_password, name='change_password'),
]