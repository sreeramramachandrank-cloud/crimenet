from django.urls import path
from .views import (
    create_complaint,
    my_complaints,
    police_complaints,
    update_complaint,update_complaint_status,police_complaint_list, citizen_complaint_tracking ,
    complaint_timeline,
)

urlpatterns = [
    path('new/', create_complaint, name='create_complaint'),
    path('mine/', my_complaints, name='my_complaints'),
    path('police/', police_complaints, name='police_complaints'),
    path('update/<int:complaint_id>/', update_complaint, name='update_complaint'),
    path(
        '<int:complaint_id>/status/<str:new_status>/',
        update_complaint_status,
        name='update_complaint_status'
    ),
    path('police/', police_complaint_list, name='police_complaints'),
    path('track/', citizen_complaint_tracking, name='citizen_complaints'),
    path(
    '<int:complaint_id>/timeline/',
    complaint_timeline,
    name='complaint_timeline'
),



]

