from django.urls import path
from . import views
app_name = 'officials'
urlpatterns = [
    # ... existing URLs ...
    path('investigator/dashboard/', views.investigator_dashboard, name='investigator_dashboard'),
    path('investigator/active-dashboard/', views.investigator_active_dashboard, name='investigator_active_dashboard'),
    path('investigator/portal/', views.investigator_portal, name='investigator_portal'),
    path('investigator/case/<int:case_id>/', views.investigator_case_dashboard, name='investigator_case_dashboard')

]