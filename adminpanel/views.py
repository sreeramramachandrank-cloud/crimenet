# ==============================
# DJANGO CORE
# ==============================
from django.contrib import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
import csv

# ==============================
# DECORATORS
# ==============================
from accounts.decorators import role_required

# ==============================
# MODELS
# ==============================
from accounts.models import User
from appeals.models import Appeal
from complaints.models import Complaint
from audit.models import AuditLog
from notifications.models import Notification
from officials.models import (
    OfficerProfile,
    OfficerDocument,
    RoleVerification,
    InvestigatorAccess
)

# ==============================
# SERVICES
# ==============================
from core.services.sla import SLAService
from core.services.escalation import EscalationService
from officials.models import OfficerProfile, RoleVerification, InvestigatorAccess


# =====================================================
# ADMIN DASHBOARD
# =====================================================
@login_required

def admin_dashboard(request):
    return render(request, 'adminpanel/dashboard.html', {
        'total_users': User.objects.count(),
        'pending_requests': User.objects.filter(
            requested_role__isnull=False
        ).count(),
    })


# =====================================================
# ROLE REQUESTS
# =====================================================
@login_required

def role_requests(request):
    users = User.objects.filter(requested_role__isnull=False)
    return render(request, 'adminpanel/role_requests.html', {
        'users': users
    })


from officials.models import RoleVerification, OfficerProfile

@login_required
def approve_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Get requested role from user
    requested_role = user.requested_role
    
    if not requested_role:
        # Also check if user has pending verification
        if hasattr(user, 'role_verification') and not user.role_verification.verified:
            requested_role = user.role_verification.role
        elif hasattr(user, 'officer_profile') and not user.officer_profile.verified:
            requested_role = 'OFFICER'
        else:
            messages.error(request, "No pending role request found.")
            return redirect('admin_users_list')
    
    # ✅ UPDATE USER ROLE
    user.role = requested_role
    user.requested_role = None  # Clear requested_role
    user.save(update_fields=['role', 'requested_role'])
    
    # ✅ HANDLE OFFICER APPROVAL
    if requested_role == 'OFFICER':
        if hasattr(user, 'officer_profile'):
            officer_profile = user.officer_profile
            officer_profile.verified = True
            officer_profile.verified_by = request.user
            officer_profile.verified_at = timezone.now()
            officer_profile.save()
        else:
            # Create officer profile if missing
            OfficerProfile.objects.create(
                user=user,
                rank="To be assigned",
                badge_id="TBD",
                department="To be assigned",
                reason_for_access="Approved by admin",
                verified=True
            )
    
    # ✅ HANDLE VERIFIED ROLES (INVESTIGATOR, FORENSIC, JUDGE, AUDITOR)
    elif requested_role in ['INVESTIGATOR', 'FORENSIC', 'JUDGE', 'AUDITOR']:
        if hasattr(user, 'role_verification'):
            role_verification = user.role_verification
            role_verification.verified = True
            role_verification.verified_by = request.user
            role_verification.verified_at = timezone.now()
            role_verification.save()
        else:
            # Create role verification if missing
            RoleVerification.objects.create(
                user=user,
                role=requested_role,
                rank="Approved",
                jurisdiction="System",
                reason_for_access="Approved by admin",
                verified=True
            )
    
    # ✅ SEND NOTIFICATION
    from notifications.models import Notification
    Notification.objects.create(
        user=user,
        title=f"Role Approved: {requested_role}",
        message=f"Your {requested_role} role has been approved by administrator.",
        notification_type='ROLE_APPROVAL'
    )
    
    # ✅ AUDIT LOG
    from audit.models import AuditLog
    AuditLog.objects.create(
        actor=request.user,
        target_user=user,
        action='ROLE_APPROVE',
        reason=f"Approved {requested_role} role for {user.username}"
    )
    
    messages.success(request, f"{user.username} approved as {requested_role}")
    return redirect('admin_users_list')

@login_required

def reject_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.requested_role = None
    user.save()

    Notification.objects.create(
        user=user,
        message="❌ Your role request was rejected."
    )

    return redirect('admin_role_requests')


