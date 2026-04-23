from django.contrib import admin
from django.urls import path, include
from apps.core.views import home, public_dashboard_data, public_live_data, public_torneio_tv

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin-area/', include('apps.core.urls')),
    path('torneio/<slug:slug>/', public_torneio_tv, name='public_torneio_tv'),
    path('api/v1/public/torneio/<slug:slug>/dashboard/', public_dashboard_data, name='public_dashboard_data'),
    path('api/v1/public/torneio/<slug:slug>/live/', public_live_data, name='public_live_data'),
]
