from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import AuditLog
from django.shortcuts import render

@login_required
@role_required(['ADMIN', 'JUDGE', 'AUDITOR'])
def audit_timeline(request):
    logs = AuditLog.objects.all().order_by('-timestamp')[:200]

    return render(request, 'audit/timeline.html', {
        'logs': logs
    })
