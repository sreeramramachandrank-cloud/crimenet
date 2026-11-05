from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Complaint
from .forms import ComplaintForm
from audit.models import AuditLog

from django.utils import timezone
from datetime import timedelta

@login_required
@role_required(['CITIZEN'])
def create_complaint(request):
    form = ComplaintForm(request.POST or None)

    if form.is_valid():
        complaint = form.save(commit=False)
        complaint.citizen = request.user

        # ✅ SLA DEADLINE (ADD HERE)
        complaint.sla_deadline = timezone.now() + timedelta(hours=48)

        complaint.save()
        return redirect('my_complaints')

    return render(request, 'complaints/create.html', {'form': form})


# Citizen: View own complaints
@login_required
@role_required(['CITIZEN'])
def my_complaints(request):
    complaints = Complaint.objects.filter(citizen=request.user)
    return render(request, 'complaints/my_complaints.html', {'complaints': complaints})


# Police: View all complaints
@login_required
@role_required(['OFFICER', 'INVESTIGATOR'])
def police_complaints(request):
    complaints = Complaint.objects.all()
    return render(request, 'complaints/police_list.html', {'complaints': complaints})


# Police: Update complaint status
@login_required
@role_required(['OFFICER', 'INVESTIGATOR'])
def update_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == 'POST':
        complaint.status = request.POST.get('status')
        complaint.police_remark = request.POST.get('police_remark')
        complaint.save()
        return redirect('police_complaints')

    return render(request, 'complaints/update.html', {'complaint': complaint})


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from core.policies import ComplaintPolicy
from core.enforce import enforce
from .models import Complaint

from core.services.notifications import NotificationService

@login_required
def update_complaint_status(request, complaint_id, new_status):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    result = ComplaintPolicy.can_change_status(
        request.user,
        complaint,
        new_status
    )

    denied = enforce(result)
    if denied:
        return denied

    if request.method == 'POST':
        old_status = complaint.status

        complaint.status = new_status
        complaint.police_remark = request.POST.get('police_remark', '')
        complaint.save()

        # ✅ NOTIFICATION (ADD HERE)
        if complaint.citizen.email:
            NotificationService.notify(
                "Complaint Status Updated",
                f"Your complaint '{complaint.subject}' is now {new_status}",
                complaint.citizen.email
            )

        # ✅ AUDIT LOG (already added)
        AuditLog.objects.create(
            actor=request.user,
            target_user=complaint.citizen,
            action='COMPLAINT_STATUS_CHANGE',
            reason=f"{old_status} → {new_status}: {complaint.police_remark}"
        )

        return redirect('complaint_detail', complaint_id=complaint.id)

    return render(request, 'complaints/update_status.html', {
        'complaint': complaint,
        'new_status': new_status
    })

from django.contrib.auth.decorators import login_required
from core.policies import ComplaintPolicy
from .models import Complaint


@login_required
def police_complaint_list(request):
    user = request.user

    if user.role == 'OFFICER':
        complaints = Complaint.objects.exclude(status__in=['CLOSED', 'REJECTED'])
    elif user.role in ['INVESTIGATOR', 'ADMIN']:
        complaints = Complaint.objects.all()
    else:
        complaints = Complaint.objects.none()

    return render(request, 'complaints/police_list.html', {
        'complaints': complaints
    })




@login_required
def citizen_complaint_tracking(request):
    complaints = Complaint.objects.filter(citizen=request.user)
    return render(request, 'complaints/citizen_tracking.html', {
        'complaints': complaints
    })





from audit.models import AuditLog

@login_required
def complaint_timeline(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Citizen can see only their complaint
    if request.user.role == 'CITIZEN' and complaint.citizen != request.user:
        return HttpResponseForbidden("Not allowed")

    logs = AuditLog.objects.filter(
        target_user=complaint.citizen,
        action='COMPLAINT_STATUS_CHANGE'
    ).order_by('timestamp')

    return render(request, 'complaints/timeline.html', {
        'complaint': complaint,
        'logs': logs
    })
