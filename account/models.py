from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import os
import uuid
from django.core.validators import FileExtensionValidator, RegexValidator
from django.core.exceptions import ValidationError
import hashlib
import jdatetime
from core.abstract_models import BaseModel
from core.utils import upload_to_dynamic


class CustomUserManager(BaseUserManager):
    """Custom manager for username-based authentication"""
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError(_("The Username field must be set"))
        if email:
            email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser, BaseModel):
    """
    Unified User model for both regular users and teachers.
    Role-based system similar to django-project.
    """
    
    # Add name field as alias for username
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Display name"),
        help_text=_("User display name (default: username)")
    )
    
    ROLE_CHOICES = [
        ('user', _('User')),
        ('teacher', _('Teacher')),
        ('admin', _('Admin')),
    ]
    
    GENDER_CHOICES = [
        ('male', _('Male')),
        ('female', _('Female')),
        ('custom', _('Custom')),
        ('prefer_not_to_say', _('Prefer not to say')),
    ]
    
    # Role System
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name=_("User role"),
        help_text=_("User: Regular user, Teacher: Teacher, Admin: Administrator")
    )
    
    # Override email to make it optional
    email = models.EmailField(
        verbose_name=_('email address'),
        blank=True,
        null=True,
        unique=False  # Allow multiple users with no email
    )
    
    # Contact Information
    phone = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Phone number")
    )
    phone_verified_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Phone verified at"))
    email_verified_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Email verified at"))
    
    # Profile Information
    profile_photo_path = models.ImageField(
        upload_to=upload_to_dynamic,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])],
        null=True,
        blank=True,
        verbose_name=_("Profile photo")
    )
    
    # Avatar Template Selection
    selected_avatar = models.ForeignKey(
        'AvatarTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Selected avatar"),
        help_text=_("Avatar template selected by user")
    )
    bio = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Bio")
    )
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Gender")
    )
    birth_date = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name=_("Birth date"),
        help_text=_("Birth date in Jalali calendar format (YYYY-MM-DD), e.g., 1403-05-24"),
        validators=[
            RegexValidator(
                regex=r'^\d{4}-\d{2}-\d{2}$',
                message=_("Birth date must be in YYYY-MM-DD format (Jalali calendar)"),
                code='invalid_jalali_date'
            )
        ]
    )
    
    # Teacher-specific fields (only used when role='teacher')
    is_teacher_verified = models.BooleanField(
        default=False,
        verbose_name=_("Teacher verified"),
        help_text=_("Whether this teacher is verified by admin")
    )
    teacher_verification_requested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Teacher verification requested at")
    )
    
    # Commission Configuration (only for teachers)
    commission_rate_override = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Special commission rate"),
        help_text=_("Special commission rate for this teacher (if empty, default rate is used). Number between 0 and 100")
    )
    
    # ========== Teacher Profile Fields ==========
    # Academic Information
    qualifications = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Educational qualifications"),
        help_text=_("Degrees, certifications, and professional qualifications")
    )
    
    # Teaching Information
    languages_taught = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("Languages taught"),
        help_text=_("Languages that can be taught (comma-separated or JSON)")
    )
    
    specialization = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("Specialization"),
        help_text=_("Area of specialization or expertise")
    )
    
    resume_summary = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Resume summary"),
        help_text=_("Brief summary of professional experience and background")
    )
    
    # Introduction & Media
    introduction_video = models.FileField(
        upload_to=upload_to_dynamic,
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'webm', 'flv', 'mkv', '3gp', 'm4v', 'ogv'])],
        null=True,
        blank=True,
        verbose_name=_("Introduction video"),
        help_text=_("Video file for teacher introduction (MP4, AVI, MOV, WebM, FLV, MKV, 3GP, M4V, OGV)")
    )
    
    # Pricing Information
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Hourly rate"),
        help_text=_("Suggested hourly teaching rate in default currency")
    )
    
    # Availability
    available_times = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Available times"),
        help_text=_("JSON object with available teaching times")
    )
    
    experience_years = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Years of experience"),
        help_text=_("Number of years of teaching experience")
    )
    
    # Device & Notifications
    push_token = models.TextField(
        null=True,
        blank=True,
        help_text=_("Push notification token")
    )
    
    # Presence tracking
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last seen"),
        help_text=_("Last online time")
    )
    is_online = models.BooleanField(
        default=False,
        verbose_name=_("Is online"),
        help_text=_("Online status")
    )
    
    # Use username as USERNAME_FIELD instead of phone
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]
    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_teacher_verified']),
        ]

    @property
    def local_phone(self):
        """Convert phone to local format"""
        if self.phone and self.phone.startswith('+98'):
            return '0' + self.phone[3:]
        return self.phone

    @property
    def is_teacher(self):
        """Check if user is a teacher"""
        return self.role == 'teacher'
    
    @property
    def is_verified_teacher(self):
        """Check if user is a verified teacher"""
        return self.role == 'teacher' and self.is_teacher_verified
    
    def __str__(self):
        return f"{self.username}"


class OTP(BaseModel):
    """
    One-Time Password model for authentication.
    Supports phone and email verification.
    """
    PURPOSE_CHOICES = [
        ('registration', _('Registration')),
        ('phone_verification', _('Phone Verification')),
        ('email_verification', _('Email Verification')),
        ('password_reset', _('Password Reset')),
        ('login', _('Login')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otp_codes',
        null=True,
        blank=True,
        verbose_name=_("User")
    )
    code = models.CharField(
        max_length=100,
        verbose_name=_("Hashed code"),
        help_text=_("Hashed OTP code")
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Phone number")
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_("Email")
    )
    expires_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Expires at")
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name=_("Is used")
    )
    purpose = models.CharField(
        max_length=50,
        choices=PURPOSE_CHOICES,
        default='login',
        verbose_name=_("Purpose")
    )

    class Meta:
        db_table = 'otp_codes'
        verbose_name = _("OTP Code")
        verbose_name_plural = _("OTP Codes")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used', 'expires_at']),
            models.Index(fields=['phone', 'code']),
            models.Index(fields=['email', 'code']),
        ]

    def __str__(self):
        if self.user:
            return f"OTP for {self.user.username} - {self.purpose}"
        return f"OTP for {self.phone or self.email} - {self.purpose}"


