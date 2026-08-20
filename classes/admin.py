from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    ClassAttachment,
    TeacherArchivedFile,
    TeacherArchiveFolder,
    ClassEnrollment,
    ClassMessage,
    ClassReaction,
    HandRaise,
    OnlineClass,
    format_datetime_display,
)


class LocalizedDateAdminMixin:
    date_fields_to_hide = []
    localized_readonly_date_fields = []

    def get_date_fields_to_hide(self, request, obj=None):
        return list(self.date_fields_to_hide)

    def get_localized_readonly_date_fields(self, request, obj=None):
        return list(self.localized_readonly_date_fields)

    def get_exclude(self, request, obj=None):
        exclude = list(super().get_exclude(request, obj) or [])

        for field_name in self.get_date_fields_to_hide(request, obj):
            if field_name not in exclude:
                exclude.append(field_name)

        return exclude

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))

        for field_name in self.get_localized_readonly_date_fields(request, obj):
            if field_name not in readonly_fields:
                readonly_fields.append(field_name)

        return readonly_fields


@admin.register(OnlineClass)
class OnlineClassAdmin(LocalizedDateAdminMixin, admin.ModelAdmin):
    list_display = [
        'title',
        'teacher',
        'class_source_display',
        'status',
        'scheduled_start_display',
        'enrolled_count',
        'max_students',
    ]
    list_filter = [
        'status',
        'scheduled_start',
        'placement_assessment__status',
        'allow_student_chat',
        'allow_student_reactions',
        'enable_recording',
    ]
    search_fields = [
        'title',
        'description',
        'teacher__username',
        'teacher__phone',
        'teacher__email',
        'placement_assessment__student__username',
        'placement_assessment__student__name',
        'placement_assessment__student__phone',
    ]
    readonly_fields = ['id', 'room_id']
    list_select_related = ['teacher', 'booking', 'placement_assessment__student']

    @admin.display(description=_('Class source'))
    def class_source_display(self, obj):
        if obj.placement_assessment_id:
            return _('Placement assessment')
        if obj.booking_id:
            return _('Booking')
        return _('Manual')
    localized_readonly_date_fields = [
        'scheduled_start_display',
        'scheduled_end_display',
        'actual_start_display',
        'actual_end_display',
        'created_at_display',
        'updated_at_display',
    ]

    def get_date_fields_to_hide(self, request, obj=None):
        if obj is None:
            return []

        return [
            'scheduled_start',
            'scheduled_end',
            'actual_start',
            'actual_end',
        ]

    def get_localized_readonly_date_fields(self, request, obj=None):
        if obj is None:
            return []

        return super().get_localized_readonly_date_fields(request, obj)


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(LocalizedDateAdminMixin, admin.ModelAdmin):
    list_display = [
        'class_session',
        'student',
        'can_unmute',
        'can_share_video',
        'can_share_screen',
        'is_moderator',
        'left_at_display',
    ]
    list_filter = [
        'can_unmute',
        'can_share_video',
        'can_share_screen',
        'is_moderator',
    ]
    search_fields = [
        'class_session__title',
        'student__username',
        'student__phone',
        'student__email',
    ]
    date_fields_to_hide = [
        'enrolled_at',
        'joined_at',
        'left_at',
    ]
    localized_readonly_date_fields = [
        'enrolled_at_display',
        'joined_at_display',
        'left_at_display',
        'created_at_display',
        'updated_at_display',
    ]


@admin.register(HandRaise)
class HandRaiseAdmin(LocalizedDateAdminMixin, admin.ModelAdmin):
    list_display = [
        'class_session',
        'student',
        'raised_at_display',
        'lowered_at_display',
        'acknowledged_by',
        'acknowledged_at_display',
    ]
    list_filter = [
        'raised_at',
        'lowered_at',
        'acknowledged_at',
    ]
    search_fields = [
        'class_session__title',
        'student__username',
        'student__phone',
    ]
    date_fields_to_hide = [
        'raised_at',
        'lowered_at',
        'acknowledged_at',
    ]
    localized_readonly_date_fields = [
        'raised_at_display',
        'lowered_at_display',
        'acknowledged_at_display',
    ]


@admin.register(ClassMessage)
class ClassMessageAdmin(LocalizedDateAdminMixin, admin.ModelAdmin):
    list_display = [
        'class_session',
        'sender',
        'content',
        'is_private',
        'is_deleted',
        'created_at_display',
    ]
    list_filter = [
        'is_private',
        'is_deleted',
        'created_at',
    ]
    search_fields = [
        'class_session__title',
        'sender__username',
        'sender__phone',
        'content',
    ]
    date_fields_to_hide = [
        'deleted_at',
    ]
    localized_readonly_date_fields = [
        'deleted_at_display',
        'created_at_display',
        'updated_at_display',
    ]




@admin.register(TeacherArchiveFolder)
class TeacherArchiveFolderAdmin(LocalizedDateAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'teacher', 'is_deleted', 'created_at_display']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['title', 'teacher__username', 'teacher__phone']
    date_fields_to_hide = ['deleted_at']
    localized_readonly_date_fields = ['created_at_display', 'updated_at_display']


@admin.register(TeacherArchivedFile)
class TeacherArchivedFileAdmin(LocalizedDateAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'teacher', 'display_folders', 'original_filename', 'file_size', 'is_deleted', 'created_at_display']
    list_filter = ['is_deleted', 'folders', 'created_at']
    search_fields = ['title', 'teacher__username', 'teacher__phone', 'original_filename', 'folders__title']

    def display_folders(self, obj):
        return ', '.join(obj.folders.values_list('title', flat=True))

    display_folders.short_description = 'Folders'
    date_fields_to_hide = ['deleted_at']
    localized_readonly_date_fields = ['created_at_display', 'updated_at_display']


@admin.register(ClassAttachment)
class ClassAttachmentAdmin(LocalizedDateAdminMixin, admin.ModelAdmin):
    list_display = [
        'class_session',
        'uploaded_by',
        'title',
        'original_filename',
        'file_size',
        'is_deleted',
        'created_at_display',
    ]
    list_filter = [
        'is_deleted',
        'created_at',
    ]
    search_fields = [
        'class_session__title',
        'uploaded_by__username',
        'uploaded_by__phone',
        'title',
        'original_filename',
    ]
    date_fields_to_hide = [
        'deleted_at',
    ]
    localized_readonly_date_fields = [
        'deleted_at_display',
        'created_at_display',
        'updated_at_display',
    ]


@admin.register(ClassReaction)
class ClassReactionAdmin(LocalizedDateAdminMixin, admin.ModelAdmin):
    list_display = [
        'class_session',
        'student',
        'emoji',
        'message',
        'created_at_display',
    ]
    list_filter = [
        'emoji',
        'created_at',
    ]
    search_fields = [
        'class_session__title',
        'student__username',
        'student__phone',
    ]
    date_fields_to_hide = [
        'created_at',
    ]
    localized_readonly_date_fields = [
        'created_at_display',
    ]

    def created_at_display(self, obj):
        return format_datetime_display(obj, obj.created_at)

    created_at_display.short_description = _('Created at')
    created_at_display.admin_order_field = 'created_at'
