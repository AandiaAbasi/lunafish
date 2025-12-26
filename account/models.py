from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import os
import uuid
from django.core.validators import FileExtensionValidator
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
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Birth date")
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
        upload_to='avatars/templates/',
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
    