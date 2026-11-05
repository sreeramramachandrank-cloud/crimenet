# crimes/models.py
from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
import hashlib
import json
import os
import uuid
from PIL import Image
import io

# ==================== CRIME CATEGORIES ====================
class CrimeCategory(models.Model):
    """IPC Crime Categories"""
    IPC_SECTIONS = [
        ('302', 'IPC 302 - Murder'),
        ('376', 'IPC 376 - Rape'),
        ('395', 'IPC 395 - Dacoity'),
        ('397', 'IPC 397 - Robbery with attempt to cause death'),
        ('399', 'IPC 399 - Preparing to commit dacoity'),
        ('420', 'IPC 420 - Cheating'),
        ('457', 'IPC 457 - Lurking house-trespass or house-breaking by night'),
        ('380', 'IPC 380 - Theft in dwelling house'),
        ('506', 'IPC 506 - Criminal intimidation'),
        ('323', 'IPC 323 - Voluntarily causing hurt'),
        ('324', 'IPC 324 - Voluntarily causing hurt by dangerous weapons'),
        ('498A', 'IPC 498A - Cruelty by husband'),
        ('354', 'IPC 354 - Assault or criminal force to woman with intent to outrage modesty'),
        ('363', 'IPC 363 - Kidnapping'),
        ('511', 'IPC 511 - Attempt to commit offences'),
    ]
    
    section = models.CharField(max_length=20, choices=IPC_SECTIONS, unique=True)
    description = models.TextField()
    punishment = models.CharField(max_length=500)
    is_cognizable = models.BooleanField(default=True)
    is_bailable = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Crime Categories"
        ordering = ['section']
    
    def __str__(self):
        return f"{self.section} - {self.description[:50]}"

