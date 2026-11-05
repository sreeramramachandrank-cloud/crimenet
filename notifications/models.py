from django.db import models
from django.conf import settings

from accounts.models import User

# notifications/models.py - Add fields
# notifications/models.py - Add related_name
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('ROLE_APPROVAL', 'Role Approval'),
        ('BLOCK', 'Account Blocked'),
        ('UNBLOCK', 'Account Unblocked'),
        ('CASE_ACCESS', 'Case Access Granted'),
        ('SYSTEM', 'System Alert'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='notifications'  # ADD THIS LINE
    )
    title = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50, 
        choices=NOTIFICATION_TYPES, 
        default='SYSTEM'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"