from django.urls import path
from .views import home

urlpatterns = [
    path('', home, name='home'),  # This makes your homepage load 'home.html'
]