from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from officials.models import InvestigatorAccess

@receiver(post_save, sender=InvestigatorAccess)
def deactivate_expired_access(sender, instance, **kwargs):
    if instance.is_expired():
        instance.active = False
        instance.save(update_fields=['active'])
