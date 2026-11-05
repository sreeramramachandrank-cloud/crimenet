# crimes/views.py - FIXED VERSION
from tkinter import Canvas
from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Q, Count, F
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.template.loader import render_to_string
from django.conf import settings
import json
import csv
import qrcode
from io import BytesIO
from PIL import Image
import hashlib
import os
import random
from datetime import datetime, timedelta
import uuid

# Django imports
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.core.files import File
from django import forms

from complaints.models import Complaint

# Import models and forms
from .models import (
    FIR, AIMatch, Witness, Evidence, InvestigationUpdate, 
    CriminalRecord, PoliceStation, CrimeCategory, FIRAuditLog
)
from .forms import (
    FIRForm, WitnessForm, EvidenceForm, InvestigationUpdateForm,
    CriminalRecordForm, BiometricCaptureForm, FIRSearchForm
)

# ==================== PERMISSION HELPERS ====================

def check_officer_permission(user):
    """Check if user is authorized as officer"""
    # Method 1: Check profile role (if using profile system)
    if hasattr(user, 'profile'):
        if hasattr(user.profile, 'role'):
            if user.profile.role in ['OFFICER', 'ADMIN', 'INVESTIGATOR']:
                return True
    
    # Method 2: Check groups
    if user.groups.filter(name__in=['Police Officers', 'Administrators', 'Investigators']).exists():
        return True
    
    # Method 3: Check if superuser
    if user.is_superuser:
        return True
    
    # Method 4: Check if is_staff (admin users)
    if user.is_staff:
        return True
    
    return False

def officer_required(view_func):
    """Decorator to check if user is officer"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not check_officer_permission(request.user):
            messages.error(request, "Access denied. Officer permission required.")
            return redirect('crimes:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

class OfficerRequiredMixin:
    """Mixin for class-based views to check officer permissions"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not check_officer_permission(request.user):
            messages.error(request, "Access denied. Officer permission required.")
            return redirect('crimes:dashboard')
        
        return super().dispatch(request, *args, **kwargs)

# ==================== DASHBOARD VIEWS ====================

@login_required
def dashboard(request):
    """Main dashboard based on user role"""
    user = request.user
    
    if check_officer_permission(user):
        return officer_dashboard(request)
    else:
        return render(request, 'crimes/dashboard_citizen.html')

@login_required
def officer_dashboard(request):
    """Police Officer Dashboard"""
    if not check_officer_permission(request.user):
        messages.error(request, "Access denied")
        return redirect('crimes:dashboard')
    
    # Get officer's FIRs
    registered_firs = FIR.objects.filter(officer_in_charge=request.user).count()
    investigating_firs = FIR.objects.filter(investigating_officer=request.user).count()
    
    # Recent FIRs
    recent_firs = FIR.objects.filter(
        Q(officer_in_charge=request.user) | Q(investigating_officer=request.user)
    ).order_by('-date_registered')[:5]
    
    # Stats
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    weekly_firs = FIR.objects.filter(
        officer_in_charge=request.user,
        date_registered__date__gte=week_ago
    ).count()
    
    pending_verification = FIR.objects.filter(
        officer_in_charge=request.user,
        biometric_status='NOT_CAPTURED'
    ).count()
    
    context = {
        'registered_firs': registered_firs,
        'investigating_firs': investigating_firs,
        'weekly_firs': weekly_firs,
        'pending_verification': pending_verification,
        'recent_firs': recent_firs,
        'dashboard_type': 'officer',
    }
    
    return render(request, 'crimes/dashboard_officer.html', context)

@login_required
def investigator_dashboard(request):
    """Investigator Dashboard"""
    user = request.user
    
    # Check if user is investigator
    is_investigator = False
    if hasattr(user, 'profile') and user.profile.role == 'INVESTIGATOR':
        is_investigator = True
    elif user.groups.filter(name='Investigators').exists():
        is_investigator = True
    elif user.is_superuser:
        is_investigator = True
    
    if not is_investigator:
        messages.error(request, "Access denied. Investigator permission required.")
        return redirect('crimes:dashboard')
    
    # Get investigator stats
    try:
        assigned_firs = FIR.objects.filter(investigating_officer=user).count()
        active_investigations = FIR.objects.filter(
            investigating_officer=user,
            status='INVESTIGATION'
        ).count()
        
        # Recent updates
        recent_updates = InvestigationUpdate.objects.filter(
            updated_by=user
        ).order_by('-update_date')[:5]
        
        # Evidence collected this month
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        evidence_collected = Evidence.objects.filter(
            collected_by=user,
            collected_date__gte=month_start
        ).count()
        
        context = {
            'assigned_firs': assigned_firs,
            'active_investigations': active_investigations,
            'evidence_collected': evidence_collected,
            'recent_updates': recent_updates,
            'dashboard_type': 'investigator',
        }
        
        return render(request, 'crimes/dashboard_investigator.html', context)
        
    except Exception as e:
        print(f"Error in investigator dashboard: {e}")
        context = {
            'assigned_firs': 0,
            'active_investigations': 0,
            'evidence_collected': 0,
            'recent_updates': [],
            'dashboard_type': 'investigator',
        }
        return render(request, 'crimes/dashboard_investigator.html', context)

