def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# audit/utils.py - Create this file
from urllib import request

from accounts.models import User
from .models import AuditLog

def log_action(actor, target_user, action, reason=''):
    """Helper to create audit logs with proper field names"""
    return AuditLog.objects.create(
        actor=actor,
        target_user=target_user,
        action=action,
        reason=reason
    )
