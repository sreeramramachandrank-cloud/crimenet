from django.db import models
from accounts.models import User

class AuditLog(models.Model):
    ACTION_CHOICES = [
    ('BLOCK', 'Block User'),
    ('UNBLOCK', 'Unblock User'),
    ('ROLE_APPROVE', 'Approve Role'),
    ('ROLE_REJECT', 'Reject Role'),
    ('LOGIN', 'User Login'),
    ('LOGOUT', 'User Logout'),
    ('CASE_ACCESS', 'Grant Case Access'),
    ('BIOMETRIC', 'Biometric Access'),
    # Add more as needed
]

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_done'
    )

    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_received'
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} → {self.target_user}"
