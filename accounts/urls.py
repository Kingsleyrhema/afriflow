from django.urls import path
from .views import RegistrationView, LoginView, UserInfoView

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user-info/', UserInfoView.as_view(), name='user-info'),
]
