from django.utils import timezone

class SLAService:

    @staticmethod
    def is_breached(complaint):
        if complaint.sla_deadline and timezone.now() > complaint.sla_deadline:
            return True
        return False
