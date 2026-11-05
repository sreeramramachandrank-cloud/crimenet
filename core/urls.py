from django.urls import path
from .views import policy_matrix_view

urlpatterns = [
    path('policy-matrix/', policy_matrix_view, name='policy_matrix'),
]
