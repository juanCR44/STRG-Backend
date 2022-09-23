from django.urls import path
from . import views

urlpatterns = [
    path('', views.apiOverView, name='api-overview'),
    path('test', views.testYolo, name = 'test-yolo')
]