# ==================== POLICE STATION ====================
class PoliceStation(models.Model):
    """Police Station Details"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    address = models.TextField()
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default="Kerala")
    phone = models.CharField(max_length=15)
    incharge_name = models.CharField(max_length=200)
    incharge_rank = models.CharField(max_length=100)
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        ordering = ['district', 'name']

# ==================== FIR MODEL ====================
class FIR(models.Model):
    """First Information Report - Main Model"""
    
    # ========== FIR STATUS ==========
    STATUS_CHOICES = [
        ('DRAFT', 'Draft - Under Preparation'),
        ('REGISTERED', 'FIR Registered'),
        ('VERIFIED', 'Verified by SHO'),
        ('INVESTIGATION', 'Under Investigation'),
        ('CHARGESHEET_FILED', 'Chargesheet Filed'),
        ('COURT', 'Case in Court'),
        ('CONVICTED', 'Convicted'),
        ('ACQUITTED', 'Acquitted'),
        ('CLOSED', 'Case Closed'),
        ('CANCELLED', 'FIR Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('HIGHEST', '🔴 Highest Priority (Heinous Crime)'),
        ('HIGH', '🟠 High Priority (Major Crime)'),
        ('MEDIUM', '🟡 Medium Priority'),
        ('LOW', '🟢 Low Priority (Minor Crime)'),
    ]
    
    # ========== UNIQUE IDENTIFIERS ==========
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fir_number = models.CharField(max_length=50, unique=True, editable=False)
    year = models.IntegerField(default=timezone.now().year)
    sequence = models.IntegerField(editable=False)
    
    # ========== POLICE STATION DETAILS ==========
    police_station = models.ForeignKey(PoliceStation, on_delete=models.PROTECT)
    
    # ========== REGISTRATION DETAILS ==========
    date_registered = models.DateTimeField(auto_now_add=True)
    time_registered = models.TimeField(auto_now_add=True)
    officer_in_charge = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='registered_firs',
        limit_choices_to={'groups__name': 'Police Officers'}
    )
    second_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assisting_firs'
    )
    
    # ========== INFORMANT DETAILS ==========
    # Personal Information
    informant_name = models.CharField(max_length=200)
    informant_father_name = models.CharField(max_length=200)
    informant_age = models.PositiveIntegerField(
        validators=[MinValueValidator(12), MaxValueValidator(120)]
    )
    informant_gender = models.CharField(max_length=20, choices=[  # CHANGED TO 20
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('TRANSGENDER', 'Transgender'),
    ])
    informant_occupation = models.CharField(max_length=100)
    
    # Address
    informant_address = models.TextField()
    informant_district = models.CharField(max_length=100)
    informant_state = models.CharField(max_length=100)
    informant_pincode = models.CharField(max_length=6, validators=[
        RegexValidator(regex=r'^\d{6}$', message='Enter valid 6-digit PIN code')  # ADDED r''
    ])
    
    # Contact with Verification
    informant_mobile = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r'^[6-9]\d{9}$', message='Enter valid Indian mobile number')]  # ADDED r''
    )
    mobile_verified = models.BooleanField(default=False)
    mobile_otp = models.CharField(max_length=6, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    
    informant_email = models.EmailField(blank=True)
    
    # Identification Documents
    informant_aadhaar = models.CharField(
        max_length=12,
        blank=True,
        validators=[RegexValidator(regex=r'^\d{12}$', message='Enter 12-digit Aadhaar number')]  # ADDED r''
    )
    aadhaar_verified = models.BooleanField(default=False)
    
    informant_voter_id = models.CharField(max_length=20, blank=True)
    informant_pan = models.CharField(max_length=10, blank=True)
    informant_driving_license = models.CharField(max_length=30, blank=True)
    
    # Relation to Case
    relation_to_case = models.CharField(max_length=100, choices=[
        ('VICTIM', 'Victim'),
        ('WITNESS', 'Eye Witness'),
        ('COMPLAINANT', 'Complainant'),
        ('GUARDIAN', 'Guardian of Victim'),
        ('PUBLIC', 'Member of Public'),
        ('POLICE', 'Police Official'),
    ])
    
    # ========== BIOMETRIC DATA ==========
    BIOMETRIC_STATUS = [
        ('NOT_CAPTURED', 'Not Captured'),
        ('CAPTURED', 'Captured'),
        ('VERIFIED', 'Verified'),
        ('MATCH_FOUND', 'Match in Criminal Database'),
        ('SUSPICIOUS', 'Suspicious - Needs Review'),
    ]
    
    biometric_status = models.CharField(
        max_length=20,
        choices=BIOMETRIC_STATUS,
        default='NOT_CAPTURED'
    )
    
    # Photos
    informant_photo = models.ImageField(
        upload_to='fir/informant_photos/%Y/%m/%d/',
        verbose_name="Passport Size Photo (2x2 inch)"
    )
    photo_hash = models.CharField(max_length=64, blank=True, editable=False)
    
    # Thumb Impression (Right Thumb)
    thumb_impression = models.ImageField(
        upload_to='fir/thumb_impressions/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Right Thumb Impression (Scanned)"
    )
    thumb_hash = models.CharField(max_length=64, blank=True, editable=False)
    
    # Digital Signature (Canvas)
    digital_signature = models.TextField(blank=True)
    
    # Criminal Database Match
    criminal_match = models.ForeignKey(
        'CriminalRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_firs'
    )
    match_confidence = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Match Percentage"
    )
    
    # ========== INCIDENT DETAILS ==========
    incident_date = models.DateField()
    incident_time = models.TimeField()
    
    # Location
    incident_location = models.TextField(verbose_name="Exact Location of Incident")
    incident_landmark = models.CharField(max_length=200, blank=True)
    incident_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    incident_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Crime Details
    crime_category = models.ForeignKey(CrimeCategory, on_delete=models.PROTECT)
    other_ipc_sections = models.CharField(max_length=500, blank=True, verbose_name="Other IPC Sections")
    local_act = models.CharField(max_length=200, blank=True, verbose_name="Special/Local Act if any")
    
    # Narrative
    incident_description = models.TextField(verbose_name="Detailed Description of Incident")
    sequence_of_events = models.TextField(verbose_name="Chronological Sequence of Events")
    
    # Delay in Reporting
    delay_in_reporting = models.CharField(max_length=100, choices=[
        ('IMMEDIATE', 'Immediate (Within 24 hours)'),
        ('WITHIN_3_DAYS', 'Within 3 days'),
        ('WITHIN_WEEK', 'Within a week'),
        ('BEYOND_WEEK', 'Beyond a week'),
        ('MONTH_PLUS', 'More than a month'),
    ])
    delay_reason = models.TextField(blank=True, verbose_name="Reason for Delay")
    
    # ========== ACCUSED DETAILS ==========
    accused_name = models.CharField(max_length=200, blank=True)
    accused_father_name = models.CharField(max_length=200, blank=True)
    accused_age = models.PositiveIntegerField(null=True, blank=True)
    accused_gender = models.CharField(max_length=20, blank=True, choices=[  # CHANGED TO 20
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('TRANSGENDER', 'Transgender'),
    ])
    accused_address = models.TextField(blank=True)
    accused_occupation = models.CharField(max_length=100, blank=True)
    
    # Accused Identification
    accused_aadhaar = models.CharField(max_length=12, blank=True)
    accused_mobile = models.CharField(max_length=10, blank=True)
    
    # Accused Biometric
    accused_photo = models.ImageField(
        upload_to='fir/accused_photos/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Accused Photo if available"
    )
    accused_photo_hash = models.CharField(max_length=64, blank=True, editable=False)
    
    # ========== VICTIM DETAILS (If different from informant) ==========
    victim_name = models.CharField(max_length=200, blank=True)
    victim_age = models.PositiveIntegerField(null=True, blank=True)
    victim_gender = models.CharField(max_length=20, blank=True, choices=[  # CHANGED TO 20
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ])
    victim_address = models.TextField(blank=True)
    victim_condition = models.CharField(max_length=100, blank=True, verbose_name="Condition of Victim")
    
    # ========== PROPERTY DETAILS ==========
    property_involved = models.BooleanField(default=False, verbose_name="Property Stolen/Damaged?")
    property_description = models.TextField(blank=True, verbose_name="Description of Property")
    property_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Estimated Value (₹)"
    )
    
    # ========== WITNESS DETAILS ==========
    witness_count = models.PositiveIntegerField(default=0)
    witness_details = models.TextField(blank=True, verbose_name="Witness Names & Addresses")
    
    # ========== EVIDENCE DETAILS ==========
    evidence_available = models.TextField(blank=True, verbose_name="Initial Evidence Available")
    
    # ========== SYSTEM FIELDS ==========
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='DRAFT')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Special Case Flags
    is_sensitive = models.BooleanField(default=False, verbose_name="Sensitive Case")
    is_cyber_crime = models.BooleanField(default=False, verbose_name="Cyber Crime Case")
    is_women_related = models.BooleanField(default=False, verbose_name="Women Related Crime")
    is_sc_st = models.BooleanField(default=False, verbose_name="SC/ST Act Case")
    is_child_victim = models.BooleanField(default=False, verbose_name="Child Victim Involved")
    
    # Investigation Team
    investigating_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investigating_firs'
    )
    io_assigned_date = models.DateTimeField(null=True, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_firs'
    )
    
    # QR Code
    qr_code = models.ImageField(upload_to='fir_qr_codes/', blank=True, null=True)
    
    class Meta:
        verbose_name = "First Information Report"
        verbose_name_plural = "First Information Reports"
        ordering = ['-date_registered']
        indexes = [
            models.Index(fields=['fir_number']),
            models.Index(fields=['informant_aadhaar']),
            models.Index(fields=['status']),
            models.Index(fields=['police_station']),
            models.Index(fields=['crime_category']),
        ]
    
    def __str__(self):
        return f"{self.fir_number} - {self.crime_category.section} - {self.informant_name}"
    
    def save(self, *args, **kwargs):
        # Generate FIR number
        if not self.fir_number:
            self.year = timezone.now().year
            last_fir = FIR.objects.filter(
                police_station=self.police_station,
                year=self.year
            ).order_by('-sequence').first()
            
            self.sequence = (last_fir.sequence + 1) if last_fir else 1
            self.fir_number = f"{self.police_station.code}/{self.year}/{self.sequence:04d}"
        
        # Generate photo hash
        if self.informant_photo and not self.photo_hash:
            self.photo_hash = self.generate_image_hash(self.informant_photo)
        
        if self.accused_photo and not self.accused_photo_hash:
            self.accused_photo_hash = self.generate_image_hash(self.accused_photo)
        
        if self.thumb_impression and not self.thumb_hash:
            self.thumb_hash = self.generate_image_hash(self.thumb_impression)
        
        # Set investigating officer if not set
        if self.status == 'INVESTIGATION' and not self.investigating_officer:
            self.investigating_officer = self.officer_in_charge
            self.io_assigned_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_image_hash(self, image_field):
        """Generate SHA256 hash of image for comparison"""
        try:
            with Image.open(image_field) as img:
                # Convert to grayscale and resize for consistent hashing
                img = img.convert('L').resize((64, 64), Image.Resampling.LANCZOS)
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                return hashlib.sha256(img_bytes).hexdigest()
        except Exception:
            return ''
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('crimes:view_fir', kwargs={'fir_id': self.id})
    
    def check_biometric_match(self):
        """Check if informant matches any criminal record"""
        from .utils import compare_biometrics
        
        if not self.photo_hash:
            return None
        
        # Compare with criminal database
        matches = compare_biometrics(self.photo_hash, self.thumb_hash)
        if matches:
            self.biometric_status = 'MATCH_FOUND'
            self.criminal_match = matches[0]['criminal']
            self.match_confidence = matches[0]['confidence']
            self.save()
        else:
            self.biometric_status = 'VERIFIED'
            self.save()
        
        return matches

# ==================== SIMPLIFIED CRIMINAL RECORD ====================
class CriminalRecord(models.Model):
    """Criminal Database"""
    criminal_id = models.CharField(max_length=50, unique=True)
    
    # Personal Details
    name = models.CharField(max_length=200)
    alias = models.CharField(max_length=200, blank=True)
    father_name = models.CharField(max_length=200)
    
    # Identification
    aadhaar_number = models.CharField(max_length=12, blank=True, unique=True)
    
    # Biometric Hashes
    photo_hash = models.CharField(max_length=64, blank=True)
    fingerprint_hash = models.CharField(max_length=64, blank=True)
    
    # Physical Description
    distinguishing_marks = models.TextField(blank=True)
    
    # Address
    permanent_address = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name="Active Criminal")
    is_wanted = models.BooleanField(default=False, verbose_name="Currently Wanted")
    
    # Photos
    front_photo = models.ImageField(upload_to='criminals/front/', blank=True, null=True)
    
    # System
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    gender = models.CharField(max_length=20, blank=True, choices=[
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('TRANSGENDER', 'Transgender'),
    ])
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Criminal Records"
    
    def __str__(self):
        return f"{self.criminal_id} - {self.name}"

# ==================== SIMPLIFIED WITNESS ====================
class Witness(models.Model):
    """Witness Details"""
    fir = models.ForeignKey(FIR, on_delete=models.CASCADE, related_name='witnesses')
    
    # Personal Details
    name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200, blank=True)  # ADD THIS
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20, choices=[  # ADD THIS
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
    ], blank=True)
    occupation = models.CharField(max_length=100, blank=True)  # ADD THIS
    
    # Contact
    address = models.TextField()
    mobile = models.CharField(max_length=10, blank=True)
    email = models.EmailField(blank=True)  # ADD THIS
    
    # Identification
    aadhaar_number = models.CharField(max_length=12, blank=True)  # ADD THIS
    
    # Witness Details
    statement = models.TextField(verbose_name="Witness Statement")
    relation_to_case = models.TextField(blank=True, verbose_name="Relation to Case")  # ADD THIS
    
    # Protection
    requires_protection = models.BooleanField(default=False)  # ADD THIS
    protection_details = models.TextField(blank=True)  # ADD THIS
    
    # Photo
    photo = models.ImageField(upload_to='witness_photos/%Y/%m/%d/', blank=True, null=True)  # ADD THIS
    
    # System
    statement_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    statement_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Witnesses"
    
    def __str__(self):
        return f"{self.name} - Witness for FIR {self.fir.fir_number}"
# ==================== SIMPLIFIED EVIDENCE ====================
class Evidence(models.Model):
    """Evidence Collected"""
    EVIDENCE_TYPES = [
        ('WEAPON', 'Weapon'),
        ('DOCUMENT', 'Document'),
        ('PHOTO', 'Photograph'),
        ('VIDEO', 'Video Recording'),
        ('AUDIO', 'Audio Recording'),
        ('CLOTHING', 'Clothing'),
        ('OTHER', 'Other'),
    ]
    
    fir = models.ForeignKey(FIR, on_delete=models.CASCADE, related_name='evidences')
    
    # Evidence Details
    evidence_type = models.CharField(max_length=20, choices=EVIDENCE_TYPES)
    description = models.TextField()
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='collected_evidence'
    )
    collected_date = models.DateTimeField(default=timezone.now)
    
    # Storage
    evidence_bag_number = models.CharField(max_length=50, blank=True)
    
    # Files
    evidence_file = models.FileField(upload_to='evidence/%Y/%m/%d/', blank=True, null=True)
    
    # Status
    sent_to_fsl = models.BooleanField(default=False, verbose_name="Sent to Forensic Lab")
    
    # System
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Evidence"
        ordering = ['-collected_date']
    
    def __str__(self):
        return f"Evidence for FIR {self.fir.fir_number}"

# ==================== SIMPLIFIED INVESTIGATION UPDATE ====================
class InvestigationUpdate(models.Model):
    """Investigation Progress Updates"""
    UPDATE_TYPES = [
        ('SITE_VISIT', 'Crime Scene Visit'),
        ('WITNESS_STATEMENT', 'Witness Statement Recorded'),
        ('EVIDENCE_COLLECTED', 'Evidence Collected'),
        ('SUSPECT_IDENTIFIED', 'Suspect Identified'),
        ('OTHER', 'Other Update'),
    ]
    
    fir = models.ForeignKey(FIR, on_delete=models.CASCADE, related_name='investigation_updates')
    
    # Update Details
    update_type = models.CharField(max_length=50, choices=UPDATE_TYPES)
    description = models.TextField()
    
    # System
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    update_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-update_date']
    
    def __str__(self):
        return f"Update for FIR {self.fir.fir_number}"

# ==================== SIMPLIFIED AUDIT LOG ====================
class FIRAuditLog(models.Model):
    """Audit Log for FIR Changes"""
    ACTION_CHOICES = [
        ('CREATED', 'FIR Created'),
        ('UPDATED', 'FIR Updated'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('BIOMETRIC_CAPTURED', 'Biometric Captured'),
    ]
    
    fir = models.ForeignKey(FIR, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # User who performed action
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    # System
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.fir.fir_number} - {self.action}"
    






class Warrant(models.Model):
     
    fir_number = models.CharField(max_length=50)
    purpose = models.CharField(max_length=200)
    requested_by = models.CharField(max_length=100)
    status = models.CharField(
         max_length=20,
         choices=[
            ("PENDING", "Pending"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
        ],
        default="PENDING",
    )
    judicial_remarks = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    def is_final(self):
        return self.status in ["APPROVED", "REJECTED"]



from django.db import models
from django.conf import settings

class AIMatch(models.Model):
    BIOMETRIC_CHOICES = [
        ("FINGERPRINT", "Fingerprint"),
        ("DNA", "DNA"),
    ]

    biometric_type = models.CharField(
        max_length=50,
        choices=BIOMETRIC_CHOICES
    )
    confidence = models.FloatField(
        help_text="AI confidence score (0–100)"
    )
    explanation = models.TextField(
        help_text="AI-generated explanation for the match"
    )
    reviewed = models.BooleanField(
        default=False,
        help_text="Reviewed by judicial authority"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.biometric_type} – {self.confidence}%"




class JudicialAuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    action = models.CharField(
        max_length=200,
        help_text="Action performed by judicial authority"
    )
    reference = models.CharField(
        max_length=100,
        help_text="Related FIR / Warrant / Evidence reference"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user} | {self.action} | {self.timestamp:%d-%m-%Y %H:%M}"




def save(self, *args, **kwargs):
    if self.pk:
        old = Warrant.objects.get(pk=self.pk)
        if old.is_final():
            raise ValueError("Final judicial decisions cannot be modified")
    super().save(*args, **kwargs)
