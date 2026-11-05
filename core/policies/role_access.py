from core.policies import PolicyResult
from officials.models import RoleVerification


class RoleAccessPolicy:
    @staticmethod
    def can_access(user):
        if user.role == 'CITIZEN':
            return PolicyResult(True)

        record = RoleVerification.objects.filter(user=user).first()

        if not record or not record.verified:
            return PolicyResult(False, "Verification pending")

        return PolicyResult(True)
