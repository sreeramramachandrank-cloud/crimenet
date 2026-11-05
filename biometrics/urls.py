from django.urls import path
from .views import biometric_search
from .views import forensic_dashboard
from .views import enroll_biometrics as biometric_enroll
urlpatterns = [
    path('search/', biometric_search, name='biometric_search'),
    path('analytics/', forensic_dashboard, name='forensic_dashboard'),
    path('enroll/<int:user_id>/', biometric_enroll, name='biometric_enroll'),
]
