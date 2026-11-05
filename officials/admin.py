# officials/admin.py - CORRECTED VERSION

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import InvestigatorAccess

@admin.register(InvestigatorAccess)
class InvestigatorAccessAdmin(admin.ModelAdmin):
    # FIX: actions should be list/tuple, not a method
    # Remove or comment out the custom 'actions' method and use a different name
    
    list_display = ['investigator', 'case_reference', 'access_period', 'status_badge', 'admin_actions']
    list_filter = ['active', 'investigator']
    search_fields = ['case_reference', 'investigator__username', 'purpose']
    raw_id_fields = ['investigator', 'created_by']
    date_hierarchy = 'access_start'
    
    # FIX: If you want custom admin actions, define them as a list
    # actions = ['deactivate_access', 'extend_access']
    
    fieldsets = (
        ('Case Details', {
            'fields': ('case_reference', 'purpose')
        }),
        ('Access Control', {
            'fields': ('investigator', 'access_start', 'access_end', 'active'),
            'description': 'Set time-limited access for specific case'
        }),
        ('Audit Trail', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def access_period(self, obj):
        return f"{obj.access_start.strftime('%Y-%m-%d %H:%M')} to {obj.access_end.strftime('%Y-%m-%d %H:%M')}"
    access_period.short_description = 'Access Period'
    
    def status_badge(self, obj):
        if not obj.active:
            return format_html('<span class="badge bg-secondary">INACTIVE</span>')
        
        if obj.is_expired():
            return format_html('<span class="badge bg-danger">EXPIRED</span>')
        else:
            remaining = obj.access_end - timezone.now()
            hours = remaining.total_seconds() / 3600
            if hours < 24:
                return format_html('<span class="badge bg-warning">{}h LEFT</span>', round(hours, 1))
            else:
                days = hours / 24
                return format_html('<span class="badge bg-success">{}d LEFT</span>', round(days, 1))
    status_badge.short_description = 'Status'
    
    # FIX: Rename this method to avoid conflict with Django's 'actions' attribute
    def admin_actions(self, obj):
        """Custom actions column (renamed from 'actions')"""
        if obj.active and not obj.is_expired():
            return format_html(
                '<a href="{}" class="button">View Details</a>',
                reverse('admin:officials_investigatoraccess_change', args=[obj.id])
            )
        return "-"
    admin_actions.short_description = 'Actions'




    
    def deactivate_selected(self, request, queryset):
        """Deactivate selected access records"""
        updated = queryset.update(active=False)
        self.message_user(request, f"{updated} access records deactivated.")
    
    def extend_access_selected(self, request, queryset):
        """Extend access by 7 days for selected records"""
        from django.utils import timezone
        from datetime import timedelta
        
        for obj in queryset:
            if not obj.is_expired():
                obj.access_end = obj.access_end + timedelta(days=7)
                obj.save()
        
        self.message_user(request, f"Access extended for {queryset.count()} records.")
    
    deactivate_selected.short_description = "Deactivate selected access"
    extend_access_selected.short_description = "Extend access by 7 days"      
    
    def save_model(self, request, obj, form, change):
        if not change:  # New access being created
            obj.created_by = request.user
            
            # Auto-set reasonable end time if not provided
            if not obj.access_end and obj.access_start:
                obj.access_end = obj.access_start + timedelta(days=7)  # Default 7 days
        
        # Create notification for investigator
        from notifications.models import Notification
        Notification.objects.create(
            user=obj.investigator,
            title=f"Case Access Granted: {obj.case_reference}",
            message=f"You have been granted access to case {obj.case_reference} until {obj.access_end.strftime('%Y-%m-%d %H:%M')}",
            notification_type='CASE_ACCESS'
        )
        
        super().save_model(request, obj, form, change)




 