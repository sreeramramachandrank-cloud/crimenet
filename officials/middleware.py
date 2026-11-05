from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse

class InvestigatorAccessMiddleware:
    """
    Enforces investigator time-limited access.
    MUST run after AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Public paths that MUST NOT be intercepted
        self.public_paths = [
            '/',
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/register/',
            '/accounts/dashboard/',
        ]

        self.active_dashboard_path = '/officials/investigator/active-dashboard/'

    def __call__(self, request):
        path = request.path

        # ✅ 1. Never touch public paths
        if path in self.public_paths:
            return self.get_response(request)

        # ✅ 2. Skip unauthenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)

        # ✅ 3. Only apply to investigators
        if getattr(request.user, 'role', None) != 'INVESTIGATOR':
            return self.get_response(request)

        from officials.models import InvestigatorAccess

        now = timezone.now()

        has_active_access = InvestigatorAccess.objects.filter(
            investigator=request.user,
            active=True,
            access_end__gt=now
        ).exists()

        # ✅ 4. Investigator WITH active access
        if has_active_access:
            # Prevent redirect loop
            if path != self.active_dashboard_path:
                return redirect(self.active_dashboard_path)

        return self.get_response(request)
