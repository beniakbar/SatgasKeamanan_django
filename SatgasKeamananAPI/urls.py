# SatgasKeamananAPI/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import JWT views
from rest_framework_simplejwt.views import (
    TokenObtainPairView, # Digunakan untuk login (mendapatkan token pertama)
    TokenRefreshView,    # Digunakan untuk memperbarui access token
)

urlpatterns = [
    # 1. Django Admin Default (Opsional)
    path('admin/', admin.site.urls),

    # 2. Web Admin Interface (Custom Dashboard)
    # Ini diletakkan di root agar http://localhost:8000/ langsung masuk sini
    path('', include('core.web_urls')),

    # 3. JWT Authentication Endpoints (Untuk Android)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 4. Aplikasi Core API (Untuk Android)
    path('api/', include('core.urls')),
]

# Konfigurasi Media Files (Foto Upload)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
