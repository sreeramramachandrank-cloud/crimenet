from django import forms
from .models import BiometricRecord

class BiometricEnrollForm(forms.ModelForm):
    class Meta:
        model = BiometricRecord
        fields = ['fingerprint_hash', 'face_hash', 'confidence']
