# core/serializers.py
from rest_framework import serializers
from .models import User, Presensi, Laporan
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'profile_picture', 'last_login', 'is_active', 'is_admin', 'is_petugas']
        read_only_fields = ['is_admin', 'is_petugas', 'last_login']

# Serializer KHUSUS untuk update profil
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'profile_picture']
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'phone_number': {'required': False, 'allow_blank': True},
            'profile_picture': {'required': False}, # Gambar tidak wajib
        }

class PresensiSerializer(serializers.ModelSerializer):
    petugas_name = serializers.CharField(source='petugas.first_name', read_only=True)

    class Meta:
        model = Presensi
        fields = [
            'id', 'petugas', 'petugas_name', 'timestamp',
            'latitude', 'longitude', 'location_note',
            'note', 'selfie_photo', 'status_validasi' 
        ]
        read_only_fields = ['petugas', 'timestamp', 'status_validasi'] 

        extra_kwargs = {
            'location_note': {'required': False, 'allow_blank': True},
            'note': {'required': False, 'allow_blank': True},
        }

class LaporanSerializer(serializers.ModelSerializer):
    petugas_name = serializers.CharField(source='petugas.first_name', read_only=True)

    class Meta:
        model = Laporan
        fields = ['id', 'petugas', 'petugas_name', 'timestamp', 'latitude', 'longitude', 'location_note', 'note', 'photo', 'status', 'priority']
        read_only_fields = ['petugas', 'timestamp', 'status', 'priority']


class PetugasDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number', 
            'profile_picture', 'is_active', 'last_login', 'date_joined'
        ]
        read_only_fields = ['email', 'is_active', 'last_login', 'date_joined']

class AdminPresensiSerializer(serializers.ModelSerializer):
    petugas_name = serializers.CharField(source='petugas.first_name', read_only=True)
    petugas_email = serializers.EmailField(source='petugas.email', read_only=True)

    class Meta:
        model = Presensi
        fields = [
            'id', 'petugas_name', 'petugas_email', 'timestamp', 
            'latitude', 'longitude', 'location_note', 'note', 'selfie_photo',
            'status_validasi' 
        ]

class PetugasStatusPresensiSerializer(serializers.ModelSerializer):
    has_presensi_today = serializers.SerializerMethodField()
    last_presensi = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'email', 'phone_number', 'has_presensi_today', 'last_presensi'
        ]

    def get_full_name(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full if full else obj.email 

    def get_target_date(self):
        return self.context.get('target_date', timezone.localdate())

    def get_has_presensi_today(self, obj):
        target_date = self.get_target_date()
        return Presensi.objects.filter(
            petugas=obj, 
            timestamp__date=target_date
        ).exists()

    def get_last_presensi(self, obj):
        target_date = self.get_target_date()
        try:
            presensi_on_date = Presensi.objects.filter(
                petugas=obj, 
                timestamp__date=target_date
            ).order_by('-timestamp').first()
            
            if presensi_on_date:
                return AdminPresensiSerializer(presensi_on_date, context=self.context).data
            return None
            
        except Exception:
            return None

class AdminLaporanSerializer(serializers.ModelSerializer):
    petugas_name = serializers.CharField(source='petugas.first_name', read_only=True)
    petugas_email = serializers.EmailField(source='petugas.email', read_only=True)

    class Meta:
        model = Laporan
        fields = [
            'id', 'petugas_name', 'petugas_email', 'timestamp', 
            'latitude', 'longitude', 'location_note', 'note', 'photo', 
            'status', 'priority'
        ]
        read_only_fields = ['status', 'priority']

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
