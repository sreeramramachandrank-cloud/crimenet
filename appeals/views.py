from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import AdminContactRequest, Appeal
from accounts.models import User
from audit.models import AuditLog
from django.shortcuts import get_object_or_404


@login_required
def submit_appeal(request):
    user = request.user

    if not user.is_blocked:
        return redirect('dashboard')

    if Appeal.objects.filter(user=user, status='PENDING').exists():
        return render(request, 'appeals/already_submitted.html')

    if request.method == 'POST':
        reason = request.POST.get('reason')
        Appeal.objects.create(user=user, reason=reason)
        return render(request, 'appeals/appeal_submitted.html')

    return render(request, 'appeals/submit_appeal.html')





@login_required
def contact_admin(request, admin_id):
    admin = get_object_or_404(User, id=admin_id, role='ADMIN')

    if request.method == 'POST':
        message = request.POST.get('message')

        AdminContactRequest.objects.create(
            user=request.user,
            admin=admin,
            message=message
        )

        AuditLog.objects.create(
            actor=request.user,
            target_user=admin,
            action='ADMIN_CONTACT_REQUEST',
            reason=message
        )

        return redirect('dashboard')

    return render(request, 'appeals/contact_admin.html', {
        'admin': admin
    })
