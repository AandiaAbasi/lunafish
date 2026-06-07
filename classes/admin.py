from django.contrib import admin

from .models import ClassEnrollment, ClassMessage, ClassReaction, HandRaise, OnlineClass


@admin.register(OnlineClass)
class OnlineClassAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'status', 'scheduled_start', 'enrolled_count', 'max_students']
    list_filter = ['status', 'scheduled_start', 'allow_student_chat', 'allow_student_reactions', 'enable_recording']
    search_fields = ['title', 'description', 'teacher__username', 'teacher__phone', 'teacher__email']
    readonly_fields = ['id', 'room_id', 'actual_start', 'actual_end', 'created_at_display', 'updated_at_display']


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['class_session', 'student', 'can_unmute', 'can_share_video', 'can_share_screen', 'is_moderator', 'left_at']
    list_filter = ['can_unmute', 'can_share_video', 'can_share_screen', 'is_moderator']
    search_fields = ['class_session__title', 'student__username', 'student__phone', 'student__email']
    readonly_fields = ['enrolled_at', 'joined_at', 'left_at', 'created_at_display', 'updated_at_display']


@admin.register(HandRaise)
class HandRaiseAdmin(admin.ModelAdmin):
    list_display = ['class_session', 'student', 'raised_at', 'lowered_at', 'acknowledged_by', 'acknowledged_at']
    list_filter = ['raised_at', 'lowered_at', 'acknowledged_at']
    search_fields = ['class_session__title', 'student__username', 'student__phone']


@admin.register(ClassMessage)
class ClassMessageAdmin(admin.ModelAdmin):
    list_display = ['class_session', 'sender', 'content', 'is_private', 'is_deleted', 'created_at']
    list_filter = ['is_private', 'is_deleted', 'created_at']
    search_fields = ['class_session__title', 'sender__username', 'sender__phone', 'content']


@admin.register(ClassReaction)
class ClassReactionAdmin(admin.ModelAdmin):
    list_display = ['class_session', 'student', 'emoji', 'message', 'created_at']
    list_filter = ['emoji', 'created_at']
    search_fields = ['class_session__title', 'student__username', 'student__phone']

