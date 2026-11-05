from django.http import HttpResponseForbidden

def enforce(policy_result):
    if not policy_result.allowed:
        return HttpResponseForbidden(policy_result.reason)
    return None
