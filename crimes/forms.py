# crimes/forms.py - MATCHING YOUR MODELS
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
import datetime
import json
from django import forms
from .models import FIR, PoliceStation, CrimeCategory, Witness, Evidence, InvestigationUpdate, CriminalRecord

User = get_user_model()

# ==================== FIR FORM ====================
class FIRForm(forms.ModelForm):
    """Main FIR creation form"""
    
    incident_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    incident_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control'
        })
    )
    
    class Meta:
        from .models import FIR  # Import inside to avoid circular imports
        
        model = FIR
        fields = [
            'police_station',
            'informant_name', 'informant_father_name', 'informant_age', 'informant_gender',
            'informant_occupation', 'informant_address', 'informant_district', 'informant_state',
            'informant_pincode', 'informant_mobile', 'informant_email',
            'informant_aadhaar', 'informant_voter_id',
            'relation_to_case',
            'incident_date', 'incident_time', 'incident_location', 'incident_landmark',
            'crime_category', 'other_ipc_sections', 'local_act',
            'incident_description', 'sequence_of_events',
            'delay_in_reporting', 'delay_reason',
            'accused_name', 'accused_father_name', 'accused_age', 'accused_gender',
            'accused_address', 'accused_occupation', 'accused_aadhaar', 'accused_mobile',
            'victim_name', 'victim_age', 'victim_gender', 'victim_address', 'victim_condition',
            'property_involved', 'property_description', 'property_value',
            'witness_count', 'witness_details',
            'evidence_available',
            'is_sensitive', 'is_cyber_crime', 'is_women_related', 'is_sc_st', 'is_child_victim'
        ]
        
        widgets = {
            'informant_name': forms.TextInput(attrs={'class': 'form-control'}),
            'informant_father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'informant_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '12'}),
            'informant_gender': forms.Select(attrs={'class': 'form-control'}),
            'informant_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'informant_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'informant_district': forms.TextInput(attrs={'class': 'form-control'}),
            'informant_state': forms.TextInput(attrs={'class': 'form-control'}),
            'informant_pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'informant_mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'informant_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'informant_aadhaar': forms.TextInput(attrs={'class': 'form-control'}),
            'informant_voter_id': forms.TextInput(attrs={'class': 'form-control'}),
            'relation_to_case': forms.Select(attrs={'class': 'form-control'}),
            'incident_location': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'incident_landmark': forms.TextInput(attrs={'class': 'form-control'}),
            'crime_category': forms.Select(attrs={'class': 'form-control'}),
            'other_ipc_sections': forms.TextInput(attrs={'class': 'form-control'}),
            'local_act': forms.TextInput(attrs={'class': 'form-control'}),
            'incident_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'sequence_of_events': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'delay_in_reporting': forms.Select(attrs={'class': 'form-control'}),
            'delay_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'accused_name': forms.TextInput(attrs={'class': 'form-control'}),
            'accused_father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'accused_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'accused_gender': forms.Select(attrs={'class': 'form-control'}),
            'accused_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'accused_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'accused_aadhaar': forms.TextInput(attrs={'class': 'form-control'}),
            'accused_mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'victim_name': forms.TextInput(attrs={'class': 'form-control'}),
            'victim_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'victim_gender': forms.Select(attrs={'class': 'form-control'}),
            'victim_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'victim_condition': forms.TextInput(attrs={'class': 'form-control'}),
            'property_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'property_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'witness_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'witness_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'evidence_available': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_sensitive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_cyber_crime': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_women_related': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_sc_st': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_child_victim': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract request from kwargs if present
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Customize form based on request
        if self.request:
            # Set initial values or filter querysets
            pass
    
    def clean_informant_mobile(self):
        mobile = self.cleaned_data.get('informant_mobile')
        if mobile and len(mobile) != 10:
            raise ValidationError('Enter valid 10-digit mobile number')
        return mobile
    
    def clean_informant_aadhaar(self):
        aadhaar = self.cleaned_data.get('informant_aadhaar')
        if aadhaar and len(aadhaar) != 12:
            raise ValidationError('Enter valid 12-digit Aadhaar number')
        return aadhaar

