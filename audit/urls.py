from django.urls import path
from .views import audit_timeline

urlpatterns = [
    path('timeline/', audit_timeline, name='audit_timeline'),
]
