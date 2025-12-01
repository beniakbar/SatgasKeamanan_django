# core/views.py
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
User = get_user_model()

from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import User, Presensi, Laporan
from .serializers import (
    PetugasDetailSerializer,
    AdminPresensiSerializer,
    AdminLaporanSerializer,
    PresensiSerializer,
    LaporanSerializer,
    EmailTokenObtainPairSerializer,
    UserSerializer,
    PetugasStatusPresensiSerializer,
    UpdateProfileSerializer # Import Serializer Baru
)

from rest_framework_simplejwt.views import TokenObtainPairView


class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        phone_number = request.data.get("phone_number")
        name = request.data.get("name") 

        if not email or not password:
            return Response({"error": "Email dan password wajib diisi."},
                            status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email sudah terdaftar."},
                            status=status.HTTP_400_BAD_REQUEST)

        first_name = ""
        last_name = ""
        if name:
            parts = name.strip().split(" ", 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        user = User.objects.create_user(
            email=email,
            password=password,
            phone_number=phone_number,
            first_name=first_name, 
            last_name=last_name
        )

        return Response(
            {"message": "User berhasil dibuat."},
            status=status.HTTP_201_CREATED
        )

# ============================================
# 1. CUSTOM PERMISSIONS
# ============================================

class IsPetugas(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_petugas)


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)

# ============================================
# 2. DASHBOARD API (UPDATED)
# ============================================
class DashboardStatsAPIView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.localdate()
        
        total_petugas = User.objects.filter(is_petugas=True).count()
        
        hadir_today = Presensi.objects.filter(
            timestamp__date=today, 
            status_validasi='hadir'
        ).values('petugas').distinct().count()
        
        belum_hadir = total_petugas - hadir_today
        laporan_baru = Laporan.objects.filter(timestamp__date=today).count()

        recent_presensi_qs = Presensi.objects.select_related('petugas').order_by('-timestamp')[:5]
        recent_presensi_data = AdminPresensiSerializer(recent_presensi_qs, many=True, context={'request': request}).data

        open_laporan_qs = Laporan.objects.select_related('petugas').filter(status='lapor').order_by('-timestamp')[:5]
        open_laporan_data = AdminLaporanSerializer(open_laporan_qs, many=True, context={'request': request}).data

        return Response({
            'total_petugas': total_petugas,
            'hadir_today': hadir_today,
            'belum_hadir': belum_hadir,
            'laporan_baru': laporan_baru,
            'recent_presensi': recent_presensi_data,
            'open_laporan': open_laporan_data
        })

# ============================================
# 3. VIEWS LAINNYA
# ============================================

class PetugasViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_petugas=True).order_by('email')
    serializer_class = PetugasDetailSerializer
    permission_classes = [IsAdmin]


class AdminPresensiViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Presensi.objects.all().order_by('-timestamp')
    serializer_class = AdminPresensiSerializer
    permission_classes = [IsAdmin]


class AdminLaporanViewSet(viewsets.ModelViewSet):
    queryset = Laporan.objects.all().order_by('-timestamp')
    serializer_class = AdminLaporanSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Laporan hanya bisa dibuat oleh Petugas.'},
            status=status.HTTP_403_FORBIDDEN
        )


class PresensiViewSet(viewsets.ModelViewSet):
    serializer_class = PresensiSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Presensi.objects.all().order_by('-timestamp')
        if user.is_petugas:
            return Presensi.objects.filter(petugas=user).order_by('-timestamp')
        return Presensi.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_petugas:
            raise permissions.exceptions.PermissionDenied("Hanya Petugas yang dapat membuat presensi.")

        today = timezone.localdate()

        if Presensi.objects.filter(petugas=self.request.user, timestamp__date=today).exists():
            raise serializers.ValidationError("Anda sudah melakukan presensi harian hari ini.")

        serializer.save(petugas=self.request.user)


class HarianPresensiReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        date_str = request.query_params.get('date')
        target_date = timezone.localdate() 

        if date_str:
            parsed_date = parse_date(date_str)
            if parsed_date:
                target_date = parsed_date
            else:
                return Response({'error': 'Format tanggal salah. Gunakan YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        petugas_queryset = User.objects.filter(is_petugas=True).order_by('email')
        
        serializer_context = {
            'request': request,
            'target_date': target_date
        }
        
        serializer = PetugasStatusPresensiSerializer(
            petugas_queryset, 
            many=True, 
            context=serializer_context
        )

        data = serializer.data
        total_petugas = len(data)
        hadir = sum(1 for p in data if p.get('has_presensi_today'))

        return Response({
            'report_date': target_date.isoformat(),
            'total_petugas': total_petugas,
            'petugas_hadir': hadir,
            'petugas_belum_hadir': total_petugas - hadir,
            'data': data
        })


class LaporanViewSet(viewsets.ModelViewSet):
    serializer_class = LaporanSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Laporan.objects.all().order_by('-timestamp')
        if user.is_petugas:
            return Laporan.objects.filter(petugas=user).order_by('-timestamp')
        return Laporan.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_petugas:
            raise permissions.exceptions.PermissionDenied("Hanya Petugas yang dapat membuat laporan.")

        serializer.save(petugas=self.request.user)


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # PATCH: Gunakan UpdateProfileSerializer agar validasi email tidak konflik
    def patch(self, request):
        user = request.user
        serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Kembalikan data user lengkap (termasuk email) setelah update
            return Response(UserSerializer(user).data)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
