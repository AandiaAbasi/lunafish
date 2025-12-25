from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.abstract_models import BaseModel

class Service(BaseModel):
    """Skyroom Service Model"""
    
    STATUS_CHOICES = [
        (0, _('Inactive')),
        (1, _('Active')),
    ]
    
    # Skyroom ID
    skyroom_id = models.IntegerField(unique=True, verbose_name=_('Skyroom Service ID'))
    
    # Basic Info
    title = models.CharField(
        max_length=128,
        verbose_name=_('Service Title'),
        help_text=_('Service title (max 128 characters)')
    )
    
    # Status
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=1,
        verbose_name=_('Status'),
        help_text=_('0: Inactive, 1: Active')
    )
    
    # Limits
    user_limit = models.IntegerField(
        default=10,
        verbose_name=_('User Limit'),
        help_text=_('Maximum concurrent users')
    )
    video_limit = models.IntegerField(
        default=8,
        verbose_name=_('Video Limit'),
        help_text=_('Maximum concurrent videos per room')
    )
    time_limit = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Time Limit (seconds)'),
        help_text=_('Person-second time limit')
    )
    
    # Usage
    time_usage = models.BigIntegerField(
        default=0,
        verbose_name=_('Time Usage (seconds)'),
        help_text=_('Person-second time used')
    )
    
    # Timestamps (Unix time)
    start_time = models.BigIntegerField(
        verbose_name=_('Start Time'),
        help_text=_('Service start time (Unix timestamp)')
    )
    stop_time = models.BigIntegerField(
        verbose_name=_('Stop Time'),
        help_text=_('Service stop time (Unix timestamp)')
    )
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
    
    def __str__(self):
        return f"{self.title} (ID: {self.skyroom_id})"


class Room(BaseModel):
    """Skyroom Room Model"""
    
    STATUS_CHOICES = [
        (0, _('Inactive')),
        (1, _('Active')),
    ]
    
    # Skyroom ID
    skyroom_id = models.IntegerField(unique=True, verbose_name=_('Skyroom Room ID'))
    
    # Service Reference
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='rooms',
        verbose_name=_('Service'),
        help_text=_('Service this room belongs to')
    )
    
    # Basic Info
    name = models.CharField(
        max_length=128,
        unique=True,
        verbose_name=_('Room Name'),
        help_text=_('Room name in Latin (max 128 characters)')
    )
    title = models.CharField(
        max_length=128,
        verbose_name=_('Room Title'),
        help_text=_('Room display title (max 128 characters)')
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Room description (max 512 characters)')
    )
    
    # Status
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=1,
        verbose_name=_('Status'),
        help_text=_('0: Inactive, 1: Active')
    )
    
    # Access Control
    guest_login = models.BooleanField(
        default=False,
        verbose_name=_('Allow Guest Login'),
        help_text=_('Allow guest login')
    )
    guest_limit = models.IntegerField(
        default=0,
        verbose_name=_('Guest Limit'),
        help_text=_('Maximum guests (0 = unlimited)')
    )
    op_login_first = models.BooleanField(
        default=True,
        verbose_name=_('Operator Login First'),
        help_text=_('Require operator to login first')
    )
    
    # Limits
    max_users = models.IntegerField(
        default=10,
        verbose_name=_('Max Users'),
        help_text=_('Maximum concurrent users')
    )
    session_duration = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Session Duration (seconds)'),
        help_text=_('Maximum session duration in seconds')
    )
    time_limit = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Time Limit (seconds)'),
        help_text=_('Person-second time limit')
    )
    
    # Usage
    time_usage = models.BigIntegerField(
        default=0,
        verbose_name=_('Time Usage (seconds)'),
        help_text=_('Person-second time used in current session')
    )
    time_total = models.BigIntegerField(
        default=0,
        verbose_name=_('Total Time Usage (seconds)'),
        help_text=_('Total person-second time used')
    )
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')
    
    def __str__(self):
        return f"{self.title} ({self.name}) - ID: {self.skyroom_id}"


