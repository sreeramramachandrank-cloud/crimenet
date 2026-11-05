from .models import AuditLog
from .utils import get_client_ip

def audit_action(action_name):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)

            if request.user.is_authenticated:
                AuditLog.objects.create(
                    user=request.user,
                    action=action_name,
                    role=request.user.role,
                    ip_address=get_client_ip(request)
                )

            return response
        return wrapper
    return decorator
