from django.urls import path

from . import views


from .views import (
    admin_dashboard,
    users_list,
    role_requests,
    approve_role,
    reject_role,
    block_user,
    unblock_user,
    appeals_list,
    review_appeal,
    analytics_dashboard,  
    complaint_trends,  
    misuse_alerts,
    sla_check,
    export_complaints,
    audit_logs,
)  
from .views import biometric_logs
from .views import user_details

  


urlpatterns = [
    path('', admin_dashboard, name='admin_dashboard'),
    path('users/', users_list, name='admin_users_list'),

    path('role-requests/', role_requests, name='admin_role_requests'),
    path('approve/<int:user_id>/', approve_role, name='admin_approve_role'),
    path('reject/<int:user_id>/', reject_role, name='admin_reject_role'),

    path('users/block/<int:user_id>/', block_user, name='admin_block_user'),
    path('users/unblock/<int:user_id>/', unblock_user, name='admin_unblock_user'),
    path('appeals/', appeals_list, name='admin_appeals'),
    path('appeals/<int:appeal_id>/', review_appeal, name='admin_review_appeal'),
    path('analytics/', analytics_dashboard, name='admin_analytics'),
    path('trends/', complaint_trends, name='admin_trends'),
    path('alerts/', misuse_alerts, name='admin_alerts'),
    path('sla-check/', sla_check, name='admin_sla_check'),
    path('export/', export_complaints, name='admin_export'),
    path('biometric-logs/', biometric_logs, name='admin_biometric_logs'),
    path('audit-logs/', audit_logs, name='admin_audit_logs'),
    path('misuse-alerts/', misuse_alerts, name='admin_misuse_alerts'),
    path('users/<int:user_id>/details/', views.user_details, name='admin_view_user_details'),

    path('users/<int:user_id>/grant-access/', views.grant_investigator_access, name='admin_grant_investigator_access'),
    path('users/<int:user_id>/approve-role/', views.approve_role, name='admin_approve_role'),
    path(
    'users/<int:user_id>/verification/',
    views.view_verification,
    name='admin_view_verification'
),
path('users/<int:user_id>/reject-verification/', views.reject_verification, name='admin_reject_verification'),











]