# =====================================================
# USERS MANAGEMENT
# =====================================================
@login_required
def users_list(request):
    users = User.objects.all().order_by('username')

    user_rows = []

    for user in users:
        verification_status = '—'
        case_access = '—'

        # 🔹 NEW FLAGS (SAFE ADDITIONS)
        can_approve = False
        can_grant_access = False

        # 👮 OFFICER verification
        if user.role == 'OFFICER':
            if hasattr(user, 'officer_profile'):
                if user.officer_profile.verified:
                    verification_status = '✅ Verified'
                else:
                    verification_status = '⏳ Pending'
                    can_approve = True   # 🔹 ADD

        # 🔐 VERIFIED ROLES
        elif user.role in ['INVESTIGATOR', 'FORENSIC', 'JUDGE', 'AUDITOR']:
            if hasattr(user, 'role_verification'):
                if user.role_verification.verified:
                    verification_status = '✅ Verified'
                    if user.role == 'INVESTIGATOR':
                        can_grant_access = True   # 🔹 ADD
                else:
                    verification_status = '⏳ Pending'
                    can_approve = True   # 🔹 ADD

        # 🕵️ INVESTIGATOR case access
        if user.role == 'INVESTIGATOR':
            access = InvestigatorAccess.objects.filter(
                investigator=user,
                active=True
            ).first()

            if access:
                case_access = f"🟢 ACTIVE ({access.case_reference})"
            else:
                case_access = "🔴 EXPIRED / NONE"

        # 🔹 APPEND (ONLY ADDING FIELDS)
        user_rows.append({
            'user': user,
            'verification': verification_status,
            'case_access': case_access,
            'can_approve': can_approve,
            'can_grant_access': can_grant_access,
        })

    return render(request, 'adminpanel/users_list.html', {
        'user_rows': user_rows,
        'total_users': users.count(),   # 🔹 ADD
    })


@login_required

def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.is_superuser or user.role == 'ADMIN':
        return render(request, 'adminpanel/action_not_allowed.html', {
            'reason': 'Admin accounts cannot be blocked.'
        })

    if request.method == 'POST':
        reason = request.POST.get('reason')

        user.is_blocked = True
        user.block_reason = reason
        user.save()

        AuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action='BLOCK',
            reason=reason
        )

        return redirect('admin_users_list')

    return render(request, 'adminpanel/block_user.html', {'user': user})


@login_required

def unblock_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    user.is_blocked = False
    user.block_reason = None
    user.save()

    AuditLog.objects.create(
        actor=request.user,
        target_user=user,
        action='UNBLOCK',
        reason='Admin unblocked user'
    )

    return redirect('admin_users_list')


# =====================================================
# APPEALS
# =====================================================
@login_required

def appeals_list(request):
    appeals = Appeal.objects.order_by('-created_at')
    return render(request, 'adminpanel/appeals_list.html', {
        'appeals': appeals
    })


@login_required
@role_required(['ADMIN'])
def review_appeal(request, appeal_id):
    appeal = get_object_or_404(Appeal, id=appeal_id)

    if request.method == 'POST':
        appeal.status = request.POST.get('decision')
        appeal.admin_comment = request.POST.get('comment')
        appeal.reviewed_at = timezone.now()
        appeal.save()

        if appeal.status == 'APPROVED':
            appeal.user.is_blocked = False
            appeal.user.block_reason = None
            appeal.user.save()

        AuditLog.objects.create(
            actor=request.user,
            target_user=appeal.user,
            action='APPEAL_REVIEWED',
            reason=appeal.status
        )

        return redirect('admin_appeals')

    return render(request, 'adminpanel/review_appeal.html', {
        'appeal': appeal
    })


# =====================================================
# ANALYTICS
# =====================================================
@login_required

def analytics_dashboard(request):
    return render(request, 'adminpanel/analytics.html', {
        'total_users': User.objects.count(),
        'total_complaints': Complaint.objects.count(),
        'pending_complaints': Complaint.objects.filter(status='PENDING').count(),
        'accepted_complaints': Complaint.objects.filter(status='ACCEPTED').count(),
        'rejected_complaints': Complaint.objects.filter(status='REJECTED').count(),
        'closed_complaints': Complaint.objects.filter(status='CLOSED').count(),
    })


@login_required