class VerificationToken(BaseModel):
    """
    Temporary verification token for completing registration
    """
    token = models.CharField(max_length=150, unique=True, verbose_name=_("Token"))
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("Phone number"))
    email = models.EmailField(null=True, blank=True, verbose_name=_("Email"))
    expires_at = models.DateTimeField(verbose_name=_("Expires at"))
    is_used = models.BooleanField(default=False, verbose_name=_("Is used"))
    
    class Meta:
        db_table = 'verification_tokens'
        verbose_name = _("Verification Token")
        verbose_name_plural = _("Verification Tokens")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token for {self.phone or self.email}"


class AvatarTemplate(BaseModel):
    """
    Avatar template images that users can choose as their profile photo
    """
    image = models.ImageField(
        upload_to=upload_to_dynamic,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        verbose_name=_("Avatar image")
    )
    
    class Meta:
        db_table = 'avatar_templates'
        verbose_name = _("Avatar Template")
        verbose_name_plural = _("Avatar Templates")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Avatar {self.id}"


class ParentProfile(BaseModel):
    """
    والدین می‌توانند با student_id + parent_password وارد شوند
    هر دانش‌آموز می‌تواند چند والد داشته باشد
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='parents',
        verbose_name=_("Student")
    )
    parent_name = models.CharField(
        max_length=200,
        verbose_name=_("Parent full name"),
        help_text=_("نام کامل والد")
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Phone number")
    )
    email = models.EmailField(
        null=True,
        blank=True,
        verbose_name=_("Email")
    )
    # Hashed password for parent login
    parent_password_hash = models.CharField(
        max_length=255,
        verbose_name=_("Parent password (hashed)"),
        help_text=_("Hashed password for parent portal login")
    )
    
    # Parent access permissions
    can_view_class_history = models.BooleanField(
        default=True,
        verbose_name=_("Can view class history"),
        help_text=_("آیا والد می‌تواند تاریخچه کلاس‌ها را مشاهده کند؟")
    )
    can_view_payments = models.BooleanField(
        default=True,
        verbose_name=_("Can view payments"),
        help_text=_("آیا والد می‌تواند پرداخت‌ها را مشاهده کند؟")
    )
    can_select_teacher = models.BooleanField(
        default=False,
        verbose_name=_("Can select teacher"),
        help_text=_("آیا والد می‌تواند معلم برای کودک انتخاب کند؟")
    )
    can_set_usage_time = models.BooleanField(
        default=True,
        verbose_name=_("Can set app usage time"),
        help_text=_("آیا والد می‌تواند محدودیت زمان استفاده اپلیکیشن را تنظیم کند؟")
    )
    
    # Usage time limits
    daily_usage_limit_minutes = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Daily usage limit (minutes)"),
        help_text=_("حداکثر دقایق استفاده روزانه از اپلیکیشن")
    )
    allowed_start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Allowed start time"),
        help_text=_("ساعت شروع مجاز استفاده (مثال: 08:00)")
    )
    allowed_end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_("Allowed end time"),
        help_text=_("ساعت پایان مجاز استفاده (مثال: 22:00)")
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is active"),
        help_text=_("آیا دسترسی والد فعال است؟")
    )
    
    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last login at"),
        help_text=_("آخرین بار ورود والد")
    )
    
    class Meta:
        db_table = 'parent_profiles'
        verbose_name = _("Parent Profile")
        verbose_name_plural = _("Parent Profiles")
        ordering = ['student', '-created_at']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ('student', 'parent_name')  # یک والد به ازای هر دانش‌آموز

    def __str__(self):
        return f"{self.parent_name} (Parent of {self.student.name or self.student.username})"
    
    def verify_password(self, raw_password):
        """تایید رمز والد"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.parent_password_hash)
    
    def set_password(self, raw_password):
        """تنظیم و هش رمز والد"""
        from django.contrib.auth.hashers import make_password
        self.parent_password_hash = make_password(raw_password)
    
    def save(self, *args, **kwargs):
        """ذخیره والدین"""
        super().save(*args, **kwargs)


class ParentAppUsageLog(BaseModel):
    """
    ثبت استفاده روزانه دانش‌آموز از اپلیکیشن برای والدین
    """
    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='usage_logs',
        verbose_name=_("Parent")
    )
    date = models.DateField(
        verbose_name=_("Date"),
        help_text=_("تاریخ استفاده")
    )
    total_minutes = models.IntegerField(
        default=0,
        verbose_name=_("Total minutes used"),
        help_text=_("کل دقایق استفاده در این روز")
    )
    session_count = models.IntegerField(
        default=0,
        verbose_name=_("Number of sessions"),
        help_text=_("تعداد جلسات استفاده در این روز")
    )
    
    class Meta:
        db_table = 'parent_app_usage_logs'
        verbose_name = _("Parent App Usage Log")
        verbose_name_plural = _("Parent App Usage Logs")
        ordering = ['-date']
        indexes = [
            models.Index(fields=['parent', '-date']),
            models.Index(fields=['date']),
        ]
        unique_together = ('parent', 'date')
    
    def __str__(self):
        return f"{self.parent.student.name} - {self.date} - {self.total_minutes} min"
    