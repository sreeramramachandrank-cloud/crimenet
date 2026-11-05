# crimes/models_minimal.py - Create this new file
from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid

class CrimeCategory(models.Model):
    name = models.CharField(max_length=200)
    ipc_section = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.ipc_section} - {self.name}"

class PoliceStation(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name

class FIR(models.Model):
    # Basic Info
    fir_number = models.CharField(max_length=50, unique=True, editable=False)
    police_station = models.ForeignKey(PoliceStation, on_delete=models.PROTECT)
    
    # Informant
    informant_name = models.CharField(max_length=200)
    informant_mobile = models.CharField(max_length=10, validators=[
        RegexValidator(regex=r'^[6-9]\d{9}$', message='Valid Indian mobile')
    ])
    informant_aadhaar = models.CharField(max_length=12, blank=True, validators=[
        RegexValidator(regex=r'^\d{12}$', message='12-digit Aadhaar')
    ])
    
    # Incident
    incident_date = models.DateField()
    incident_location = models.TextField()
    crime_category = models.ForeignKey(CrimeCategory, on_delete=models.PROTECT)
    incident_description = models.TextField()
    
    # Officer
    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='firs'
    )
    
    # Biometric
    informant_photo = models.ImageField(upload_to='fir_photos/', blank=True, null=True)
    
    # Status
    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('INVESTIGATION', 'Under Investigation'),
        ('CLOSED', 'Closed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTERED')
    
    # System
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.fir_number:
            year = timezone.now().year
            count = FIR.objects.filter(created_at__year=year).count() + 1
            self.fir_number = f"FIR/{year}/{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.fir_number

# crimes/forms_minimal.py
from django import forms
from .models_minimal import FIR, CrimeCategory, PoliceStation

class SimpleFIRForm(forms.ModelForm):
    class Meta:
        model = FIR
        fields = ['police_station', 'informant_name', 'informant_mobile', 
                 'incident_date', 'incident_location', 'crime_category', 
                 'incident_description']
        
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'incident_location': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'incident_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }