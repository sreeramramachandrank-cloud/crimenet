from django.db import models
from accounts.models import User

class Appeal(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Appeal by {self.user.username} ({self.status})"




class AdminContactRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_requests')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_contacts')
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('OPEN', 'Open'),
            ('RESPONDED', 'Responded'),
            ('CLOSED', 'Closed')
        ],
        default='OPEN'
    )
    created_at = models.DateTimeField(auto_now_add=True)