def complaint_trends(request):
    daily = (
        Complaint.objects
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
    )

    monthly = (
        Complaint.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
    )

    return render(request, 'adminpanel/trends.html', {
        'daily': daily,
        'monthly': monthly,
    })


# =====================================================
# MISUSE & AUDIT
# =====================================================
@login_required

def misuse_alerts(request):
    alerts = (
        AuditLog.objects
        .filter(action='COMPLAINT_REJECTED')
        .values('actor__username')
        .annotate(count=Count('id'))
        .filter(count__gte=3)
    )

    return render(request, 'adminpanel/misuse_alerts.html', {
        'alerts': alerts
    })


@login_required

def audit_logs(request):
    logs = AuditLog.objects.all().order_by('-timestamp')
    return render(request, 'adminpanel/audit_logs.html', {
        'logs': logs
    })


@login_required

def biometric_logs(request):
    logs = AuditLog.objects.filter(
        action__in=['BIOMETRIC_ACCESS', 'BIOMETRIC_MISUSE_ALERT']
    ).order_by('-timestamp')

    return render(request, 'adminpanel/biometric_logs.html', {
        'logs': logs
    })


# =====================================================
# SLA & ESCALATION
# =====================================================
@login_required

def sla_check(request):
    complaints = Complaint.objects.filter(sla_breached=False)
    breached = 0

    for c in complaints:
        if SLAService.is_breached(c):
            c.sla_breached = True
            EscalationService.escalate(c)
            c.save()
            breached += 1

            AuditLog.objects.create(
                actor=request.user,
                target_user=c.citizen,
                action='SLA_BREACH',
                reason='SLA breached and escalated'
            )

    return render(request, 'adminpanel/sla_check.html', {
        'breached': breached
    })


# =====================================================
# EXPORT
# =====================================================
@login_required

def export_complaints(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="complaints.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Citizen', 'Subject', 'Status', 'SLA Breached'])

    for c in Complaint.objects.all():
        writer.writerow([
            c.id,
            c.citizen.username,
            c.subject,
            c.status,
            c.sla_breached
        ])

    return response


# =====================================================
# INVESTIGATOR ACCESS
# =====================================================
@login_required

def grant_investigator_access(request, user_id):
    if request.method == 'POST':
        InvestigatorAccess.objects.create(
            investigator_id=user_id,
            case_reference=request.POST['case_reference'],
            purpose=request.POST['purpose'],
            access_end=request.POST['access_end'],
            created_by=request.user
        )

        Notification.objects.create(
            user_id=user_id,
            message="🔐 Investigation access granted with time limit."
        )

        return redirect('admin_dashboard')

    return render(request, 'adminpanel/grant_investigator_access.html', {
        'user_id': user_id
    })



@login_required
def user_details(request, user_id):
    user = get_object_or_404(User, id=user_id)

    officer_profile = getattr(user, 'officer_profile', None)
    role_verification = getattr(user, 'role_verification', None)

    investigator_access = InvestigatorAccess.objects.filter(
        investigator=user
    ).order_by('-access_end')

    return render(request, 'adminpanel/user_details.html', {
        'user_obj': user,
        'officer_profile': officer_profile,
        'role_verification': role_verification,
        'investigator_access': investigator_access,
    })




from officials.models import OfficerProfile, RoleVerification

@login_required
# adminpanel/views.py - Update the view_verification function

def view_verification(request, user_id):
    from django.shortcuts import get_object_or_404, render
    from accounts.models import User
    from officials.models import RoleVerification, OfficerProfile
    from django.conf import settings
    import os
    
    user = get_object_or_404(User, id=user_id)
    
    context = {
        'user': user,
        'role_verification': None,
        'officer_profile': None,
        'file_url': None,
    }
    
    # Check RoleVerification (for INVESTIGATOR, FORENSIC, JUDGE, AUDITOR)
    if hasattr(user, 'role_verification'):
        role_verification = user.role_verification
        context['role_verification'] = role_verification
        
        # Get file URL if exists
        if role_verification.appointment_order:
            context['file_url'] = role_verification.appointment_order.url
            context['file_name'] = os.path.basename(role_verification.appointment_order.name)
    
    # Check OfficerProfile
    elif hasattr(user, 'officer_profile'):
        context['officer_profile'] = user.officer_profile
    
    return render(request, 'adminpanel/view_verification.html', context)








# adminpanel/views.py or wherever user list is displayed

# Add this method to your user display logic
def get_investigator_access_display(user):
    if user.role != 'INVESTIGATOR':
        return "—"
    
    from officials.models import InvestigatorAccess
    from django.utils import timezone
    
    # Check for active access
    active = InvestigatorAccess.objects.filter(
        investigator=user,
        active=True,
        access_end__gt=timezone.now()
    ).exists()
    
    if active:
        return "● ACTIVE"
    
    # Check for any access records
    any_access = InvestigatorAccess.objects.filter(investigator=user).exists()
    
    if any_access:
        # Check if expired
        expired = InvestigatorAccess.objects.filter(
            investigator=user,
            active=True,
            access_end__lte=timezone.now()
        ).exists()
        
        if expired:
            return "● EXPIRED"
        else:
            return "● INACTIVE"
    
    return "● NONE (Verified)"




def get_user_list(request):
    users = User.objects.all()
    
    # Add access status to each user
    for user in users:
        user.access_display = get_investigator_access_display(user)
    
    return render(request, 'adminpanel/user_list.html', {'users': users})



# adminpanel/views.py - Find and fix the approve_role function



def pending_role_requests(request):
    from accounts.models import User
    from officials.models import RoleVerification, OfficerProfile
    
    # Get users with pending role verification
    pending_verifications = RoleVerification.objects.filter(
        verified=False
    ).select_related('user')
    
    # Get users with pending officer profile verification
    pending_officers = OfficerProfile.objects.filter(
        verified=False
    ).select_related('user')
    
    # Combine and prepare data
    pending_requests = []
    
    # Add role verifications
    for verification in pending_verifications:
        pending_requests.append({
            'type': 'ROLE_VERIFICATION',
            'user': verification.user,
            'requested_role': verification.role,
            'verification': verification,
            'submitted_at': verification.created_at,
            'has_file': bool(verification.appointment_order),
            'file_url': verification.appointment_order.url if verification.appointment_order else None,
        })
    
    # Add officer profiles
    for officer in pending_officers:
        pending_requests.append({
            'type': 'OFFICER_PROFILE',
            'user': officer.user,
            'requested_role': 'OFFICER',
            'officer_profile': officer,
            'submitted_at': officer.submitted_at,
            'has_file': officer.user.officer_documents.exists(),
            'documents': list(officer.user.officer_documents.all()),
        })
    
    # Sort by submission date
    pending_requests.sort(key=lambda x: x['submitted_at'], reverse=True)
    
    return render(request, 'adminpanel/pending_requests.html', {
        'pending_requests': pending_requests,
        'total_pending': len(pending_requests),
    })




# adminpanel/views.py - Add reject_verification function

def reject_verification(request, user_id):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from accounts.models import User
    from officials.models import RoleVerification, OfficerProfile
    
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        if not rejection_reason:
            messages.error(request, "Please provide a rejection reason.")
            return redirect('admin_view_verification', user_id=user_id)
        
        # Check what type of verification to reject
        if hasattr(user, 'role_verification'):
            verification = user.role_verification
            verification.delete()  # Or mark as rejected
            
            # Send notification
            from notifications.models import Notification
            Notification.objects.create(
                user=user,
                title="Role Verification Rejected",
                message=f"Your {verification.role} role request was rejected. Reason: {rejection_reason}",
                notification_type='ROLE_APPROVAL'
            )
            
            messages.success(request, f"{user.username}'s role request has been rejected.")
            
        elif hasattr(user, 'officer_profile'):
            officer_profile = user.officer_profile
            officer_profile.delete()  # Or mark as rejected
            
            # Send notification
            from notifications.models import Notification
            Notification.objects.create(
                user=user,
                title="Officer Verification Rejected",
                message=f"Your officer role request was rejected. Reason: {rejection_reason}",
                notification_type='ROLE_APPROVAL'
            )
            
            messages.success(request, f"{user.username}'s officer request has been rejected.")
        
        # Audit log
        from audit.models import AuditLog
        AuditLog.objects.create(
    actor=request.user,
    target_user=user,
    action='ROLE_APPROVE',  # Must be from ACTION_CHOICES
    reason=f"Approved {user.role} role for {user.username}"  # Use 'reason' not 'details'
)