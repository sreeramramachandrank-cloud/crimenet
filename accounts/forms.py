from django import forms
from .models import User
from officials.models import OfficerProfile, RoleVerification


from django import forms
from .models import User
from officials.models import OfficerProfile, RoleVerification


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    # Officer
    rank = forms.ChoiceField(
        choices=OfficerProfile.RANK_CHOICES,
        required=False
    )
    badge_id = forms.CharField(required=False)
    department = forms.CharField(required=False)

    # Shared
    appointment_order = forms.FileField(required=False)
    reason_for_access = forms.CharField(widget=forms.Textarea, required=False)

    # Forensic
    lab_affiliation = forms.CharField(required=False)
    forensic_license = forms.FileField(required=False)

    # Judge
    judicial_id = forms.CharField(required=False)
    court_name = forms.CharField(required=False)

    # Auditor
    authority_letter = forms.FileField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'requested_role']

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        role = cleaned_data.get('requested_role')

        if password != confirm:
            self.add_error('confirm_password', 'Passwords do not match')

        # Officer
        if role == 'OFFICER':
            required = ['rank', 'badge_id', 'department', 'reason_for_access']

        # Investigator
        elif role == 'INVESTIGATOR':
            required = ['rank', 'appointment_order', ]

        # Forensic
        elif role == 'FORENSIC':
            required = ['lab_affiliation', 'forensic_license', 'reason_for_access']

        # Judge
        elif role == 'JUDGE':
            required = ['judicial_id', 'court_name']

        # Auditor
        elif role == 'AUDITOR':
            required = ['authority_letter']

        else:
            required = []

        for field in required:
            if not cleaned_data.get(field):
                self.add_error(field, 'This field is required for this role')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])

        selected_role = self.cleaned_data.get('requested_role')

        user.role = 'CITIZEN'
        user.requested_role = selected_role if selected_role != 'CITIZEN' else None

        if commit:
          user.save()

        # 👮 OFFICER
        if selected_role == 'OFFICER':
            OfficerProfile.objects.create(
                user=user,
                rank=self.cleaned_data['rank'],
                badge_id=self.cleaned_data['badge_id'],
                department=self.cleaned_data['department'],
                reason_for_access=self.cleaned_data['reason_for_access']
            )

        # 🔐 ALL VERIFIED ROLES (ONE MODEL)
        elif selected_role in ['INVESTIGATOR', 'FORENSIC', 'JUDGE', 'AUDITOR']:
            RoleVerification.objects.create(
                user=user,
                role=selected_role,
                rank=self.cleaned_data.get('rank'),
                jurisdiction=self.cleaned_data.get('jurisdiction'),
                appointment_order=self.cleaned_data.get('appointment_order'),
                reason_for_access = forms.CharField(
    widget=forms.Textarea,
    required=False
)

            )

        return user



class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):
                raise forms.ValidationError("Invalid username or password")
            self.user = user
        except User.DoesNotExist:
            raise forms.ValidationError("Invalid username or password")

    def get_user(self):
        return self.user    