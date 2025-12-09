# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


# Fungsi untuk menentukan lokasi upload foto
def user_directory_path(instance, filename):
    return 'user_{0}/{1}'.format(instance.email, filename)

from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email harus diisi")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_admin", True)        
        extra_fields.setdefault("is_petugas", False)     

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser harus memiliki is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser harus memiliki is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=user_directory_path, blank=True, null=True)

    is_admin = models.BooleanField(default=False)
    is_petugas = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class Presensi(models.Model):
    petugas = models.ForeignKey(User, on_delete=models.CASCADE, related_name='presensi_set')
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    location_note = models.CharField(max_length=255, help_text="Alamat atau nama lokasi presensi.")
    note = models.TextField(help_text="Catatan harian dari petugas (e.g., 'Presensi Harian').")
    selfie_photo = models.ImageField(upload_to='presensi_photos/')

    # Tambahan: Status Verifikasi Admin
    STATUS_PRESENSI_CHOICES = [
        ('hadir', 'Hadir'), # Default saat kirim
        ('tidak_hadir', 'Tidak Hadir'), # Jika dibatalkan admin
        ('diluar_lokasi', 'Kehadiran Diluar Lokasi'), # Jika lokasi tidak valid
    ]
    
    status_validasi = models.CharField(
        max_length=20, 
        choices=STATUS_PRESENSI_CHOICES, 
        default='hadir'
    )

    class Meta:
        pass

    def __str__(self):
        return f"Presensi {self.petugas.first_name} ({self.status_validasi})"


class Laporan(models.Model):
    petugas = models.ForeignKey(User, on_delete=models.CASCADE, related_name='laporan_set')
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    location_note = models.CharField(max_length=255, help_text="Alamat atau nama lokasi kejadian.")
    note = models.TextField(help_text="Detail laporan insiden/anomaly.")
    photo = models.ImageField(upload_to='laporan_photos/')

    STATUS_CHOICES = [
        ('lapor', 'Lapor'),
        ('ditanggapi', 'Ditanggapi'),
        ('selesai', 'Selesai'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lapor')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    def __str__(self):
        return f"Laporan {self.petugas.first_name} - {self.status}"


class EmergencyAlarm(models.Model):
    CATEGORY_CHOICES = [
        ('maling', 'Maling'),
        ('kebakaran', 'Kebakaran'),
        ('bencana', 'Bencana Alam'),
        ('keributan', 'Keributan/Tawuran'),
        ('medis', 'Gawat Darurat Medis'),
        ('lainnya', 'Lainnya'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('handled', 'Handled/Resolved'),
        ('false_alarm', 'False Alarm'),
    ]

    petugas = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alarms_triggered')
    timestamp = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True, help_text="Deskripsi tambahan jika kategori Lainnya")
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alarms_resolved')

    def __str__(self):
        return f"ALARM: {self.category} by {self.petugas.first_name} at {self.timestamp}"
