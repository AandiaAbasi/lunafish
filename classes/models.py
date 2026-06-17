import uuid

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
import jdatetime

from core.abstract_models import BaseModel


def format_datetime_display(instance, dt):
    formatter = getattr(instance, "_format_datetime", None)
    if callable(formatter):
        return formatter(dt)

    if not dt:
        return "-"

    try:
        dt = timezone.localtime(dt)
    except Exception:
        pass

    lang = get_language()

    if lang and lang.startswith("fa"):
        return jdatetime.datetime.fromgregorian(
            datetime=dt
        ).strftime('%H:%M:%S %Y-%m-%d')

    return dt.strftime('%H:%M:%S %Y-%m-%d')


class OnlineClass(BaseModel):
    STATUS_SCHEDULED = 'scheduled'
    STATUS_ACTIVE = 'active'
    STATUS_ENDED = 'ended'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, _('Scheduled')),
        (STATUS_ACTIVE, _('Active')),
        (STATUS_ENDED, _('Ended')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='classes_teaching',
        verbose_name=_('Teacher'),
    )
    booking = models.OneToOneField(
        "classroom.ClassBooking",
        on_delete=models.PROTECT,
        related_name='booked_class',
        verbose_name=_("کلاس رزرو شده"),
        null=True,
        blank=True,
    )
    reward_granted = models.BooleanField(default=False, verbose_name=_('Reward granted'))
    scheduled_start = models.DateTimeField(verbose_name=_('Scheduled start'))
    scheduled_end = models.DateTimeField(verbose_name=_('Scheduled end'))
    actual_start = models.DateTimeField(null=True, blank=True, verbose_name=_('Actual start'))
    actual_end = models.DateTimeField(null=True, blank=True, verbose_name=_('Actual end'))
    room_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name=_('RTC room ID'))
    max_students = models.PositiveIntegerField(default=100, verbose_name=_('Max students'))
    allow_student_chat = models.BooleanField(default=True, verbose_name=_('Allow student chat'))
    allow_student_reactions = models.BooleanField(default=True, verbose_name=_('Allow student reactions'))
    require_approval_to_join = models.BooleanField(default=False, verbose_name=_('Require approval to join'))
    enable_recording = models.BooleanField(default=False, verbose_name=_('Enable recording'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SCHEDULED,
        db_index=True,
        verbose_name=_('Status'),
    )

    class Meta:
        ordering = ['-scheduled_start']
        verbose_name = _('Online Class')
        verbose_name_plural = _('Online Classes')
        indexes = [
            models.Index(fields=['teacher', 'status']),
            models.Index(fields=['scheduled_start', 'status']),
        ]

    def clean(self):
        if self.teacher_id and getattr(self.teacher, 'role', None) != 'teacher':
            raise ValidationError({'teacher': _('Selected user must have teacher role.')})
        if self.scheduled_end and self.scheduled_start and self.scheduled_end <= self.scheduled_start:
            raise ValidationError({'scheduled_end': _('Scheduled end must be after scheduled start.')})

    def __str__(self):
        return f'{self.title} - {self.teacher}'

    def scheduled_start_display(self):
        return format_datetime_display(self, self.scheduled_start)
    scheduled_start_display.short_description = _('Scheduled start')
    scheduled_start_display.admin_order_field = 'scheduled_start'

    def scheduled_end_display(self):
        return format_datetime_display(self, self.scheduled_end)
    scheduled_end_display.short_description = _('Scheduled end')
    scheduled_end_display.admin_order_field = 'scheduled_end'

    def actual_start_display(self):
        return format_datetime_display(self, self.actual_start)
    actual_start_display.short_description = _('Actual start')
    actual_start_display.admin_order_field = 'actual_start'

    def actual_end_display(self):
        return format_datetime_display(self, self.actual_end)
    actual_end_display.short_description = _('Actual end')
    actual_end_display.admin_order_field = 'actual_end'

    @property
    @admin.display(boolean=True, description=_('Is active'), ordering='status')
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    @admin.display(description=_('Duration (minutes)'))
    def duration_minutes(self):
        if not self.scheduled_start or not self.scheduled_end:
            return 0
        return int((self.scheduled_end - self.scheduled_start).total_seconds() / 60)

    @property
    @admin.display(description=_('Actual duration (minutes)'))
    def actual_duration_minutes(self):
        if not self.actual_start or not self.actual_end:
            return 0
        return int((self.actual_end - self.actual_start).total_seconds() / 60)

    @property
    @admin.display(description=_('Enrolled count'))
    def enrolled_count(self):
        return self.enrollments.filter(left_at__isnull=True).count()

    @property
    @admin.display(boolean=True, description=_('Is full'))
    def is_full(self):
        return self.enrolled_count >= self.max_students

    def start(self):
        if self.status != self.STATUS_SCHEDULED:
            raise ValueError(_('Only scheduled classes can be started.'))
        self.status = self.STATUS_ACTIVE
        self.actual_start = timezone.now()
        self.save(update_fields=['status', 'actual_start', 'updated_at'])

    def end(self):
        if self.status != self.STATUS_ACTIVE:
            raise ValueError(_('Only active classes can be ended.'))
        self.status = self.STATUS_ENDED
        self.actual_end = timezone.now()
        self.save(update_fields=['status', 'actual_end', 'updated_at'])

    def cancel(self):
        if self.status not in [self.STATUS_SCHEDULED, self.STATUS_ACTIVE]:
            raise ValueError(_('Only scheduled or active classes can be cancelled.'))
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=['status', 'updated_at'])


