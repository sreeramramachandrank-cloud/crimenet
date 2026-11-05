from django import forms
from officials.models import InvestigatorAccess

class InvestigatorAccessForm(forms.ModelForm):
    class Meta:
        model = InvestigatorAccess
        fields = [
            'case_reference',
            'purpose',
            'access_end'
        ]

        widgets = {
            'access_end': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            )
        }
