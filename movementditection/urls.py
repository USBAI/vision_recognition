from django.urls import path
from . import views

urlpatterns = [
    path('pushupmodel', views.pushup_count_api, name='pushupmodel'),
]
