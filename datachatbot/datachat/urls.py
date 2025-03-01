from django.urls import path
from .views import home, prompt_2, prompt_3

urlpatterns = [
    path('', home, name='home'),  # This makes your homepage load 'home.html'
    path('p2', prompt_2, name='p2'),
    path('p3', prompt_3, name='p3')
]