# ==================== BIOMETRIC CAPTURE FORM ====================
class BiometricCaptureForm(forms.ModelForm):
    """Form for capturing biometrics"""
    
    class Meta:
        from .models import FIR  # Import inside to avoid circular imports
        
        model = FIR
        fields = [
            'informant_photo',
            'thumb_impression',
            'digital_signature',
            'accused_photo',
        ]
        
        widgets = {
            'informant_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'thumb_impression': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'accused_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'digital_signature': forms.HiddenInput(),
        }

# ==================== WITNESS FORM ====================
class WitnessForm(forms.ModelForm):
    """Form for adding witnesses"""
    
    class Meta:
        from .models import Witness
        
        model = Witness
        fields = [
            'name', 'father_name', 'age', 'gender', 'occupation',
            'address', 'mobile', 'email', 'aadhaar_number',
            'statement', 'relation_to_case',
            'requires_protection', 'protection_details',
            'photo'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '120'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-control'}),
            'statement': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'relation_to_case': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'protection_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'requires_protection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if mobile and len(mobile) != 10:
            raise ValidationError('Enter valid 10-digit mobile number')
        return mobile
    
    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number')
        if aadhaar and len(aadhaar) != 12:
            raise ValidationError('Enter valid 12-digit Aadhaar number')
        return aadhaar

# ==================== EVIDENCE FORM ====================
class EvidenceForm(forms.ModelForm):
    """Form for adding evidence"""
    
    class Meta:
        from .models import Evidence
        
        model = Evidence
        fields = [
            'evidence_type', 'description', 'collected_date',
            'evidence_file', 'evidence_bag_number', 'sent_to_fsl'
        ]
        
        widgets = {
            'evidence_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'collected_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'evidence_file': forms.FileInput(attrs={'class': 'form-control'}),
            'evidence_bag_number': forms.TextInput(attrs={'class': 'form-control'}),
            'sent_to_fsl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# ==================== INVESTIGATION UPDATE FORM ====================
class InvestigationUpdateForm(forms.ModelForm):
    """Form for investigation updates"""
    
    class Meta:
        from .models import InvestigationUpdate
        
        model = InvestigationUpdate
        fields = ['update_type', 'description']
        
        widgets = {
            'update_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

# ==================== CRIMINAL RECORD FORM ====================
class CriminalRecordForm(forms.ModelForm):
    """Form for criminal records"""
    
    class Meta:
        from .models import CriminalRecord
        
        model = CriminalRecord
        fields = [
            'name', 'alias', 'father_name', 'aadhaar_number', 'gender',
            'permanent_address', 'distinguishing_marks', 'front_photo',
            'is_active', 'is_wanted'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'alias': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'permanent_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'distinguishing_marks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'front_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_wanted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number')
        if aadhaar and len(aadhaar) != 12:
            raise ValidationError('Enter valid 12-digit Aadhaar number')
        return aadhaar

# ==================== FIR SEARCH FORM ====================
class FIRSearchForm(forms.Form):
    """Form for searching FIRs"""
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by FIR number, name, mobile...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + FIR.STATUS_CHOICES if 'FIR' in locals() else [],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    police_station = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="All Stations"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import PoliceStation
        
        # Set police station queryset
        self.fields['police_station'].queryset = PoliceStation.objects.all()
        
        # Update status choices
        from .models import FIR
        self.fields['status'].choices = [('', 'All Statuses')] + list(FIR.STATUS_CHOICES)




# In crimes/forms.py, add this:

class FIRSearchForm(forms.Form):
    SEARCH_BY_CHOICES = [
        ('fir_number', 'FIR Number'),
        ('informant_name', 'Informant Name'),
        ('informant_mobile', 'Mobile Number'),
        ('accused_name', 'Accused Name'),
        ('crime_category', 'Crime Category'),
    ]
    
    search_by = forms.ChoiceField(
        choices=SEARCH_BY_CHOICES,
        initial='fir_number',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search term...'
        })
    )
    
    police_station = forms.ModelChoiceField(
        queryset=PoliceStation.objects.all(),
        required=False,
        empty_label="All Stations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(FIR.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )