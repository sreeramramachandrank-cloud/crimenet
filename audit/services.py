# audit/services.py
from audit.models import AuditLog

def get_blocking_admin(user):
    return AuditLog.objects.filter(
        target_user=user,
        action='USER_BLOCKED'
    ).order_by('-timestamp').first()
