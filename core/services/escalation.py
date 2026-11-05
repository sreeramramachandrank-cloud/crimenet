class EscalationService:

    @staticmethod
    def escalate(complaint):
        if complaint.sla_breached and not complaint.escalated:
            complaint.escalated = True
            complaint.save()
            return True
        return False
