from .base import PolicyResult

class BiometricPolicy:





    @staticmethod
    def can_enroll(user):
        if user.is_blocked:
            return PolicyResult(False, "User is blocked")

        if user.role not in ['FORENSIC', 'INVESTIGATOR']:
            return PolicyResult(False, "Only forensic or investigator can enroll biometrics")

        return PolicyResult(True)

    @staticmethod
    def can_access(user, warrant=False):
        if user.is_blocked:
            return PolicyResult(False, "User is blocked")

        if not warrant:
            return PolicyResult(False, "Judicial warrant required")
        

        if warrant.issued_to != user:
            return PolicyResult(False, "Warrant not issued to this user")

        if user.role not in ['FORENSIC', 'INVESTIGATOR']:
            return PolicyResult(False, "Insufficient clearance")

        return PolicyResult(True)