class ClassEnrollment(BaseModel):
    class_session = models.ForeignKey(
        OnlineClass,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_('Class session'),
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrolled_classes',
        verbose_name=_('Student'),
    )
    can_unmute = models.BooleanField(default=False, verbose_name=_('Can unmute'))
    can_share_video = models.BooleanField(default=False, verbose_name=_('Can share video'))
    can_share_screen = models.BooleanField(default=False, verbose_name=_('Can share screen'))
    is_moderator = models.BooleanField(default=False, verbose_name=_('Is moderator'))
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Enrolled at'))
    joined_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Joined at'))
    left_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Left at'))

    class Meta:
        ordering = ['enrolled_at']
        unique_together = ('class_session', 'student')
        verbose_name = _('Class Enrollment')
        verbose_name_plural = _('Class Enrollments')
        indexes = [
            models.Index(fields=['student', 'left_at']),
            models.Index(fields=['class_session', 'left_at']),
        ]

    def clean(self):
        if self.student_id and getattr(self.student, 'role', None) == 'teacher':
            raise ValidationError({'student': _('Teacher users cannot be enrolled as students.')})
        if self.class_session_id and self.student_id == self.class_session.teacher_id:
            raise ValidationError({'student': _('Class teacher cannot be enrolled as student.')})

    def __str__(self):
        return f'{self.student} in {self.class_session}'

    def enrolled_at_display(self):
        return format_datetime_display(self, self.enrolled_at)
    enrolled_at_display.short_description = _('Enrolled at')
    enrolled_at_display.admin_order_field = 'enrolled_at'

    def joined_at_display(self):
        return format_datetime_display(self, self.joined_at)
    joined_at_display.short_description = _('Joined at')
    joined_at_display.admin_order_field = 'joined_at'

    def left_at_display(self):
        return format_datetime_display(self, self.left_at)
    left_at_display.short_description = _('Left at')
    left_at_display.admin_order_field = 'left_at'

    @property
    @admin.display(boolean=True, description=_('Is active'), ordering='left_at')
    def is_active(self):
        return self.left_at is None

    @property
    @admin.display(boolean=True, description=_('Is currently joined'), ordering='joined_at')
    def is_currently_joined(self):
        return self.joined_at is not None and self.left_at is None

    def join(self):
        if not self.is_active:
            raise ValueError(_('Inactive enrollment cannot join.'))
        self.joined_at = timezone.now()
        self.left_at = None
        self.save(update_fields=['joined_at', 'left_at', 'updated_at'])

    def leave(self):
        self.left_at = timezone.now()
        self.save(update_fields=['left_at', 'updated_at'])


