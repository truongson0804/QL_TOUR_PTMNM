from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from .views import *

urlpatterns = [
    path('register/', Register.as_view(), name='register'),
    path('login/', Login.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    
    # Profile
    path('<str:username>/profile/', ProfileView.as_view(), name='user_profile'),
    path('<str:username>/profile/cancel/<int:booking_id>/', cancel_booking, name='cancel_booking'),
    path('<str:username>/profile/edit/', edit_profile, name='edit_profile'),
    path('<str:username>/profile/change-password/', change_password, name='change_password'),
]