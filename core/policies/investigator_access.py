from django.utils import timezone
from officials.models import InvestigatorAccess
from core.policies.base import PolicyResult

class InvestigatorAccessPolicy:

    @staticmethod
    def can_access(user):
        access = InvestigatorAccess.objects.filter(
            investigator=user,
            active=True
        ).first()

        if not access:
            return PolicyResult(False, "No active investigation access")

        if access.is_expired():
            access.active = False
            access.save()
            return PolicyResult(False, "Investigation access expired")

        return PolicyResult(True)
