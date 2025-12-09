from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth import logout # Import Logout
from .models import User, Presensi, Laporan, EmergencyAlarm
from .serializers import PetugasStatusPresensiSerializer 

# --- VIEW KHUSUS LOGOUT (GET Support) ---
def logout_view(request):
    logout(request)
    return redirect('login')

# Mixin untuk memastikan hanya Admin yang bisa akses
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class DashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        context['total_petugas'] = User.objects.filter(is_petugas=True).count()
        
        context['hadir_today'] = Presensi.objects.filter(
            timestamp__date=today, 
            status_validasi='hadir'
        ).values('petugas').distinct().count()
        
        context['belum_hadir'] = context['total_petugas'] - context['hadir_today']
        context['laporan_baru'] = Laporan.objects.filter(timestamp__date=today).count()
        context['today'] = today

        context['recent_presensi'] = Presensi.objects.select_related('petugas').order_by('-timestamp')[:5]
        context['open_laporan'] = Laporan.objects.select_related('petugas').filter(status='lapor').order_by('-timestamp')[:5]

        return context

# --- VIEW BARU: DAFTAR PETUGAS ---
class WebPetugasListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'core/petugas_list.html'
    context_object_name = 'petugas_list'
    paginate_by = 20

    def get_queryset(self):
        return User.objects.filter(is_petugas=True).order_by('first_name')

# --- VIEW BARU: REKAP HARIAN (Belum Hadir) ---
class WebRekapHarianView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'core/rekap_harian.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ambil tanggal dari filter atau hari ini
        date_str = self.request.GET.get('date')
        if date_str:
            from django.utils.dateparse import parse_date
            target_date = parse_date(date_str) or timezone.localdate()
        else:
            target_date = timezone.localdate()

        petugas_queryset = User.objects.filter(is_petugas=True).order_by('first_name')
        
        # Gunakan Serializer yang sudah kita buat untuk API agar logicnya konsisten
        serializer = PetugasStatusPresensiSerializer(
            petugas_queryset, 
            many=True, 
            context={'target_date': target_date}
        )
        
        context['data_rekap'] = serializer.data
        context['target_date'] = target_date
        context['selected_date'] = date_str
        return context


class WebPresensiListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Presensi
    template_name = 'core/presensi_list.html'
    context_object_name = 'presensi_list'
    paginate_by = 20

    def get_queryset(self):
        queryset = Presensi.objects.select_related('petugas').order_by('-timestamp')
        
        date_str = self.request.GET.get('date')
        if date_str:
            queryset = queryset.filter(timestamp__date=date_str)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_date'] = self.request.GET.get('date', '')
        return context

class WebPresensiDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Presensi
    template_name = 'core/presensi_detail.html'
    context_object_name = 'presensi'

    def post(self, request, *args, **kwargs):
        presensi = self.get_object()
        new_status = request.POST.get('status_validasi')
        
        if new_status in ['hadir', 'tidak_hadir', 'diluar_lokasi']:
            presensi.status_validasi = new_status
            presensi.save()
            messages.success(request, f"Status validasi presensi berhasil diubah menjadi {new_status.replace('_', ' ').title()}")
        
        return redirect('web-presensi-detail', pk=presensi.id)

class WebLaporanListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Laporan
    template_name = 'core/laporan_list.html'
    context_object_name = 'laporan_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = Laporan.objects.select_related('petugas').order_by('-timestamp')
        
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # UPDATE: Tambahkan Filter Tanggal
        date_str = self.request.GET.get('date')
        if date_str:
            queryset = queryset.filter(timestamp__date=date_str)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'all')
        context['selected_date'] = self.request.GET.get('date', '')
        return context

class WebLaporanDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = Laporan
    template_name = 'core/laporan_detail.html'
    context_object_name = 'laporan'

    def post(self, request, *args, **kwargs):
        laporan = self.get_object()
        new_status = request.POST.get('status')
        
        if new_status in ['lapor', 'ditanggapi', 'selesai']:
            laporan.status = new_status
            laporan.save()
            messages.success(request, f"Status laporan berhasil diubah menjadi {new_status.upper()}")
        
        return redirect('web-laporan-detail', pk=laporan.id)

class WebAlarmListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = EmergencyAlarm
    template_name = 'core/alarm_list.html'
    context_object_name = 'alarm_list'
    paginate_by = 15

    def get_queryset(self):
        queryset = EmergencyAlarm.objects.select_related('petugas').order_by('-timestamp')
        
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        date_str = self.request.GET.get('date')
        if date_str:
            queryset = queryset.filter(timestamp__date=date_str)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'all')
        context['selected_date'] = self.request.GET.get('date', '')
        return context

class WebAlarmDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = EmergencyAlarm
    template_name = 'core/alarm_detail.html'
    context_object_name = 'alarm'

    def post(self, request, *args, **kwargs):
        alarm = self.get_object()
        new_status = request.POST.get('status')
        
        if new_status in ['active', 'handled', 'false_alarm']:
            alarm.status = new_status
            if new_status != 'active':
                alarm.resolved_at = timezone.now()
                alarm.resolved_by = request.user
            alarm.save()
            messages.success(request, f"Status alarm berhasil diubah menjadi {new_status.upper()}")
        
        return redirect('web-alarm-detail', pk=alarm.id)
