from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):

    ROLE_CHOICES = (
        ('CITIZEN', 'Citizen'),
        ('OFFICER', 'Police Officer'),
        ('INVESTIGATOR', 'Investigating Officer'),
        ('JUDGE', 'Judge'),
        ('FORENSIC', 'Forensic Analyst'),
        ('AUDITOR', 'Judicial Auditor'),
        ('ADMIN', 'System Administrator'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='CITIZEN',
        blank=False,
        null=False
    )

    requested_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        blank=True,
        null=True
    )

    region = models.CharField(max_length=100, blank=True)
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True, null=True)



    def get_investigator_access_display(self):
        """Display investigator access status for admin/user display"""
        if self.role != 'INVESTIGATOR':
            return "—"
        
        from officials.models import InvestigatorAccess
        from django.utils import timezone
        
        # Check for active access
        active = InvestigatorAccess.objects.filter(
            investigator=self,
            active=True,
            access_end__gt=timezone.now()
        ).exists()
        
        if active:
            return "● ACTIVE"
        
        # Check for expired access
        expired = InvestigatorAccess.objects.filter(
            investigator=self,
            active=True,
            access_end__lte=timezone.now()
        ).exists()
        
        if expired:
            return "● EXPIRED"
        
        # Check for any inactive access
        any_access = InvestigatorAccess.objects.filter(investigator=self).exists()
        
        if any_access:
            return "● INACTIVE"
        
        return "● NO ACCESS"
    
    # You can also make it a property for easier access
    @property
    def investigator_access_status(self):
        """Property version of the access display"""
        return self.get_investigator_access_display()
def clean(self):
    if self.requested_role == 'ADMIN':
        raise ValueError("System Admin role cannot be requested.")

