from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from . import views

urlpatterns = [
    path('', views.apiOverView, name='api-overview'),
    path('detect', views.detect, name = 'detect'),
    path('registeruser', views.registerUser, name = 'register-user'),
    path('loginuser', views.loginUser, name = 'login-user'),
    path('detectstate', views.detectState, name = 'detect-state'),
    path('registerdetection', views.registerDetection, name = 'register-detection'),
    path('getdetection', views.getDetection, name = 'get-detection'),
]