class SkyroomUser(BaseModel):
    """Skyroom User Model"""
    
    STATUS_CHOICES = [
        (0, _('Inactive')),
        (1, _('Active')),
    ]
    
    GENDER_CHOICES = [
        (0, _('Unknown')),
        (1, _('Male')),
        (2, _('Female')),
    ]
    
    # Skyroom ID
    skyroom_id = models.IntegerField(unique=True, verbose_name=_('Skyroom User ID'))
    
    # Credentials
    username = models.CharField(
        max_length=32,
        unique=True,
        verbose_name=_('Username'),
        help_text=_('Username in Latin (max 32 characters)')
    )
    nickname = models.CharField(
        max_length=128,
        verbose_name=_('Nickname'),
        help_text=_('Display name (max 128 characters)')
    )
    password = models.CharField(
        max_length=255,
        verbose_name=_('Password Hash'),
        help_text=_('Password hash (max 24 characters original)')
    )
    
    # Contact Info
    email = models.EmailField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name=_('Email'),
        help_text=_('Email address (max 128 characters)')
    )
    
    # Personal Info
    fname = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name=_('First Name'),
        help_text=_('First name (max 128 characters)')
    )
    lname = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name=_('Last Name'),
        help_text=_('Last name (max 128 characters)')
    )
    gender = models.IntegerField(
        choices=GENDER_CHOICES,
        default=0,
        verbose_name=_('Gender'),
        help_text=_('0: Unknown, 1: Male, 2: Female')
    )
    
    # Status
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=1,
        verbose_name=_('Status'),
        help_text=_('0: Inactive, 1: Active')
    )
    
    # Public/Concurrent
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Is Public'),
        help_text=_('Is this a public/shared account')
    )
    concurrent = models.IntegerField(
        default=0,
        verbose_name=_('Concurrent Limit'),
        help_text=_('Concurrent usage limit (0 = unlimited)')
    )
    
    # Time Management
    time_limit = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Time Limit (seconds)'),
        help_text=_('Maximum time allowed (seconds)')
    )
    time_usage = models.BigIntegerField(
        default=0,
        verbose_name=_('Time Usage (seconds)'),
        help_text=_('Current time used (seconds)')
    )
    time_total = models.BigIntegerField(
        default=0,
        verbose_name=_('Total Time Usage (seconds)'),
        help_text=_('Total time used across all sessions (seconds)')
    )
    
    # Expiry
    expiry_date = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Expiry Date'),
        help_text=_('Account expiry date (Unix timestamp)')
    )
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Skyroom User')
        verbose_name_plural = _('Skyroom Users')
    
    def __str__(self):
        return f"{self.nickname} ({self.username}) - ID: {self.skyroom_id}"


class RoomUserAccess(BaseModel):
    """Room User Access Model"""
    
    ACCESS_CHOICES = [
        (1, _('Normal User')),
        (2, _('Presenter')),
        (3, _('Operator')),
    ]
    
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='user_accesses',
        verbose_name=_('Room')
    )
    user = models.ForeignKey(
        SkyroomUser,
        on_delete=models.CASCADE,
        related_name='room_accesses',
        verbose_name=_('User')
    )
    
    access = models.IntegerField(
        choices=ACCESS_CHOICES,
        default=1,
        verbose_name=_('Access Level'),
        help_text=_('1: Normal User, 2: Presenter, 3: Operator')
    )
    
    class Meta:
        unique_together = ['room', 'user']
        verbose_name = _('Room User Access')
        verbose_name_plural = _('Room User Accesses')
    
    def __str__(self):
        return f"{self.user.username} -> {self.room.name} ({self.get_access_display()})"


class LoginUrl(BaseModel):
    """Login URL Model for direct access without login"""
    
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='login_urls',
        verbose_name=_('Room')
    )
    
    # User identifier can be a number or string
    user_id = models.CharField(
        max_length=255,
        verbose_name=_('User ID'),
        help_text=_('User identifier (number or string)')
    )
    
    nickname = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name=_('Nickname'),
        help_text=_('Display name for this login')
    )
    
    access = models.IntegerField(
        choices=RoomUserAccess.ACCESS_CHOICES,
        default=1,
        verbose_name=_('Access Level')
    )
    
    concurrent = models.IntegerField(
        default=1,
        verbose_name=_('Concurrent Limit'),
        help_text=_('Number of concurrent users allowed')
    )
    
    url = models.TextField(verbose_name=_('Login URL'))
    
    ttl = models.IntegerField(
        default=3600,
        verbose_name=_('TTL (seconds)'),
        help_text=_('Time to live for this login URL')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    expires_at = models.DateTimeField(
        verbose_name=_('Expires At'),
        help_text=_('When this login URL expires')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Login URL')
        verbose_name_plural = _('Login URLs')
    
    def __str__(self):
        return f"{self.room.name} - {self.user_id} (Expires: {self.expires_at})"
    
    def is_expired(self):
        """Check if login URL has expired"""
        return timezone.now() > self.expires_at
