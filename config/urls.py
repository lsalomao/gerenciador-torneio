from django.contrib import admin
from django.urls import path, include
from apps.core.views import home

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin-area/', include('apps.core.urls')),
]
