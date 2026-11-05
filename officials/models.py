from django.db import models
from accounts.models import User

class OfficerProfile(models.Model):

    RANK_CHOICES = [
        ('CONSTABLE', 'Constable'),
        ('SI', 'Sub-Inspector'),
        ('INSPECTOR', 'Inspector'),
        ('DSP', 'DSP'),
        ('SP', 'SP'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='officer_profile'
    )

    rank = models.CharField(max_length=20, choices=RANK_CHOICES)
    badge_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    reason_for_access = models.TextField()

    verified = models.BooleanField(default=False)  # ADMIN approval
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.rank})"



from django.db import models
from accounts.models import User

class OfficerDocument(models.Model):
    DOCUMENT_TYPES = (
        ('ID', 'Government ID'),
        ('ORDER', 'Appointment Order'),
        ('BADGE', 'Badge Proof'),
    )

    officer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='officer_documents'
    )

    doc_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='officer_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    verified = models.BooleanField(default=False)
    admin_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.officer.username} - {self.doc_type}"




class RoleVerification(models.Model):
    ROLE_CHOICES = [
        ('INVESTIGATOR', 'Investigating Officer'),
        ('FORENSIC', 'Forensic Analyst'),
        ('JUDGE', 'Judge'),
        ('AUDITOR', 'Judicial Auditor'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='role_verification'
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # 🔐 Authority proof (real-world)
    rank = models.CharField(max_length=100)
    jurisdiction = models.CharField(
        max_length=255,
        null=True,      # ✅ CHANGE
        blank=True      # ✅ CHANGE
    )

    
    appointment_order = models.FileField(upload_to='appointments/')

    reason_for_access = models.TextField(null=True, blank=True)

    # ✅ Admin verification
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_roles'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.role}"





from django.db import models
from django.utils import timezone
from accounts.models import User

class InvestigatorAccess(models.Model):
    investigator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='investigation_accesses'
    )

    case_reference = models.CharField(max_length=200)
    purpose = models.TextField()

    access_start = models.DateTimeField(default=timezone.now)
    access_end = models.DateTimeField()

    active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_investigator_access'
    )
    def time_remaining(self):
        """Calculate remaining time in human-readable format"""
        from django.utils import timezone
        if not self.active:
            return "Inactive"
        
        if self.is_expired():
            return "Expired"
        
        remaining = self.access_end - timezone.now()
        total_seconds = remaining.total_seconds()
        
        if total_seconds < 3600:  # Less than 1 hour
            minutes = int(total_seconds / 60)
            return f"{minutes}m"
        elif total_seconds < 86400:  # Less than 1 day
            hours = int(total_seconds / 3600)
            return f"{hours}h"
        else:
            days = int(total_seconds / 86400)
            return f"{days}d"

    def is_expired(self):
        return timezone.now() > self.access_end

    def __str__(self):
        return f"{self.investigator.username} → {self.case_reference}"
from django.db import models
from accounts.models import User

class OfficerProfile(models.Model):

    RANK_CHOICES = [
        ('CONSTABLE', 'Constable'),
        ('SI', 'Sub-Inspector'),
        ('INSPECTOR', 'Inspector'),
        ('DSP', 'DSP'),
        ('SP', 'SP'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='officer_profile'
    )

    rank = models.CharField(max_length=20, choices=RANK_CHOICES)
    badge_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    reason_for_access = models.TextField()

    verified = models.BooleanField(default=False)  # ADMIN approval
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.rank})"
