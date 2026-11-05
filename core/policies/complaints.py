from .base import PolicyResult


class ComplaintPolicy:
    @staticmethod
    def can_change_status(user, complaint, new_status):
        if user.is_blocked:
            return PolicyResult(False, "Blocked user")

        if user.role == 'CITIZEN':
            return PolicyResult(False, "Citizens cannot change status")

        if user.role in ['OFFICER', 'INVESTIGATOR']:
            return PolicyResult(True)

        if user.role == 'ADMIN':
            return PolicyResult(True)

        return PolicyResult(False, "Not authorized")
