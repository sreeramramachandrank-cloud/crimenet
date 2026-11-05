from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone

from complaints.models import Complaint
from crimes.models import FIR
from officials.forms import OfficerRegistrationForm
from .models import OfficerProfile, RoleVerification, InvestigatorAccess

@login_required
def officer_details(request):
    form = OfficerRegistrationForm(request.POST or None)

    if form.is_valid():
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        return redirect('dashboard')

    return render(request, 'officials/officer_details.html', {
        'form': form
    })



    


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.decorators import role_required
from .models import OfficerDocument, RoleVerification, RoleVerification

@login_required
@role_required(['OFFICER'])
def upload_documents(request):
    if request.method == 'POST':
        OfficerDocument.objects.create(
            officer=request.user,
            doc_type=request.POST['doc_type'],
            file=request.FILES['file']
        )
        return redirect('upload_documents')

    documents = OfficerDocument.objects.filter(officer=request.user)
    return render(request, 'officials/upload_documents.html', {
        'documents': documents
    })




from django.utils import timezone
from datetime import timedelta
from officials.models import InvestigatorAccess
    

@login_required

def approve_investigator(request, verification_id):
    record = get_object_or_404(RoleVerification, id=verification_id)

    if request.method == 'POST':
        duration_days = int(request.POST['duration_days'])

        InvestigatorAccess.objects.create(
            investigator=record.user,
            case_reference=request.POST['case_reference'],
            purpose=record.reason_for_access,
            access_end=timezone.now() + timedelta(days=duration_days),
            created_by=request.user
        )

        record.verified = True
        record.verified_by = request.user
        record.verified_at = timezone.now()
        record.save()

        user = record.user
        user.role = 'INVESTIGATOR'
        user.requested_role = None
        user.save()

        return redirect('admin_role_requests')

    return render(request, 'adminpanel/approve_investigator.html', {
        'record': record
    })



from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages
from .models import InvestigatorAccess

def is_investigator(user):
    """Check if user is investigator"""
    return user.role == 'INVESTIGATOR'


@login_required
def investigator_active_dashboard(request):
    active_accesses = InvestigatorAccess.objects.filter(
        investigator=request.user,
        active=True,
        access_end__gt=timezone.now()
    )

    if not active_accesses.exists():
        messages.warning(request, "No active investigation access found.")
        return redirect('investigator_dashboard')

    # Calculate remaining time
    for access in active_accesses:
        remaining = access.access_end - timezone.now()
        access.remaining_hours = round(remaining.total_seconds() / 3600, 2)

    context = get_base_dashboard_context(request)
    context.update({
        "active_accesses": active_accesses,
        "has_active_access": True,
    })

    return render(
        request,
        "officials/investigator/investigator_active_dashboard.html",
        context
    )


@login_required
@user_passes_test(is_investigator)
def investigator_dashboard(request):
    active_access = InvestigatorAccess.objects.filter(
        investigator=request.user,
        active=True,
        access_end__gt=timezone.now()
    ).exists()

    if active_access:
        return redirect('investigator_active_dashboard')

    context = get_base_dashboard_context(request)
    context.update({
        "has_active_access": False,
    })

    return render(
        request,
        "officials/investigator_dashboard.html",
        context
    )





# officials/views.py - ADD these views

# officials/views.py - ADD these functions at the bottom

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages

def is_verified_investigator(user):
    """Check if user is a verified investigator"""
    if not hasattr(user, 'role') or user.role != 'INVESTIGATOR':
        return False
    
    # Must have verified RoleVerification
    if not hasattr(user, 'role_verification') or not user.role_verification.verified:
        return False
    
    return True

# officials/views.py - Update investigator_portal function

@login_required
@user_passes_test(is_verified_investigator)
def investigator_portal(request):
    """Main portal for verified investigators"""
    from django.utils import timezone
    
    # Get all access records
    all_accesses = InvestigatorAccess.objects.filter(
        investigator=request.user
    ).order_by('-access_start')
    
    # Categorize accesses
    active_accesses = []
    expired_accesses = []
    inactive_accesses = []
    
    for access in all_accesses:
        if access.active and access.access_end > timezone.now():
            active_accesses.append(access)
        elif access.active and access.access_end <= timezone.now():
            expired_accesses.append(access)
        else:
            inactive_accesses.append(access)
    
    # Determine status message
    if active_accesses:
        status = "active"
        status_message = "You have active case access."
    elif expired_accesses:
        status = "expired"
        status_message = "Your previous case access has expired."
    else:
        status = "none"
        status_message = "No case access has been assigned yet."
    
    context = {
        'user': request.user,
        'all_accesses': all_accesses,
        'active_accesses': active_accesses,
        'expired_accesses': expired_accesses,
        'inactive_accesses': inactive_accesses,
        'status': status,
        'status_message': status_message,
        'has_active_access': len(active_accesses) > 0,
        'current_time': timezone.now(),
        'title': 'Investigator Portal'
    }
    return render(request, 'officials/investigator_portal.html', context)

@login_required
@user_passes_test(is_verified_investigator)
def investigator_case_dashboard(request, case_id):
    """Dashboard for investigators WITH active case access"""
    from .models import InvestigatorAccess
    
    # Get the specific case access
    case_access = InvestigatorAccess.objects.filter(
        id=case_id,
        investigator=request.user,
        active=True,
        access_end__gt=timezone.now()
    ).first()
    
    if not case_access:
        messages.error(request, "Case access not found or expired.")
        return redirect('investigator_portal')
    
    # Calculate time remaining
    remaining = case_access.access_end - timezone.now()
    hours_remaining = remaining.total_seconds() / 3600
    
    # Warn if less than 24 hours remaining
    warning = hours_remaining < 24
    
    context = {
        'case_access': case_access,
        'hours_remaining': round(hours_remaining, 2),
        'warning': warning,
        'has_active_access': True,
        'current_time': timezone.now(),
        'title': f'Case: {case_access.case_reference}'
    }
    return render(request, 'officials/investigator_case_dashboard.html', context)



def get_base_dashboard_context(request):
    return {
        "user": request.user,
        "role": getattr(request.user, "role", None),
        "current_time": timezone.now(),
    }
