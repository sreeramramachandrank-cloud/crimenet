from django.http import HttpResponseForbidden
from django.shortcuts import render

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return HttpResponseForbidden("Access Denied")

            # 🚫 BLOCKED USER CHECK
            if request.user.is_blocked:
                return render(
                    request,
                    'accounts/blocked.html',
                    {'reason': request.user.block_reason}
                )

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("Access Denied")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
