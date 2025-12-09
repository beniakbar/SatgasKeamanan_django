from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from .web_views import (
    DashboardView,
    WebPetugasListView, 
    WebRekapHarianView, 
    WebPresensiListView,
    WebPresensiDetailView,
    WebLaporanListView,
    WebLaporanDetailView,
    WebAlarmListView,
    WebAlarmDetailView,
    logout_view
)

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='web-dashboard', permanent=False)),

    path('dashboard/', DashboardView.as_view(), name='web-dashboard'),
    
    # Petugas & Rekap
    path('dashboard/petugas/', WebPetugasListView.as_view(), name='web-petugas-list'),
    path('dashboard/rekap-harian/', WebRekapHarianView.as_view(), name='web-rekap-harian'),

    # Presensi
    path('dashboard/presensi/', WebPresensiListView.as_view(), name='web-presensi-list'),
    path('dashboard/presensi/<int:pk>/', WebPresensiDetailView.as_view(), name='web-presensi-detail'),

    # Laporan
    path('dashboard/laporan/', WebLaporanListView.as_view(), name='web-laporan-list'),
    path('dashboard/laporan/<int:pk>/', WebLaporanDetailView.as_view(), name='web-laporan-detail'),
    
    # Alarm
    path('dashboard/alarm/', WebAlarmListView.as_view(), name='web-alarm-list'),
    path('dashboard/alarm/<int:pk>/', WebAlarmDetailView.as_view(), name='web-alarm-detail'),

    # Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # Gunakan view custom untuk logout (agar support GET request)
    path('accounts/logout/', logout_view, name='logout'),
]