class HandRaise(models.Model):
    class_session = models.ForeignKey(OnlineClass, on_delete=models.CASCADE, related_name='raised_hands', verbose_name=_('Class session'))
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hand_raises', verbose_name=_('Student'))
    raised_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Raised at'))
    lowered_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Lowered at'))
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='acknowledged_hands',
        null=True,
        blank=True,
        verbose_name=_('Acknowledged by'),
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Acknowledged at'))

    class Meta:
        ordering = ['raised_at']
        verbose_name = _('Hand Raise')
        verbose_name_plural = _('Hand Raises')
        indexes = [
            models.Index(fields=['class_session', 'lowered_at']),
            models.Index(fields=['student', 'raised_at']),
        ]

    def raised_at_display(self):
        return format_datetime_display(self, self.raised_at)
    raised_at_display.short_description = _('Raised at')
    raised_at_display.admin_order_field = 'raised_at'

    def lowered_at_display(self):
        return format_datetime_display(self, self.lowered_at)
    lowered_at_display.short_description = _('Lowered at')
    lowered_at_display.admin_order_field = 'lowered_at'

    def acknowledged_at_display(self):
        return format_datetime_display(self, self.acknowledged_at)
    acknowledged_at_display.short_description = _('Acknowledged at')
    acknowledged_at_display.admin_order_field = 'acknowledged_at'

    @property
    @admin.display(boolean=True, description=_('Is active'), ordering='lowered_at')
    def is_active(self):
        return self.lowered_at is None

    @property
    @admin.display(boolean=True, description=_('Is acknowledged'), ordering='acknowledged_at')
    def is_acknowledged(self):
        return self.acknowledged_at is not None

    @property
    @admin.display(description=_('Duration (seconds)'))
    def duration_seconds(self):
        return int(((self.lowered_at or timezone.now()) - self.raised_at).total_seconds())

    def lower(self):
        self.lowered_at = timezone.now()
        self.save(update_fields=['lowered_at'])

    def acknowledge(self, by_user):
        self.acknowledged_by = by_user
        self.acknowledged_at = timezone.now()
        self.save(update_fields=['acknowledged_by', 'acknowledged_at'])


class ClassMessage(BaseModel):
    class_session = models.ForeignKey(OnlineClass, on_delete=models.CASCADE, related_name='messages', verbose_name=_('Class session'))
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='class_messages_sent', verbose_name=_('Sender'))
    content = models.TextField(verbose_name=_('Content'))
    is_private = models.BooleanField(default=False, verbose_name=_('Is private'))
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='class_messages_received',
        null=True,
        blank=True,
        verbose_name=_('Recipient'),
    )
    is_deleted = models.BooleanField(default=False, verbose_name=_('Is deleted'))
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='deleted_class_messages',
        null=True,
        blank=True,
        verbose_name=_('Deleted by'),
    )
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Deleted at'))

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Class Message')
        verbose_name_plural = _('Class Messages')
        indexes = [
            models.Index(fields=['class_session', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['is_deleted', 'created_at']),
        ]

    def deleted_at_display(self):
        return format_datetime_display(self, self.deleted_at)
    deleted_at_display.short_description = _('Deleted at')
    deleted_at_display.admin_order_field = 'deleted_at'

    def soft_delete(self, by_user):
        self.is_deleted = True
        self.deleted_by = by_user
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_by', 'deleted_at', 'updated_at'])


class ClassReaction(models.Model):
    EMOJI_CHOICES = [
        ('👍', _('Thumbs Up')),
        ('❤️', _('Heart')),
        ('👏', _('Clap')),
        ('🎉', _('Party')),
        ('🤔', _('Thinking')),
        ('😮', _('Surprised')),
    ]

    class_session = models.ForeignKey(OnlineClass, on_delete=models.CASCADE, related_name='reactions', verbose_name=_('Class session'))
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='class_reactions', verbose_name=_('Student'))
    emoji = models.CharField(max_length=10, choices=EMOJI_CHOICES, verbose_name=_('Emoji'))
    message = models.ForeignKey(ClassMessage, on_delete=models.CASCADE, related_name='reactions', null=True, blank=True, verbose_name=_('Message'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Class Reaction')
        verbose_name_plural = _('Class Reactions')
        indexes = [
            models.Index(fields=['class_session', 'created_at']),
            models.Index(fields=['student', 'created_at']),
        ]

