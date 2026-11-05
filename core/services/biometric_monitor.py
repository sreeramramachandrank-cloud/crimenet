from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from audit.models import AuditLog

class BiometricMisuseDetector:

    @staticmethod
    def is_excessive(user):
        window_start = timezone.now() - timedelta(
            minutes=settings.BIOMETRIC_TIME_WINDOW_MIN
        )

        count = AuditLog.objects.filter(
            actor=user,
            action='BIOMETRIC_ACCESS',
            timestamp__gte=window_start
        ).count()

        return count >= settings.BIOMETRIC_SEARCH_LIMIT
