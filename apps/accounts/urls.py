from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('signup/', views.student_signup, name='signup'),
    path('profile/', views.user_profile, name='profile'),
]
