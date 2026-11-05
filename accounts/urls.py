from .views import register_view
from .views import login_view
from .views import dashboard    
from django.urls import path
from .views import logout_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),
]
