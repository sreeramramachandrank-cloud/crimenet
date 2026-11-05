from datetime import timezone
from django.db.models import Count

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.conf import settings

from accounts.decorators import role_required
from core.enforce import enforce
from core.policies.biometrics import BiometricPolicy
from core.services.biometric_monitor import BiometricMisuseDetector

from audit.models import AuditLog
from biometrics.models import BiometricRecord, Warrant
from accounts.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from .forms import BiometricEnrollForm


@login_required
def biometric_search(request):

    # 1️⃣ GET WARRANT (REQUIRED)
    warrant_id = request.GET.get('warrant_id')
    warrant = get_object_or_404(Warrant, id=warrant_id)

    # 2️⃣ POLICY CHECK
    result = BiometricPolicy.can_access(
        request.user,
        warrant=warrant
    )


    records = BiometricRecord.objects.filter(
    fingerprint_hash__icontains=query,
    confidence__gte=settings.MIN_BIOMETRIC_CONFIDENCE
)

    # 3️⃣ ENFORCE DECISION
    denied = enforce(result)
    if denied:
        return denied

    records = None

    # 4️⃣ BUSINESS LOGIC
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()

        if query:
            records = BiometricRecord.objects.filter(
                fingerprint_hash__icontains=query,
                confidence__gte=settings.MIN_BIOMETRIC_CONFIDENCE
            )

            # 5️⃣ AUDIT LOG
            AuditLog.objects.create(
                actor=request.user,
                target_user=None,
                action='BIOMETRIC_ACCESS',
                reason=f'Biometric search performed (query={query})'
            )

            # 6️⃣ MISUSE DETECTION
            if BiometricMisuseDetector.is_excessive(request.user):
                AuditLog.objects.create(
                    actor=request.user,
                    target_user=None,
                    action='BIOMETRIC_MISUSE_ALERT',
                    reason='Excessive biometric searches detected'
                )

    # 7️⃣ RESPONSE
    return render(request, 'biometrics/search.html', {
        'records': records,
        'warrant': warrant
    })




@login_required
def enroll_biometrics(request, user_id):
    result = BiometricPolicy.can_enroll(request.user)
    denied = enforce(result)
    if denied:
        return denied

    target_user = get_object_or_404(User, id=user_id)

    if hasattr(target_user, 'biometric_record'):
        return HttpResponseForbidden("Biometrics already exist")

    form = BiometricEnrollForm(request.POST or None)

    if form.is_valid():
        record = form.save(commit=False)
        record.user = target_user
        record.save()

        AuditLog.objects.create(
            actor=request.user,
            target_user=target_user,
            action='BIOMETRIC_ENROLL',
            reason='Biometric data enrolled by forensic'
        )

        return redirect('dashboard')

    return render(request, 'biometrics/enroll.html', {
        'form': form,
        'target_user': target_user
    })










@login_required
def biometric_enroll(request, user_id):
    # 🔐 CORE POLICY CHECK
    result = BiometricPolicy.can_enroll(request.user)
    denied = enforce(result)
    if denied:
        return denied

    target_user = User.objects.get(id=user_id)

    record = getattr(target_user, 'biometric_record', None)

    form = BiometricEnrollForm(
        request.POST or None,
        instance=record
    )

    if form.is_valid():
        biometric = form.save(commit=False)
        biometric.user = target_user
        biometric.save()

        # ✅ AUDIT LOG
        AuditLog.objects.create(
            actor=request.user,
            target_user=target_user,
            action='BIOMETRIC_ENROLL',
            reason='Biometric data enrolled by forensic analyst'
        )

        return redirect('forensic_dashboard')

    return render(request, 'biometrics/enroll.html', {
        'form': form,
        'target_user': target_user
    })





# @login_required
# @role_required(['FORENSIC', 'ADMIN'])
# def forensic_dashboard(request):
#     today = timezone.now().date()

#     data = {
#         # Biometrics
#         'total_biometrics': BiometricRecord.objects.count(),

#         # Searches today
#         'searches_today': AuditLog.objects.filter(
#             action='BIOMETRIC_ACCESS',
#             timestamp__date=today
#         ).count(),

#         # Misuse alerts
#         'misuse_alerts': AuditLog.objects.filter(
#             action='BIOMETRIC_MISUSE_ALERT'
#         ).count(),

#         # Confidence buckets
#         'high_confidence': BiometricRecord.objects.filter(confidence__gte=0.9).count(),
#         'medium_confidence': BiometricRecord.objects.filter(confidence__range=(0.7, 0.89)).count(),
#         'low_confidence': BiometricRecord.objects.filter(confidence__lt=0.7).count(),

#         # Top searched users
#         'top_targets': (
#             AuditLog.objects
#             .filter(action='BIOMETRIC_ACCESS')
#             .values('actor__username')
#             .annotate(total=count('id'))
#             .order_by('-total')[:5]
#         )
#     }

#     return render(request, 'biometrics/analytics.html', data)
from django.utils import timezone

@login_required
@role_required(['FORENSIC', 'ADMIN'])
def forensic_dashboard(request):
    today = timezone.now().date()

    data = {
        'total_biometrics': BiometricRecord.objects.count(),

        'searches_today': AuditLog.objects.filter(
            action='BIOMETRIC_ACCESS',
            timestamp__date=today
        ).count(),

        'misuse_alerts': AuditLog.objects.filter(
            action='BIOMETRIC_MISUSE_ALERT'
        ).count(),

        'high_confidence': BiometricRecord.objects.filter(confidence__gte=0.9).count(),
        'medium_confidence': BiometricRecord.objects.filter(confidence__range=(0.7, 0.89)).count(),
        'low_confidence': BiometricRecord.objects.filter(confidence__lt=0.7).count(),

        'top_targets': (
    AuditLog.objects
    .filter(action='BIOMETRIC_ACCESS')
    .values('actor__username')
    .annotate(total=Count('id'))
    .order_by('-total')[:5]
)

    }

    return render(request, 'biometrics/analytics.html', data)


