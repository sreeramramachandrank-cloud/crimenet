from audit.models import AuditLog
from django.utils.timezone import now, timedelta

class MisuseDetector:

    @staticmethod
    def excessive_rejections(user):
        last_24h = now() - timedelta(hours=24)

        count = AuditLog.objects.filter(
            actor=user,
            action='COMPLAINT_STATUS_CHANGE',
            reason__icontains='REJECTED',
            timestamp__gte=last_24h
        ).count()

        return count >= 10
