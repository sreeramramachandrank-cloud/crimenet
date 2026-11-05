# accounts/admin.py or adminpanel/admin.py

from django.contrib import admin
from django.utils.html import format_html
from accounts.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'investigator_access_column', 'is_superuser', 'is_blocked']
    
    def investigator_access_column(self, obj):
        """Custom column for investigator access status"""
        status = obj.get_investigator_access_display()
        
        # Color code the status
        if status == "● ACTIVE":
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', status)
        elif status == "● EXPIRED":
            return format_html('<span style="color: orange; font-weight: bold;">{}</span>', status)
        elif status == "● INACTIVE":
            return format_html('<span style="color: gray;">{}</span>', status)
        elif status == "● NO ACCESS":
            return format_html('<span style="color: #666;">{}</span>', status)
        else:
            return status
    
    investigator_access_column.short_description = 'Investigator Access'