from django.db import models
from accounts.models import User

class BiometricRecord(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='biometric_record',
        null=True,        # ✅ ADD THIS
        blank=True        # ✅ ADD THIS
    )

    fingerprint_hash = models.CharField(max_length=255)
    face_hash = models.CharField(
    max_length=255,
    null=True,        # ✅ ADD
    blank=True        # ✅ ADD
)

    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    match_count = models.IntegerField(default=0)
    false_positive_count = models.IntegerField(default=0)


    def __str__(self):
        return f"Biometrics for {self.user.username if self.user else 'Unassigned'}"



from django.db import models
from accounts.models import User

class Warrant(models.Model):
    judge = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='issued_warrants'
    )

    issued_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='biometric_warrants'
    )

    valid_until = models.DateTimeField()
    reason = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    match_count = models.IntegerField(default=0)
    false_positive_count = models.IntegerField(default=0)


    def is_valid(self):
        from django.utils import timezone
        return timezone.now() <= self.valid_until




class BiometricNote(models.Model):
    biometric = models.ForeignKey(
        BiometricRecord,
        on_delete=models.CASCADE,
        related_name='notes'
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
