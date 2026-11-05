# officials/decorators.py
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def investigator_access_required(view_func):
    """
    Decorator to check if investigator has active time-limited access
    Use this on views that require active investigation access
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        
        # Only apply to investigators
        if hasattr(user, 'role') and user.role == 'INVESTIGATOR':
            # Check for active InvestigatorAccess
            active_access = user.investigation_accesses.filter(
                active=True,
                access_end__gt=timezone.now()
            ).exists()
            
            if not active_access:
                messages.error(
                    request, 
                    "🔒 Investigation Access Required\n"
                    "You need active investigation access to view this page."
                )
                return redirect('investigator_dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def check_investigator_access(user):
    """
    Utility function to check investigator access status
    Returns: (has_access, message, redirect_url)
    """
    if not hasattr(user, 'role') or user.role != 'INVESTIGATOR':
        return True, "", None  # Not an investigator
    
    # Check for active InvestigatorAccess
    active_accesses = user.investigation_accesses.filter(
        active=True,
        access_end__gt=timezone.now()
    )
    
    if not active_accesses.exists():
        # Investigator but no active access - normal login allowed
        return True, "No active investigation access", None
    
    # Check if any access is expired
    expired_accesses = user.investigation_accesses.filter(
        active=True,
        access_end__lte=timezone.now()
    )
    
    if expired_accesses.exists():
        # Mark expired accesses as inactive
        expired_accesses.update(active=False)
        return False, "Investigation Access Ended", 'investigator_dashboard'
    
    return True, "Active investigation access", 'investigator_active_dashboard'