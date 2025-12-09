from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserProfileView, 
    RegisterUserView,
    PresensiViewSet,
    LaporanViewSet,
    PetugasViewSet,
    AdminPresensiViewSet,
    AdminLaporanViewSet,
    HarianPresensiReportView,
    DashboardStatsAPIView,
    EmergencyAlarmViewSet # Import Baru
)

router = DefaultRouter()

# Endpoint Petugas (Presensi & Laporan)
router.register(r'presensi', PresensiViewSet, basename='presensi')
router.register(r'laporan', LaporanViewSet, basename='laporan')
router.register(r'alarm', EmergencyAlarmViewSet, basename='alarm') # Endpoint Alarm


# Endpoint Admin → Data Petugas
router.register(r'admin/petugas', PetugasViewSet, basename='admin-petugas')

# Endpoint Admin → Monitoring Presensi & Laporan
router.register(r'admin/presensi', AdminPresensiViewSet, basename='admin-presensi')
router.register(r'admin/laporan', AdminLaporanViewSet, basename='admin-laporan')


urlpatterns = [
    # Admin: Dashboard Stats (Untuk Mobile)
    path(
        'admin/dashboard/stats/',
        DashboardStatsAPIView.as_view(),
        name='api-dashboard-stats'
    ),

    # Admin: laporan presensi harian
    path(
        'admin/laporan/harian/',
        HarianPresensiReportView.as_view(),
        name='harian-presensi-report'
    ),
    
    # User endpoints
    path('user/profile/', UserProfileView.as_view(), name='user-profile'), 
    path('user/register/', RegisterUserView.as_view(), name='user-register'),

    # Router URLs (General patterns)
    path('', include(router.urls)),
]
