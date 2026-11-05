from .base import PolicyResult


class FIRWorkflowPolicy:
    """
    Controls FIR / Crime status transitions
    """

    VALID_TRANSITIONS = {
        'DRAFT': ['FILED'],
        'FILED': ['ASSIGNED'],
        'ASSIGNED': ['INVESTIGATING'],
        'INVESTIGATING': ['CHARGESHEET'],
        'CHARGESHEET': ['CLOSED'],
    }

    @staticmethod
    def can_change_status(user, crime, new_status):
        if user.is_blocked:
            return PolicyResult(False, "Blocked user")

        current = crime.status

        if new_status not in FIRWorkflowPolicy.VALID_TRANSITIONS.get(current, []):
            return PolicyResult(False, "Invalid status transition")

        if current == 'DRAFT' and user.role == 'CITIZEN':
            return PolicyResult(True)

        if current in ['FILED', 'ASSIGNED'] and user.role in ['ADMIN', 'INVESTIGATOR']:
            return PolicyResult(True)

        if current == 'INVESTIGATING' and user.role == 'INVESTIGATOR':
            return PolicyResult(True)

        if current == 'CHARGESHEET' and user.role == 'JUDGE':
            return PolicyResult(True)

        return PolicyResult(False, "Not authorized")
from .base import PolicyResult


class CrimePolicy:
    """
    Controls who can view/edit crime records
    """

    @staticmethod
    def can_view(user, crime):
        if user.is_blocked:
            return PolicyResult(False, "Blocked user")

        if user.role in ['OFFICER', 'INVESTIGATOR', 'ADMIN', 'JUDGE']:
            return PolicyResult(True)

        return PolicyResult(False, "Not authorized")

    @staticmethod
    def can_edit(user, crime):
        if user.is_blocked:
            return PolicyResult(False, "Blocked user")

        if user.role in ['INVESTIGATOR', 'ADMIN']:
            return PolicyResult(True)

        return PolicyResult(False, "Edit not allowed")
