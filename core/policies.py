class PolicyResult:
    def __init__(self, allowed: bool, reason: str = ""):
        self.allowed = allowed
        self.reason = reason


class CrimePolicy:

    @staticmethod
    def can_view_crime(user, crime):
        # Blocked users can never view
        if user.is_blocked:
            return PolicyResult(False, "User is blocked")

        # Admin & Investigator can view all
        if user.role in ['ADMIN', 'INVESTIGATOR']:
            return PolicyResult(True)

        # Officer can view only assigned crime
        if user.role == 'OFFICER' and crime.assigned_officer == user:
            return PolicyResult(True)

        return PolicyResult(False, "Not authorized to view this FIR")






class FIRWorkflowPolicy:

    VALID_TRANSITIONS = {
        'DRAFT': ['FILED'],
        'FILED': ['ASSIGNED'],
        'ASSIGNED': ['INVESTIGATING'],
        'INVESTIGATING': ['CHARGESHEET'],
        'CHARGESHEET': ['CLOSED'],
    }

    @staticmethod
    def can_change_status(user, crime, new_status):
        # Blocked users can never act
        if user.is_blocked:
            return PolicyResult(False, "Blocked user")

        current = crime.status

        # Invalid transition
        if new_status not in FIRWorkflowPolicy.VALID_TRANSITIONS.get(current, []):
            return PolicyResult(False, "Invalid status transition")

        # Role-based control
        if current == 'DRAFT' and user.role == 'CITIZEN':
            return PolicyResult(True)

        if current in ['FILED', 'ASSIGNED'] and user.role in ['ADMIN', 'INVESTIGATOR']:
            return PolicyResult(True)

        if current == 'INVESTIGATING' and user.role == 'INVESTIGATOR':
            return PolicyResult(True)

        if current == 'CHARGESHEET' and user.role == 'JUDGE':
            return PolicyResult(True)

        return PolicyResult(False, "You are not authorized for this action")




from core.policies import PolicyResult


class ComplaintPolicy:

    VALID_TRANSITIONS = {
        'PENDING': ['IN_PROGRESS', 'ACCEPTED', 'REJECTED'],
        'IN_PROGRESS': ['ACCEPTED', 'REJECTED'],
        'ACCEPTED': ['CLOSED'],
        'REJECTED': [],
        'CLOSED': [],
    }

    @staticmethod
    def can_change_status(user, complaint, new_status):
        # Blocked users can never act
        if user.is_blocked:
            return PolicyResult(False, "Blocked user")

        # Invalid transition
        if new_status not in ComplaintPolicy.VALID_TRANSITIONS.get(
            complaint.status, []
        ):
            return PolicyResult(False, "Invalid complaint status transition")

        # Citizen rules
        if user.role == 'CITIZEN':
            return PolicyResult(False, "Citizens cannot change complaint status")

        # Officer rules
        if user.role == 'OFFICER':
            if complaint.status in ['PENDING', 'IN_PROGRESS']:
                return PolicyResult(True)

        # Investigator & Admin rules
        if user.role in ['INVESTIGATOR', 'ADMIN']:
            return PolicyResult(True)

        return PolicyResult(False, "Not authorized to perform this action")
