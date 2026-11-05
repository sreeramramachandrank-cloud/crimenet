from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView

from officials.models import OfficerProfile, RoleVerification

from .forms import LoginForm, RegisterForm
from audit.services import get_blocking_admin
from core.policies.investigator_access import InvestigatorAccessPolicy
from core.enforce import enforce


# ============================================================
# LOGIN (ROLE-BASED REDIRECT – SAFE)
# ============================================================

class RoleBasedLoginView(LoginView):
    """
    Redirect users AFTER successful login.
    Home page (/) is never hijacked.
    """

    def get_success_url(self):
        user = self.request.user

        if getattr(user, 'role', None) == 'INVESTIGATOR':
            return reverse_lazy('officials:investigator_portal')

        if getattr(user, 'role', None) == 'OFFICER':
            return reverse_lazy('officials:officer_dashboard')

        return reverse_lazy('home')


def login_view(request):
    form = LoginForm(data=request.POST or None)

    if form.is_valid():
        user = form.get_user()
        login(request, user)

        if user.is_superuser:
            return redirect('/admin-panel/')

        return redirect('dashboard')

    return render(request, 'accounts/login.html', {'form': form})


# ============================================================
# REGISTRATION (FIXED – NO DUPLICATE CREATION)
# ============================================================
# def register_view(request):
#     form = RegisterForm(request.POST or None, request.FILES or None)

#     if form.is_valid():
#         try:
#             user = form.save()  # IMPORTANT: do NOT use commit=False
#             requested_role = user.requested_role

#             # 👤 Citizen
#             if not requested_role:
#                 messages.success(
#                     request,
#                     "Registration successful. You can now log in as a Citizen."
#                 )
#                 return redirect('login')

#             # 👮 Officer
#             if requested_role == 'OFFICER':
#                 OfficerProfile.objects.create(
#                     user=user,
#                     rank=form.cleaned_data['rank'],
#                     badge_id=form.cleaned_data['badge_id'],
#                     department=form.cleaned_data['department'],
#                     reason_for_access=form.cleaned_data['reason_for_access']
#                 )

#             # 🔐 Verified roles
#             elif requested_role in ['INVESTIGATOR', 'FORENSIC', 'JUDGE', 'AUDITOR']:
#                 RoleVerification.objects.create(
#                     user=user,
#                     role=requested_role,
#                     rank=form.cleaned_data.get('rank'),
#                     # jurisdiction=form.cleaned_data.get('jurisdiction'),
#                     appointment_order=form.cleaned_data.get('appointment_order'),
#                     reason_for_access=form.cleaned_data.get('reason_for_access')
#                 )

#             messages.success(
#                 request,
#                 "Registration submitted successfully. "
#                 "Your account will be activated after administrator verification."
#             )
#             return redirect('login')

#         except Exception as e:
#             messages.error(
#                 request,
#                 f"Registration failed due to a system error: {str(e)}"
#             )

#     else:
#         messages.error(
#             request,
#             "Registration failed. Please correct the highlighted errors."
#         )

#     return render(request, 'accounts/register.html', {'form': form})

def register_view(request):
    form = RegisterForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        user = form.save()
        messages.success(
            request,
            "Registration submitted successfully. Await administrator verification."
        )
        return redirect('login')
    

    messages.error(request, "Please correct the highlighted errors.")
    return render(request, 'accounts/register.html', {'form': form})

# ============================================================
# DASHBOARD (ROLE + SECURITY ENFORCEMENT)
# ============================================================

@login_required
def dashboard(request):
    user = request.user

    # 🚫 Blocked user
    if getattr(user, 'is_blocked', False):
        return redirect('account_blocked')

    # 🕒 Officer not approved
    if user.role == 'OFFICER':
        if hasattr(user, 'officer_profile') and not user.officer_profile.verified:
            return render(request, 'accounts/pending_approval.html')

    # 🕵️ Investigator logic (VALIDATE but DO NOT FORCE REDIRECT)
    if user.role == 'INVESTIGATOR':
        if not hasattr(user, 'role_verification') or not user.role_verification.verified:
            return render(request, 'accounts/pending_approval.html', {
                'message': 'Your investigator credentials are pending admin verification.'
            })

        from officials.models import InvestigatorAccess
        from django.utils import timezone

        all_access = InvestigatorAccess.objects.filter(
            investigator=user
        ).order_by('-access_start')

        active_access = all_access.filter(
            active=True,
            access_end__gt=timezone.now()
        ).first()

        expired_access = all_access.filter(
            active=True,
            access_end__lte=timezone.now()
        ).exists()

        if active_access:
            result = InvestigatorAccessPolicy.can_access(user)
            denied = enforce(result)

            if denied:
                logout(request)
                return render(request, 'accounts/access_expired.html', {
    'role': user.role
})


            messages.info(
                request,
                "You have active investigation access. "
                "Use the dashboard to open your assigned case."
            )

        elif expired_access:
            messages.warning(
                request,
                "Your previous investigation access has expired. "
                "Please request new case access from administrator."
            )
        else:
            messages.info(
                request,
                "Welcome to Investigator Dashboard. "
                "No case access has been assigned yet."
            )

    # 🔔 Notifications
    notifications = user.notifications.filter(is_read=False)
    notifications.update(is_read=True)

    context = {
        'role': user.role,
        'requested_role': user.requested_role,
        'notifications': notifications,
    }

    # ========== OFFICER CRIME DATA ==========
    if user.role == 'OFFICER':
        try:
            from crimes.models import FIR
            from django.db.models import Q
            from django.utils import timezone
            from datetime import timedelta

            registered_firs = FIR.objects.filter(officer_in_charge=user).count()
            investigating_firs = FIR.objects.filter(investigating_officer=user).count()

            recent_firs = FIR.objects.filter(
                Q(officer_in_charge=user) | Q(investigating_officer=user)
            ).order_by('-date_registered')[:5]

            today = timezone.now().date()
            week_ago = today - timedelta(days=7)

            weekly_firs = FIR.objects.filter(
                officer_in_charge=user,
                date_registered__date__gte=week_ago
            ).count()

            pending_verification = FIR.objects.filter(
                officer_in_charge=user,
                biometric_status='NOT_CAPTURED'
            ).count()

            context.update({
                'registered_firs': registered_firs,
                'investigating_firs': investigating_firs,
                'weekly_firs': weekly_firs,
                'pending_verification': pending_verification,
                'recent_firs': recent_firs,
                'has_crime_access': True,
            })

        except Exception as e:
            print(f"Error loading crime data: {e}")
            context.update({
                'registered_firs': 0,
                'investigating_firs': 0,
                'weekly_firs': 0,
                'pending_verification': 0,
                'recent_firs': [],
                'has_crime_access': False,
            })
    else:
        context.update({'has_crime_access': False})

    return render(request, 'accounts/dashboard.html', context)


# ============================================================
# BLOCKED ACCOUNT
# ============================================================

@login_required
def account_blocked(request):
    block_log = get_blocking_admin(request.user)

    return render(request, 'accounts/blocked.html', {
        'block_reason': block_log.reason if block_log else None,
        'blocked_by': block_log.actor if block_log else None,
    })


# ============================================================
# LOGOUT
# ============================================================

from django.http import HttpResponseRedirect
from django.urls import reverse

def logout_view(request):
    logout(request)
    request.session.flush()
    return HttpResponseRedirect(reverse('home'))
