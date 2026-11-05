"""
URL configuration for crimenet project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from adminpanel import views
from .views import home_view

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views 

urlpatterns = [

    path('', home_view, name='home'),  
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('crimes/', include('crimes.urls')),
    path('dashboard/', include('accounts.urls')),
    path('complaints/', include('complaints.urls')),
    path('admin-panel/', include('adminpanel.urls')),
    path('appeals/', include('appeals.urls')),
    path('biometrics/', include('biometrics.urls')),
    path('core/', include('core.urls')),
    path('officials/', include('officials.urls')),
 
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



