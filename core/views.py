from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from django.shortcuts import render

@login_required
@role_required(['ADMIN'])
def policy_matrix_view(request):

    matrix = [
        {
            "action": "View Crime",
            "CITIZEN": False,
            "OFFICER": True,
            "INVESTIGATOR": True,
            "ADMIN": True,
            "JUDGE": True,
        },
        {
            "action": "Edit Crime",
            "CITIZEN": False,
            "OFFICER": False,
            "INVESTIGATOR": True,
            "ADMIN": True,
            "JUDGE": False,
        },
        {
            "action": "Change Complaint Status",
            "CITIZEN": False,
            "OFFICER": True,
            "INVESTIGATOR": True,
            "ADMIN": True,
            "JUDGE": False,
        },
        {
            "action": "Biometric Access (Warrant)",
            "CITIZEN": False,
            "OFFICER": False,
            "INVESTIGATOR": True,
            "ADMIN": False,
            "JUDGE": False,
        },
    ]

    return render(request, "core/policy_matrix.html", {
        "matrix": matrix
    })
