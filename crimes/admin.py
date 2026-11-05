# crimes/admin.py - Corrected version

from django.contrib import admin
from .models import (
    CrimeCategory, PoliceStation, FIR, CriminalRecord,
    Witness, Evidence, InvestigationUpdate, FIRAuditLog
)

@admin.register(CrimeCategory)
class CrimeCategoryAdmin(admin.ModelAdmin):
    list_display = ('section', 'description', 'is_cognizable', 'is_bailable')
    search_fields = ('section', 'description')
    list_filter = ('is_cognizable', 'is_bailable')

@admin.register(PoliceStation)
class PoliceStationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'district', 'state', 'incharge_name')
    search_fields = ('code', 'name', 'district', 'incharge_name')
    list_filter = ('district', 'state')

@admin.register(FIR)
class FIRAdmin(admin.ModelAdmin):
    list_display = ('fir_number', 'informant_name', 'crime_category', 'status', 'date_registered')
    search_fields = ('fir_number', 'informant_name', 'informant_mobile', 'informant_aadhaar')
    list_filter = ('status', 'police_station', 'crime_category', 'priority')
    readonly_fields = ('fir_number', 'uuid', 'photo_hash', 'thumb_hash', 'created_at', 'updated_at')
    filter_horizontal = ()
    date_hierarchy = 'date_registered'

@admin.register(CriminalRecord)
class CriminalRecordAdmin(admin.ModelAdmin):
    list_display = ('criminal_id', 'name', 'alias', 'is_active', 'is_wanted')
    search_fields = ('criminal_id', 'name', 'alias', 'aadhaar_number')
    list_filter = ('is_active', 'is_wanted')  # REMOVED 'gender' from here
    readonly_fields = ('criminal_id', 'created_at', 'updated_at')

@admin.register(Witness)
class WitnessAdmin(admin.ModelAdmin):
    list_display = ('name', 'fir', 'age', 'statement_recorded_by')
    search_fields = ('name', 'fir__fir_number')
    list_filter = ('statement_recorded_by',)
    raw_id_fields = ('fir',)

@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('evidence_type', 'fir', 'collected_by', 'collected_date')
    search_fields = ('evidence_type', 'fir__fir_number')
    list_filter = ('evidence_type', 'sent_to_fsl')
    date_hierarchy = 'collected_date'

@admin.register(InvestigationUpdate)
class InvestigationUpdateAdmin(admin.ModelAdmin):
    list_display = ('update_type', 'fir', 'updated_by', 'update_date')
    search_fields = ('update_type', 'fir__fir_number')
    list_filter = ('update_type',)
    date_hierarchy = 'update_date'

@admin.register(FIRAuditLog)
class FIRAuditLogAdmin(admin.ModelAdmin):
    list_display = ('fir', 'action', 'user', 'timestamp')
    search_fields = ('fir__fir_number', 'action', 'user__username')
    list_filter = ('action', 'timestamp')
    readonly_fields = ('fir', 'action', 'description', 'user', 'timestamp')  # REMOVED ip_address and user_agent
    date_hierarchy = 'timestamp'


from .models import AIMatch

@admin.register(AIMatch)
class AIMatchAdmin(admin.ModelAdmin):
    list_display = ("biometric_type", "confidence", "reviewed", "created_at")
    list_filter = ("biometric_type", "reviewed")


from .models import JudicialAuditLog

@admin.register(JudicialAuditLog)
class JudicialAuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "reference", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("user__username", "reference", "action")