@login_required
def admin_dashboard(request):
    """Admin Dashboard"""
    user = request.user
    
    # Check if user is admin
    is_admin = False
    if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
        is_admin = True
    elif user.groups.filter(name='Administrators').exists():
        is_admin = True
    elif user.is_superuser:
        is_admin = True
    
    if not is_admin:
        messages.error(request, "Access denied. Admin permission required.")
        return redirect('crimes:dashboard')
    
    # Get admin stats
    try:
        total_firs = FIR.objects.count()
        today_firs = FIR.objects.filter(
            date_registered__date=timezone.now().date()
        ).count()
        
        pending_biometric = FIR.objects.filter(
            biometric_status='NOT_CAPTURED'
        ).count()
        
        criminal_matches = FIR.objects.filter(
            biometric_status='MATCH_FOUND'
        ).count()
        
        # Crime type distribution
        crime_distribution = (
            FIR.objects.values('crime_category__section')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Station-wise stats
        station_stats = (
            PoliceStation.objects.annotate(
                fir_count=Count('fir'),
                today_count=Count('fir', filter=Q(fir__date_registered__date=timezone.now().date()))
            ).order_by('-fir_count')[:10]
        )
        
        context = {
            'total_firs': total_firs,
            'today_firs': today_firs,
            'pending_biometric': pending_biometric,
            'criminal_matches': criminal_matches,
            'crime_distribution': crime_distribution,
            'station_stats': station_stats,
            'dashboard_type': 'admin',
        }
        
        return render(request, 'crimes/dashboard_admin.html', context)
        
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        context = {
            'total_firs': 0,
            'today_firs': 0,
            'pending_biometric': 0,
            'criminal_matches': 0,
            'crime_distribution': [],
            'station_stats': [],
            'dashboard_type': 'admin',
        }
        return render(request, 'crimes/dashboard_admin.html', context)

# ==================== FIR MANAGEMENT VIEWS ====================

class FIRCreateView(LoginRequiredMixin, OfficerRequiredMixin, CreateView):
    """Create new FIR"""
    model = FIR
    form_class = FIRForm
    template_name = 'crimes/fir_create.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        with transaction.atomic():
            form.instance.created_by = self.request.user
            
            # if not form.instance.officer_in_charge:
            #     form.instance.officer_in_charge = self.request.user
            if not hasattr(form.instance, "officer_in_charge") or form.instance.officer_in_charge_id is None:
             form.instance.officer_in_charge = self.request.user

            
            form.instance.status = 'DRAFT'
            
            response = super().form_valid(form)
            
            FIRAuditLog.objects.create(
                fir=form.instance,
                action='CREATED',
                description=f"FIR created by {self.request.user.username}",
                user=self.request.user,
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(
                self.request,
                f"FIR draft created successfully! FIR Number: {form.instance.fir_number}"
            )
            
            return response
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def get_success_url(self):
        return reverse('crimes:fir_biometric', kwargs={'pk': self.object.pk})

@login_required
@officer_required
def fir_biometric(request, pk):
    """Capture biometrics for FIR"""
    fir = get_object_or_404(FIR, pk=pk)
    
    if not (request.user == fir.officer_in_charge or request.user.is_superuser):
        messages.error(request, "You don't have permission to add biometrics to this FIR")
        return redirect('crimes:dashboard')
    
    if request.method == 'POST':
        form = BiometricCaptureForm(request.POST, request.FILES, instance=fir)
        if form.is_valid():
            fir = form.save(commit=False)
            
            if fir.informant_photo:
                fir.biometric_status = 'CAPTURED'
                fir.status = 'REGISTERED'
                fir.date_registered = timezone.now()
            
            fir.save()
            
            FIRAuditLog.objects.create(
                fir=fir,
                action='BIOMETRIC_CAPTURED',
                description=f"Biometrics captured by {request.user.username}",
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, "✅ Biometrics captured successfully!")
            return redirect('crimes:fir_detail', pk=fir.pk)
    else:
        form = BiometricCaptureForm(instance=fir)
    
    context = {
        'fir': fir,
        'form': form,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY if hasattr(settings, 'GOOGLE_MAPS_API_KEY') else '',
    }
    
    return render(request, 'crimes/fir_biometric.html', context)

@login_required
@officer_required
def fir_detail(request, pk):
    """View FIR details"""
    fir = get_object_or_404(FIR, pk=pk)
    
    can_view = False
    if request.user == fir.officer_in_charge:
        can_view = True
    elif request.user == fir.investigating_officer:
        can_view = True
    elif request.user.groups.filter(name='Administrators').exists():
        can_view = True
    elif request.user.is_superuser:
        can_view = True
    elif check_officer_permission(request.user):
        can_view = True
    
    if not can_view:
        messages.error(request, "You don't have permission to view this FIR")
        return redirect('crimes:dashboard')
    
    witnesses = fir.witnesses.all()
    evidences = fir.evidences.all()
    investigation_updates = fir.investigation_updates.all()
    audit_logs = fir.audit_logs.all()[:10]
    
    if not fir.qr_code:
        generate_qr_code(fir)
    
    context = {
        'fir': fir,
        'witnesses': witnesses,
        'evidences': evidences,
        'investigation_updates': investigation_updates,
        'audit_logs': audit_logs,
        'can_edit': request.user == fir.officer_in_charge or request.user.is_superuser,
        'can_investigate': request.user == fir.investigating_officer,
    }
    
    return render(request, 'crimes/fir_detail.html', context)

def generate_qr_code(fir):
    """Generate QR code for FIR"""
    qr_data = f"""
    FIR Number: {fir.fir_number}
    Police Station: {fir.police_station.name}
    Date: {fir.date_registered.strftime('%d-%m-%Y') if fir.date_registered else 'N/A'}
    Status: {fir.get_status_display()}
    """
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    filename = f'qr_fir_{fir.fir_number.replace("/", "_") if fir.fir_number else "unknown"}.png'
    fir.qr_code.save(filename, File(buffer), save=True)
    buffer.close()
    
    return fir.qr_code.url

class FIRListView(LoginRequiredMixin, OfficerRequiredMixin, ListView):
    """List all FIRs with filtering"""
    model = FIR
    template_name = 'crimes/fir_list.html'
    context_object_name = 'firs'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = FIR.objects.all().select_related(
            'police_station', 'crime_category', 'officer_in_charge'
        )
        
        search = self.request.GET.get('search', '')
        status = self.request.GET.get('status', '')
        station = self.request.GET.get('station', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        biometric_status = self.request.GET.get('biometric_status', '')
        
        if search:
            queryset = queryset.filter(
                Q(fir_number__icontains=search) |
                Q(informant_name__icontains=search) |
                Q(informant_mobile__icontains=search) |
                Q(accused_name__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        if station:
            queryset = queryset.filter(police_station__code=station)
        
        if date_from:
            queryset = queryset.filter(date_registered__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(date_registered__date__lte=date_to)
        
        if biometric_status:
            queryset = queryset.filter(biometric_status=biometric_status)
        
        if not self.request.user.is_superuser and not self.request.user.groups.filter(name='Administrators').exists():
            queryset = queryset.filter(
                Q(officer_in_charge=self.request.user) |
                Q(investigating_officer=self.request.user)
            )
        
        return queryset.order_by('-date_registered')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['police_stations'] = PoliceStation.objects.all()
        context['status_choices'] = FIR.STATUS_CHOICES
        context['biometric_status_choices'] = FIR.BIOMETRIC_STATUS
        
        # Calculate statistics
        queryset = self.get_queryset()
        context['investigation_count'] = queryset.filter(status='INVESTIGATION').count()
        context['registered_count'] = queryset.filter(status='REGISTERED').count()
        context['pending_biometric'] = queryset.filter(biometric_status='NOT_CAPTURED').count()
        
        for key in ['search', 'status', 'station', 'date_from', 'date_to', 'biometric_status']:
            context[key] = self.request.GET.get(key, '')
        
        return context

@login_required
@officer_required
def fir_update_status(request, pk):
    """Update FIR status"""
    fir = get_object_or_404(FIR, pk=pk)
    
    if not (request.user == fir.officer_in_charge or request.user.is_superuser):
        messages.error(request, "You don't have permission to update this FIR")
        return redirect('crimes:fir_detail', pk=fir.pk)
    
    if request.method == 'POST':
        old_status = fir.status
        new_status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        
        valid_transitions = {
            'DRAFT': ['REGISTERED'],
            'REGISTERED': ['VERIFIED', 'INVESTIGATION', 'CANCELLED'],
            'VERIFIED': ['INVESTIGATION'],
            'INVESTIGATION': ['CHARGESHEET_FILED', 'COURT', 'CLOSED'],
            'CHARGESHEET_FILED': ['COURT'],
            'COURT': ['CONVICTED', 'ACQUITTED'],
            'CONVICTED': ['CLOSED'],
            'ACQUITTED': ['CLOSED'],
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            messages.error(request, f"Invalid status transition: {old_status} → {new_status}")
            return redirect('crimes:fir_detail', pk=fir.pk)
        
        fir.status = new_status
        
        if new_status == 'VERIFIED' and not fir.date_verified:
            fir.date_verified = timezone.now()
        elif new_status == 'INVESTIGATION' and not fir.io_assigned_date:
            fir.io_assigned_date = timezone.now()
        elif new_status == 'CLOSED' and not fir.date_closed:
            fir.date_closed = timezone.now()
        
        fir.save()
        
        FIRAuditLog.objects.create(
            fir=fir,
            action='STATUS_CHANGED',
            description=f"Status changed from {old_status} to {new_status}. Remarks: {remarks}",
            user=request.user,
            old_value=old_status,
            new_value=new_status,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f"FIR status updated to {fir.get_status_display()}")
        
        return redirect('crimes:fir_detail', pk=fir.pk)
    
    context = {
        'fir': fir,
        'status_choices': FIR.STATUS_CHOICES,
        'current_status': fir.status,
    }
    
    return render(request, 'crimes/fir_update_status.html', context)

@login_required
@officer_required
def assign_investigator(request, pk):
    """Assign investigating officer"""
    fir = get_object_or_404(FIR, pk=pk)
    
    if not (request.user == fir.officer_in_charge or request.user.is_superuser):
        messages.error(request, "You don't have permission to assign investigators")
        return redirect('crimes:fir_detail', pk=fir.pk)
    
    if request.method == 'POST':
        investigator_id = request.POST.get('investigator_id')
        
        try:
            investigator = User.objects.get(
                pk=investigator_id,
                groups__name='Investigators'
            )
            
            old_investigator = fir.investigating_officer
            fir.investigating_officer = investigator
            fir.io_assigned_date = timezone.now()
            
            if fir.status in ['REGISTERED', 'VERIFIED']:
                fir.status = 'INVESTIGATION'
            
            fir.save()
            
            FIRAuditLog.objects.create(
                fir=fir,
                action='INVESTIGATOR_ASSIGNED',
                description=f"Investigating officer assigned: {investigator.username}",
                user=request.user,
                old_value=str(old_investigator) if old_investigator else '',
                new_value=str(investigator),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Investigator {investigator.get_full_name()} assigned to FIR")
            
            return redirect('crimes:fir_detail', pk=fir.pk)
            
        except User.DoesNotExist:
            messages.error(request, "Invalid investigator selected")
    
    try:
        investigator_group = Group.objects.get(name='Investigators')
        investigators = investigator_group.user_set.filter(is_active=True)
    except Group.DoesNotExist:
        investigators = User.objects.none()
    
    context = {
        'fir': fir,
        'investigators': investigators,
    }
    
    return render(request, 'crimes/assign_investigator.html', context)

# ==================== WITNESS MANAGEMENT ====================

@login_required
@officer_required
def add_witness(request, fir_id):
    """Add witness to FIR"""
    fir = get_object_or_404(FIR, pk=fir_id)
    
    if not (request.user == fir.officer_in_charge or 
            request.user == fir.investigating_officer or
            request.user.is_superuser):
        messages.error(request, "You don't have permission to add witnesses to this FIR")
        return redirect('crimes:fir_detail', pk=fir.pk)
    
    if request.method == 'POST':
        form = WitnessForm(request.POST, request.FILES)
        if form.is_valid():
            witness = form.save(commit=False)
            witness.fir = fir
            witness.statement_recorded_by = request.user
            
            if witness.photo:
                witness.photo_hash = generate_image_hash(witness.photo)
            
            witness.save()
            
            fir.witness_count = fir.witnesses.count()
            fir.save(update_fields=['witness_count'])
            
            FIRAuditLog.objects.create(
                fir=fir,
                action='WITNESS_ADDED',
                description=f"Witness added: {witness.name}",
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Witness {witness.name} added successfully")
            return redirect('crimes:fir_detail', pk=fir.pk)
    else:
        form = WitnessForm()
    
    context = {
        'fir': fir,
        'form': form,
    }
    
    return render(request, 'crimes/add_witness.html', context)

def generate_image_hash(image_field):
    """Generate SHA256 hash of uploaded image"""
    try:
        img = Image.open(image_field)
        img = img.convert('L').resize((64, 64), Image.Resampling.LANCZOS)
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        return hashlib.sha256(img_bytes).hexdigest()
    except Exception as e:
        print(f"Error generating image hash: {e}")
        return ''

# ==================== EVIDENCE MANAGEMENT ====================

@login_required
@officer_required
def add_evidence(request, fir_id):
    """Add evidence to FIR"""
    fir = get_object_or_404(FIR, pk=fir_id)
    
    if not (request.user == fir.officer_in_charge or 
            request.user == fir.investigating_officer or
            request.user.is_superuser):
        messages.error(request, "You don't have permission to add evidence to this FIR")
        return redirect('crimes:fir_detail', pk=fir.pk)
    
    if request.method == 'POST':
        form = EvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            evidence = form.save(commit=False)
            evidence.fir = fir
            evidence.collected_by = request.user
            evidence.current_custodian = request.user
            
            if not evidence.evidence_bag_number:
                today = timezone.now().strftime('%Y%m%d')
                count = Evidence.objects.filter(collected_date__date=timezone.now().date()).count() + 1
                evidence.evidence_bag_number = f"EB-{today}-{count:04d}"
            
            evidence.save()
            
            FIRAuditLog.objects.create(
                fir=fir,
                action='EVIDENCE_ADDED',
                description=f"Evidence added: {evidence.description[:50]}...",
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, "Evidence added successfully")
            return redirect('crimes:fir_detail', pk=fir.pk)
    else:
        form = EvidenceForm()
    
    context = {
        'fir': fir,
        'form': form,
    }
    
    return render(request, 'crimes/add_evidence.html', context)

@login_required
@officer_required
def update_evidence_custody(request, evidence_id):
    """Update chain of custody for evidence"""
    evidence = get_object_or_404(Evidence, pk=evidence_id)
    
    if not (request.user == evidence.current_custodian or 
            request.user == evidence.fir.officer_in_charge or
            request.user == evidence.fir.investigating_officer or
            request.user.is_superuser):
        messages.error(request, "You don't have permission to transfer this evidence")
        return redirect('crimes:fir_detail', pk=evidence.fir.pk)
    
    if request.method == 'POST':
        new_custodian_id = request.POST.get('custodian_id')
        reason = request.POST.get('reason', '')
        
        try:
            new_custodian = User.objects.get(pk=new_custodian_id)
            old_custodian = evidence.current_custodian
            
            evidence.current_custodian = new_custodian
            evidence.save()
            
            FIRAuditLog.objects.create(
                fir=evidence.fir,
                action='EVIDENCE_CUSTODY_CHANGED',
                description=f"Evidence custody changed from {old_custodian} to {new_custodian}. Reason: {reason}",
                user=request.user,
                old_value=str(old_custodian),
                new_value=str(new_custodian),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Evidence custody transferred to {new_custodian.get_full_name()}")
            return redirect('crimes:fir_detail', pk=evidence.fir.pk)
            
        except User.DoesNotExist:
            messages.error(request, "Invalid user selected")
    
    available_users = User.objects.filter(
        Q(groups__name='Police Officers') | 
        Q(groups__name='Investigators') |
        Q(is_superuser=True)
    ).distinct()
    
    context = {
        'evidence': evidence,
        'available_users': available_users,
    }
    
    return render(request, 'crimes/update_evidence_custody.html', context)

# ==================== INVESTIGATION UPDATES ====================

@login_required
@officer_required
def add_investigation_update(request, fir_id):
    """Add investigation progress update"""
    fir = get_object_or_404(FIR, pk=fir_id)
    
    if not (request.user == fir.investigating_officer or request.user.is_superuser):
        messages.error(request, "You don't have permission to add investigation updates")
        return redirect('crimes:fir_detail', pk=fir.pk)
    
    if request.method == 'POST':
        form = InvestigationUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            update = form.save(commit=False)
            update.fir = fir
            update.updated_by = request.user
            
            update.save()
            
            FIRAuditLog.objects.create(
                fir=fir,
                action='INVESTIGATION_UPDATE',
                description=f"Investigation update: {update.get_update_type_display()}",
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, "Investigation update added")
            return redirect('crimes:fir_detail', pk=fir.pk)
    else:
        form = InvestigationUpdateForm()
    
    context = {
        'fir': fir,
        'form': form,
    }
    
    return render(request, 'crimes/add_investigation_update.html', context)

# ==================== CRIMINAL DATABASE ====================

class CriminalRecordListView(LoginRequiredMixin, OfficerRequiredMixin, ListView):
    """List criminal records"""
    model = CriminalRecord
    template_name = 'crimes/criminal_list.html'
    context_object_name = 'criminals'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CriminalRecord.objects.all()
        
        search = self.request.GET.get('search', '')
        is_wanted = self.request.GET.get('is_wanted', '')
        is_active = self.request.GET.get('is_active', '')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(alias__icontains=search) |
                Q(aadhaar_number__icontains=search) |
                Q(criminal_id__icontains=search)
            )
        
        if is_wanted == 'true':
            queryset = queryset.filter(is_wanted=True)
        elif is_wanted == 'false':
            queryset = queryset.filter(is_wanted=False)
        
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['is_wanted'] = self.request.GET.get('is_wanted', '')
        context['is_active'] = self.request.GET.get('is_active', '')
        return context

@login_required
@officer_required
def add_criminal_record(request):
    """Add new criminal record"""
    if request.method == 'POST':
        form = CriminalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            criminal = form.save(commit=False)
            criminal.created_by = request.user
            
            if not criminal.criminal_id:
                year = timezone.now().year
                last_criminal = CriminalRecord.objects.filter(
                    criminal_id__startswith=f'CR{year}'
                ).order_by('criminal_id').last()
                
                if last_criminal:
                    last_num = int(last_criminal.criminal_id[-6:])
                    new_num = last_num + 1
                else:
                    new_num = 1
                
                criminal.criminal_id = f'CR{year}{new_num:06d}'
            
            if criminal.front_photo:
                criminal.photo_hash = generate_image_hash(criminal.front_photo)
            
            criminal.save()
            
            messages.success(request, f"Criminal record added: {criminal.criminal_id}")
            return redirect('crimes:criminal_detail', pk=criminal.pk)
    else:
        form = CriminalRecordForm()
    
    return render(request, 'crimes/add_criminal_record.html', {'form': form})

@login_required
@officer_required
def criminal_detail(request, pk):
    """View criminal details"""
    criminal = get_object_or_404(CriminalRecord, pk=pk)
    
    matched_firs = FIR.objects.filter(criminal_match=criminal)
    
    context = {
        'criminal': criminal,
        'matched_firs': matched_firs,
    }
    
    return render(request, 'crimes/criminal_detail.html', context)

@login_required
@officer_required
def search_criminal(request):
    """Search criminal records"""
    query = request.GET.get('q', '')
    
    if query:
        criminals = CriminalRecord.objects.filter(
            Q(name__icontains=query) |
            Q(alias__icontains=query) |
            Q(aadhaar_number__icontains=query) |
            Q(criminal_id__icontains=query) |
            Q(father_name__icontains=query) |
            Q(mother_name__icontains=query) |
            Q(address__icontains=query) |
            Q(distinguishing_marks__icontains=query)
        ).distinct()
    else:
        criminals = CriminalRecord.objects.none()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        results = []
        for criminal in criminals[:10]:
            results.append({
                'id': criminal.id,
                'criminal_id': criminal.criminal_id,
                'name': criminal.name,
                'alias': criminal.alias,
                'photo_url': criminal.front_photo.url if criminal.front_photo else '',
                'is_wanted': criminal.is_wanted,
                'is_active': criminal.is_active,
                'detail_url': reverse('crimes:criminal_detail', args=[criminal.id])
            })
        return JsonResponse({'results': results})
    
    context = {
        'criminals': criminals,
        'query': query,
        'total_results': criminals.count(),
    }
    
    return render(request, 'crimes/search_criminal.html', context)

# ==================== REPORTS ====================

@login_required
@officer_required
def generate_report(request):
    """Generate various reports"""
    report_type = request.GET.get('type', 'daily')
    
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)
    
    if report_type == 'daily':
        data = FIR.objects.filter(date_registered__date=today)
        title = f"Daily Report - {today.strftime('%d-%m-%Y')}"
    elif report_type == 'weekly':
        week_ago = today - timedelta(days=7)
        data = FIR.objects.filter(date_registered__date__gte=week_ago)
        title = f"Weekly Report - {week_ago.strftime('%d-%m-%Y')} to {today.strftime('%d-%m-%Y')}"
    elif report_type == 'monthly':
        data = FIR.objects.filter(date_registered__date__gte=month_start)
        title = f"Monthly Report - {month_start.strftime('%B %Y')}"
    elif report_type == 'yearly':
        data = FIR.objects.filter(date_registered__date__gte=year_start)
        title = f"Yearly Report - {year_start.year}"
    elif report_type == 'station':
        station_id = request.GET.get('station_id')
        if station_id:
            station = get_object_or_404(PoliceStation, pk=station_id)
            data = FIR.objects.filter(police_station=station)
            title = f"Station Report - {station.name}"
        else:
            data = FIR.objects.none()
            title = "Station Report - Please select a station"
    elif report_type == 'category':
        category_id = request.GET.get('category_id')
        if category_id:
            category = get_object_or_404(CrimeCategory, pk=category_id)
            data = FIR.objects.filter(crime_category=category)
            title = f"Crime Category Report - {category.name}"
        else:
            data = FIR.objects.none()
            title = "Category Report - Please select a category"
    else:
        data = FIR.objects.all()
        title = "Comprehensive Report"
    
    data_investigation_count = data.filter(status='INVESTIGATION').count()
    data_registered_count = data.filter(status='REGISTERED').count()
    data_closed_count = data.filter(status__in=['CLOSED', 'CONVICTED', 'ACQUITTED']).count()
    
    total_firs = FIR.objects.count()
    active_investigations = FIR.objects.filter(status='INVESTIGATION').count()
    closed_cases = FIR.objects.filter(status__in=['CLOSED', 'CONVICTED', 'ACQUITTED']).count()
    court_cases = FIR.objects.filter(status='COURT').count()
    
    format = request.GET.get('format', 'html')
    
    if format == 'csv':
        return generate_csv_report(data, title)
    elif format == 'pdf':
        return generate_pdf_report(data, title)
    else:
        context = {
            'data': data,
            'title': title,
            'report_type': report_type,
            'data_investigation_count': data_investigation_count,
            'data_registered_count': data_registered_count,
            'data_closed_count': data_closed_count,
            'stations': PoliceStation.objects.all(),
            'categories': CrimeCategory.objects.all(),
            'total_firs': total_firs,
            'active_investigations': active_investigations,
            'closed_cases': closed_cases,
            'court_cases': court_cases,
        }
        return render(request, 'crimes/report_template.html', context)

def generate_csv_report(data, title):
    """Generate CSV report"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{title.replace(" ", "_")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['FIR Number', 'Police Station', 'Crime Category', 'Informant Name', 
                     'Date Registered', 'Status', 'Officer in Charge'])
    
    for fir in data:
        writer.writerow([
            fir.fir_number,
            fir.police_station.name if fir.police_station else '',
            fir.crime_category.name if fir.crime_category else '',
            fir.informant_name,
            fir.date_registered.strftime('%d-%m-%Y') if fir.date_registered else '',
            fir.get_status_display(),
            fir.officer_in_charge.get_full_name() if fir.officer_in_charge else ''
        ])
    
    return response

def generate_pdf_report(data, title):
    """Generate PDF report (placeholder)"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{title.replace(" ", "_")}.pdf"'
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, title)
        p.drawString(100, 730, f"Total Records: {data.count()}")
        
        y = 700
        for fir in data[:20]:
            p.drawString(100, y, f"{fir.fir_number} - {fir.informant_name}")
            y -= 20
            if y < 100:
                p.showPage()
                y = 750
        
        p.save()
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
    except ImportError:
        response.write(b'PDF generation requires ReportLab library')
    
    return response

# ==================== API ENDPOINTS ====================

@csrf_exempt
@require_POST
def verify_mobile_otp(request):
    """Verify mobile OTP for FIR registration"""
    try:
        data = json.loads(request.body)
        mobile = data.get('mobile')
        otp = data.get('otp')
        
        if not mobile or not otp:
            return JsonResponse({'error': 'Mobile and OTP are required'}, status=400)
        
        cache_key = f'mobile_otp_{mobile}'
        cached_otp = cache.get(cache_key)
        
        if not cached_otp:
            return JsonResponse({'error': 'OTP expired or not generated'}, status=400)
        
        if str(otp) != str(cached_otp):
            return JsonResponse({'error': 'Invalid OTP'}, status=400)
        
        cache.delete(cache_key)
        
        return JsonResponse({
            'success': True,
            'message': 'Mobile verified successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def verify_aadhaar(request):
    """Verify Aadhaar number"""
    try:
        data = json.loads(request.body)
        aadhaar_number = data.get('aadhaar_number')
        
        if not aadhaar_number:
            return JsonResponse({'error': 'Aadhaar number is required'}, status=400)
        
        if not aadhaar_number.isdigit() or len(aadhaar_number) != 12:
            return JsonResponse({'error': 'Aadhaar must be 12 digits'}, status=400)
        
        criminal_exists = CriminalRecord.objects.filter(
            aadhaar_number=aadhaar_number,
            is_active=True
        ).exists()
        
        fir_exists = FIR.objects.filter(
            Q(informant_aadhaar=aadhaar_number) | Q(accused_aadhaar=aadhaar_number)
        ).exists()
        
        response_data = {
            'success': True,
            'aadhaar_number': aadhaar_number,
            'is_valid_format': True,
            'exists_in_criminal_db': criminal_exists,
            'exists_in_fir_records': fir_exists,
            'verification_status': 'VALID' if not criminal_exists else 'WARNING',
            'message': 'Aadhaar verified successfully' if not criminal_exists else 'Aadhaar found in criminal database'
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def check_biometric_match(request):
    """Check biometric match with criminal database (AJAX)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        
        mock_matches = []
        
        criminals = CriminalRecord.objects.filter(is_active=True)[:5]
        
        for criminal in criminals:
            match_probability = random.randint(60, 95)
            if match_probability > 70:
                mock_matches.append({
                    'criminal_id': criminal.criminal_id,
                    'name': criminal.name,
                    'alias': criminal.alias,
                    'match_probability': match_probability,
                    'photo_url': criminal.front_photo.url if criminal.front_photo else '',
                    'details_url': reverse('crimes:criminal_detail', args=[criminal.pk])
                })
        
        return JsonResponse({
            'matches': mock_matches,
            'match_count': len(mock_matches)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_police_station_details(request, station_id):
    """Get police station details"""
    try:
        station = PoliceStation.objects.get(pk=station_id)
        
        return JsonResponse({
            'id': station.id,
            'code': station.code,
            'name': station.name,
            'address': station.address,
            'phone': station.phone,
            'email': station.email,
            'officer_in_charge': station.officer_in_charge,
            'jurisdiction': station.jurisdiction,
            'fir_count': FIR.objects.filter(police_station=station).count(),
            'today_fir_count': FIR.objects.filter(
                police_station=station,
                date_registered__date=timezone.now().date()
            ).count()
        })
        
    except PoliceStation.DoesNotExist:
        return JsonResponse({'error': 'Police station not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ==================== PUBLIC ENDPOINTS ====================

def verify_fir_public(request, uuid):
    """Public FIR verification via UUID"""
    try:
        fir = get_object_or_404(FIR, public_verification_uuid=uuid)
        
        context = {
            'fir': fir,
            'is_verified': True,
            'verification_date': timezone.now(),
            'show_details': True,
        }
        
        FIRAuditLog.objects.create(
            fir=fir,
            action='PUBLIC_VERIFICATION',
            description=f"FIR publicly verified via UUID {uuid}",
            user=None,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return render(request, 'crimes/public_fir_verification.html', context)
        
    except FIR.DoesNotExist:
        return render(request, 'crimes/public_fir_verification.html', {
            'is_verified': False,
            'error': 'FIR not found or verification link is invalid'
        })

# ==================== ERROR HANDLING ====================

def handler403(request, exception=None):
    """Custom 403 Forbidden handler"""
    context = {
        'exception': str(exception) if exception else "Access Denied"
    }
    return render(request, 'crimes/403.html', context, status=403)

def handler404(request, exception=None):
    """Custom 404 Not Found handler"""
    context = {
        'exception': str(exception) if exception else "Page Not Found"
    }
    return render(request, 'crimes/404.html', context, status=404)

def handler500(request):
    """Custom 500 Server Error handler"""
    return render(request, 'crimes/500.html', status=500)

# ==================== HELPER FUNCTIONS ====================

def get_user_role(user):
    """Get user role for display"""
    if hasattr(user, 'profile') and user.profile.role:
        return user.profile.role
    
    if user.groups.filter(name='Administrators').exists():
        return 'ADMIN'
    elif user.groups.filter(name='Investigators').exists():
        return 'INVESTIGATOR'
    elif user.groups.filter(name='Police Officers').exists():
        return 'OFFICER'
    elif user.is_superuser:
        return 'SUPERUSER'
    
    return 'CITIZEN'

def validate_fir_data(data):
    """Validate FIR data before saving"""
    errors = []
    
    required_fields = ['police_station', 'crime_category', 'informant_name']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    mobile = data.get('informant_mobile', '')
    if mobile and not mobile.isdigit():
        errors.append("Mobile number must contain only digits")
    
    email = data.get('informant_email', '')
    if email and '@' not in email:
        errors.append("Invalid email address")
    
    return errors

@login_required
def get_notifications(request):
    """Get notifications for current user (AJAX)"""
    if not request.user.is_authenticated:
        return JsonResponse({'notifications': []})
    
    notifications = []
    
    if check_officer_permission(request.user):
        pending_firs = FIR.objects.filter(
            officer_in_charge=request.user,
            biometric_status='NOT_CAPTURED'
        ).count()
        
        if pending_firs > 0:
            notifications.append({
                'type': 'warning',
                'message': f'{pending_firs} FIR(s) pending biometric verification',
                'url': reverse('crimes:fir_list') + '?biometric_status=NOT_CAPTURED'
            })
    
    new_assignments = FIR.objects.filter(
        investigating_officer=request.user,
        io_assigned_date__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    if new_assignments > 0:
        notifications.append({
            'type': 'info',
            'message': f'{new_assignments} new investigation assignment(s)',
            'url': reverse('crimes:fir_list') + '?status=INVESTIGATION'
        })
    
    return JsonResponse({'notifications': notifications})

from django.shortcuts import render, get_object_or_404, redirect
from .models import CriminalRecord
from .forms import CriminalRecordForm

def edit_criminal_record(request, pk):
    criminal = get_object_or_404(CriminalRecord, pk=pk)

    if request.method == "POST":
        form = CriminalRecordForm(request.POST, instance=criminal)
        if form.is_valid():
            form.save()
            return redirect("crimes:criminal_list")  # ✅ MUST return
    else:
        form = CriminalRecordForm(instance=criminal)

    return render(
        request,
        "crimes/criminal_edit.html",
        {
            "form": form,
            "criminal": criminal,
        },
    )


# ==================== CRIMINAL VIEWS (CBV) ====================

class CriminalListView(ListView):
    model = CriminalRecord
    template_name = 'crimes/criminal_list.html'
    context_object_name = 'criminals'
    paginate_by = 25

class CriminalDetailView(DetailView):
    model = CriminalRecord
    template_name = 'crimes/criminal_detail.html'
    context_object_name = 'criminal'

class CriminalCreateView(CreateView):
    model = CriminalRecord
    template_name = 'crimes/criminal_form.html'
    fields = ['full_name', 'aliases', 'father_name', 'aadhaar', 'date_of_birth', 
              'gender', 'address', 'contact_number', 'email', 'photo', 
              'identifying_marks', 'known_associates', 'remarks', 'status']
    success_url = reverse_lazy('crimes:criminal_list')

class CriminalUpdateView(UpdateView):
    model = CriminalRecord
    template_name = 'crimes/criminal_form.html'
    fields = ['full_name', 'aliases', 'father_name', 'aadhaar', 'date_of_birth', 
              'gender', 'address', 'contact_number', 'email', 'photo', 
              'identifying_marks', 'known_associates', 'remarks', 'status']
    success_url = reverse_lazy('crimes:criminal_list')

class CriminalDeleteView(DeleteView):
    model = CriminalRecord
    template_name = 'crimes/criminal_confirm_delete.html'
    success_url = reverse_lazy('crimes:criminal_list')

# ==================== SEARCH VIEW ====================

@login_required
@officer_required
def fir_search_view(request):
    """Search FIRs with advanced filters"""
    form = FIRSearchForm(request.GET or None)
    results = FIR.objects.none()
    
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query', '')
        search_by = form.cleaned_data.get('search_by', 'fir_number')
        police_station = form.cleaned_data.get('police_station')
        status = form.cleaned_data.get('status')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        results = FIR.objects.all()
        
        if search_query:
            if search_by == 'fir_number':
                results = results.filter(fir_number__icontains=search_query)
            elif search_by == 'informant_name':
                results = results.filter(informant_name__icontains=search_query)
            elif search_by == 'informant_mobile':
                results = results.filter(informant_mobile__icontains=search_query)
            elif search_by == 'accused_name':
                results = results.filter(accused_name__icontains=search_query)
            elif search_by == 'crime_category':
                results = results.filter(crime_category__section__icontains=search_query)
        
        if police_station:
            results = results.filter(police_station=police_station)
        
        if status:
            results = results.filter(status=status)
        
        if start_date:
            results = results.filter(date_registered__date__gte=start_date)
        
        if end_date:
            results = results.filter(date_registered__date__lte=end_date)
        
        if not (request.user.is_superuser or request.user.groups.filter(name='Administrators').exists()):
            results = results.filter(
                Q(officer_in_charge=request.user) |
                Q(investigating_officer=request.user)
            )
        
        results = results.order_by('-date_registered')
    
    total_count = results.count() if results else 0
    
    investigation_count = 0
    registered_count = 0
    
    if results:
        investigation_count = results.filter(status='INVESTIGATION').count()
        registered_count = results.filter(status='REGISTERED').count()
    
    crime_categories = CrimeCategory.objects.all()
    
    context = {
        'form': form,
        'results': results,
        'crime_categories': crime_categories,
        'status_choices': FIR.STATUS_CHOICES,
        'total_count': total_count,
        'investigation_count': investigation_count,
        'registered_count': registered_count,
    }
    
    return render(request, 'crimes/fir/search.html', context)



@login_required
@officer_required
def print_fir(request, pk):
    fir = get_object_or_404(FIR, pk=pk)

    if not (
        request.user == fir.officer_in_charge or
        request.user == fir.investigating_officer or
        request.user.is_superuser
    ):
        messages.error(request, "You don't have permission to print this FIR")
        return redirect('crimes:fir_detail', pk=fir.pk)

    return render(request, 'crimes/print_fir.html', {
        'fir': fir
    })



@login_required
@officer_required
def crime_analytics(request):
    """Crime analytics dashboard"""

    # Basic analytics (safe starter version)
    total_firs = FIR.objects.count()

    by_status = (
        FIR.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    by_category = (
        FIR.objects
        .values('crime_category__section')

        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    by_station = (
        FIR.objects
        .values('police_station__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    context = {
        'total_firs': total_firs,
        'by_status': by_status,
        'by_category': by_category,
        'by_station': by_station,
    }

    return render(request, 'crimes/crime_analytics.html', context)




@login_required
def help_support(request):
    """Help & Support page"""

    context = {
        'support_email': 'support@keralapolice.gov.in',
        'support_phone': '+91-471-1234567',
        'office_hours': '09:00 AM – 05:00 PM (Mon–Fri)',
    }

    return render(request, 'crimes/help_support.html', context)




@login_required
def user_manual(request):
    """User Manual page"""

    context = {
        'system_name': 'Kerala Police CrimeNET',
        'version': '1.0',
        'last_updated': 'January 2026',
    }

    return render(request, 'crimes/user_manual.html', context)





@login_required
def view_fir(request, fir_id):
    fir = FIR.objects.get(id=fir_id)
    return render(request, 'crimes/fir_detail.html', {'fir': fir})




@login_required
def edit_fir(request, pk):
    fir = get_object_or_404(FIR, pk=pk)

    if request.user != fir.officer_in_charge and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this FIR.")
        return redirect('crimes:fir_detail', pk=fir.pk)

    if request.method == 'POST':
        form = FIRForm(request.POST, request.FILES, instance=fir)
        if form.is_valid():
            form.save()
            messages.success(request, "FIR updated successfully.")
            return redirect('crimes:fir_detail', pk=fir.pk)
    else:
        form = FIRForm(instance=fir)

    return render(request, 'crimes/edit_fir.html', {
        'fir': fir,
        'form': form
    })





@login_required
def share_fir(request, pk):
    fir = get_object_or_404(FIR, pk=pk)

    share_url = request.build_absolute_uri(
        reverse('crimes:fir_detail', args=[fir.pk])
    )

    return render(request, 'crimes/share_fir.html', {
        'fir': fir,
        'share_url': share_url
    })






import qrcode
from django.core.files.base import ContentFile
from io import BytesIO

@login_required
def generate_fir_qr(request, pk):
    fir = get_object_or_404(FIR, pk=pk)

    qr = qrcode.make(
        request.build_absolute_uri(
            reverse('crimes:fir_detail', args=[fir.pk])
        )
    )

    buffer = BytesIO()
    qr.save(buffer, format='PNG')

    fir.qr_code.save(
        f'fir_{fir.fir_number}.png',
        ContentFile(buffer.getvalue()),
        save=True
    )

    messages.success(request, "QR Code generated successfully.")
    return redirect('crimes:fir_detail', pk=fir.pk)



@login_required
def delete_fir(request, pk):
    fir = get_object_or_404(FIR, pk=pk)

    if not request.user.is_superuser:
        messages.error(request, "Only administrators can delete FIRs.")
        return redirect('crimes:fir_detail', pk=fir.pk)

    if request.method == 'POST':
        fir.delete()
        messages.success(request, "FIR deleted successfully.")
        return redirect('crimes:fir_list')

    return render(request, 'crimes/confirm_delete_fir.html', {'fir': fir})



import csv
from django.http import HttpResponse
from .models import CriminalRecord

def export_criminals_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="criminal_records.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "ID",
        "Name",
        "Crime Category",
        "Police Station",
        "Status",
    ])

    for c in CriminalRecord.objects.all():
        crime = (
            c.crime_category.section
            if hasattr(c, "crime_category") and c.crime_category
            else "N/A"
        )

        station = (
            c.police_station.name
            if hasattr(c, "police_station") and c.police_station
            else "N/A"
        )

        status = getattr(c, "status", "N/A")

        writer.writerow([
            c.id,
            c.name,
            crime,
            station,
            status,
        ])

    return response




from openpyxl import Workbook
from django.http import HttpResponse
from .models import CriminalRecord

def export_criminals_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Criminal Records"

    # Header row
    ws.append([
        "ID",
        "Name",
        "Crime Category",
        "Police Station",
        "Status",
    ])

    for c in CriminalRecord.objects.all():
        crime = (
            c.crime_category.section
            if hasattr(c, "crime_category") and c.crime_category
            else "N/A"
        )

        station = (
            c.police_station.name
            if hasattr(c, "police_station") and c.police_station
            else "N/A"
        )

        status = getattr(c, "status", "N/A")

        ws.append([
            c.id,
            c.name,
            crime,
            station,
            status,
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="criminal_records.xlsx"'

    wb.save(response)
    return response


from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import CriminalRecord

def export_criminals_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="criminal_records.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 10)

    y = 800
    p.drawString(40, y, "CrimeNet – Criminal Records Report")
    y -= 30

    for c in CriminalRecord.objects.all():
        crime = (
            c.crime_category.section
            if hasattr(c, "crime_category") and c.crime_category
            else "N/A"
        )

        status = getattr(c, "status", "N/A")

        line = f"{c.id} | {c.name} | {crime} | {status}"
        p.drawString(40, y, line)
        y -= 15

        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = 800

    p.save()
    return response



@login_required
def forensic_upload_reports(request):
    if request.user.role != "FORENSIC":
        return HttpResponseForbidden("Access denied")

    return render(request, "crimes/forensic_upload.html")
@login_required
def forensic_biometric_matching(request):
    if request.user.role != "FORENSIC":
        return HttpResponseForbidden("Access denied")

    return render(request, "crimes/forensic_biometric.html")
@login_required
def forensic_evidence_verification(request):
    if request.user.role != "FORENSIC":
        return HttpResponseForbidden("Access denied")

    return render(request, "crimes/forensic_evidence.html")






from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
def authority_required(user):
    return hasattr(user, "role") and user.role in ["ADMIN", "SUPERIOR","JUDGE"]
@login_required
def review_evidence_chain(request):
    if not authority_required(request.user):
        return HttpResponseForbidden("Access denied")

    return render(request, "crimes/review_evidence_chain.html")
@login_required
def view_ai_match_explanations(request):
    if not authority_required(request.user):
        return HttpResponseForbidden("Access denied")

    return render(request, "crimes/ai_match_explanations.html")
@login_required
def authorize_warrants(request):
    if not authority_required(request.user):
        return HttpResponseForbidden("Access denied")

    return render(request, "crimes/authorize_warrants.html")
@login_required
def review_complaint_rejections(request):
    if not authority_required(request.user):
        return HttpResponseForbidden("Access denied")

    return render(request, "crimes/review_complaint_rejections.html")




ROLE_CHOICES = [
    ("OFFICER", "Officer"),
    ("FORENSIC", "Forensic"),
    ("JUDICIAL", "Judicial"),
    ("ADMIN", "Admin"),
    ("JUDGE", "JUDGE"),
]
from django.http import HttpResponseForbidden

def judicial_required(request):
    return hasattr(request.user, "role") and request.user.role == "JUDGE"



from django.utils import timezone
from .models import Warrant, JudicialAuditLog
@login_required
def authorize_warrants(request):
    if not judicial_required(request):
        return HttpResponseForbidden("Access denied")

    warrants = Warrant.objects.filter(status="PENDING")

    if request.method == "POST":
        warrant = Warrant.objects.get(id=request.POST["warrant_id"])
        decision = request.POST["decision"]
        remarks = request.POST.get("remarks", "")

        if warrant.is_final():
            return HttpResponseForbidden("Decision already final")

        warrant.status = decision
        warrant.judicial_remarks = remarks
        warrant.decided_by = request.user
        warrant.decided_at = timezone.now()
        warrant.save()

        JudicialAuditLog.objects.create(
            user=request.user,
            action=f"Warrant {decision}",
            reference=warrant.fir_number,
        )

    return render(request, "crimes/authorize_warrants.html", {
        "warrants": warrants
    })



@login_required
def view_ai_match_explanations(request):
    if not judicial_required(request):
        return HttpResponseForbidden("Access denied")

    matches = AIMatch.objects.all()

    if request.method == "POST":
        match = AIMatch.objects.get(id=request.POST["match_id"])
        match.reviewed = True
        match.save()

        JudicialAuditLog.objects.create(
            user=request.user,
            action="Reviewed AI Match",
            reference=str(match.id),
        )

    return render(request, "crimes/ai_match_explanations.html", {
        "matches": matches
    })




@login_required
def review_complaint_rejections(request):
    if not judicial_required(request):
        return HttpResponseForbidden("Access denied")

    complaints = Complaint.objects.filter(status="REJECTED")

    if request.method == "POST":
        c = Complaint.objects.get(id=request.POST["complaint_id"])
        c.status = request.POST["decision"]
        c.save()

        JudicialAuditLog.objects.create(
            user=request.user,
            action=f"Complaint {c.status}",
            reference=str(c.id),
        )

    return render(request, "crimes/review_complaint_rejections.html", {
        "complaints": complaints
    })




from reportlab.pdfgen import canvas
def warrant_pdf(request, pk):
    warrant = Warrant.objects.get(pk=pk)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=warrant_order.pdf"

    p = canvas.Canvas(response)
    p.drawString(50, 800, "OFFICIAL WARRANT ORDER")
    p.drawString(50, 770, f"FIR: {warrant.fir_number}")
    p.drawString(50, 740, f"Decision: {warrant.status}")
    p.drawString(50, 710, f"Authorized By: {warrant.decided_by}")
    p.drawString(50, 680, f"Remarks: {warrant.judicial_remarks}")

    p.save()
    return response



@login_required
def judicial_audit_logs(request):
    if not judicial_required(request):
        return HttpResponseForbidden()

    logs = JudicialAuditLog.objects.order_by("-timestamp")
    return render(request, "crimes/judicial_audit.html", {"logs": logs})
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

@login_required
def review_evidence_chain(request):
    if not hasattr(request.user, "role") or request.user.role != "JUDGE":
        return HttpResponseForbidden("Access denied")

    return render(request, "crimes/review_evidence_chain.html")
