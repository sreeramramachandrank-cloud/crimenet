# officials/forms.py - ADD this if needed
from django import forms
from .models import OfficerProfile

class OfficerRegistrationForm(forms.ModelForm):
    class Meta:
        model = OfficerProfile
        fields = ['rank', 'badge_id', 'department', 'reason_for_access']
        widgets = {
            'reason_for_access': forms.Textarea(attrs={'rows': 4}),
        }