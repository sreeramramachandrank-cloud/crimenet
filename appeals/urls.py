from django.urls import path
from .views import submit_appeal

urlpatterns = [
    path('submit/', submit_appeal, name='submit_appeal'),
]
