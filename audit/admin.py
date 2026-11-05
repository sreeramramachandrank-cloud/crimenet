from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'actor',
        'action',
        'target_user',
        'reason',
    )

    list_filter = (
        'action',
        'timestamp',
    )

    search_fields = (
        'actor__username',
        'target_user__username',
        'reason',
    )

    ordering = ('-timestamp',)
