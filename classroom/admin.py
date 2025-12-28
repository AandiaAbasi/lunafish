from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    ClassLevel, Language, Course, Lesson, LessonEnrollment,
    LessonMaterial, Whiteboard, Quiz, QuizQuestion, QuizAnswer,
    StudentQuizAttempt, StudentQuestionResponse, Attendance,
    Badge, StudentBadge, StudentProgress, AgoraToken
)


@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'created_at']
    list_editable = ['order']
    search_fields = ['name']
    ordering = ['order']


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'language', 'level', 'max_students', 'hourly_rate', 'is_active', 'created_at']
    list_filter = ['is_active', 'level', 'language', 'created_at']
    search_fields = ['title', 'teacher__username', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'description', 'teacher')
        }),
        (_('Course Details'), {
            'fields': ('language', 'level', 'max_students', 'duration_minutes')
        }),
        (_('Pricing'), {
            'fields': ('hourly_rate',)
        }),
        (_('Media'), {
            'fields': ('cover_image',)
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


class LessonMaterialInline(admin.TabularInline):
    model = LessonMaterial
    extra = 1
    fields = ['title', 'material_type', 'file', 'external_link', 'order']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'scheduled_at', 'status', 'is_recorded', 'created_at']
    list_filter = ['status', 'is_recorded', 'course', 'scheduled_at']
    search_fields = ['title', 'course__title', 'agora_channel_name']
    readonly_fields = ['created_at', 'updated_at', 'agora_channel_id']
    inlines = [LessonMaterialInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('course', 'title', 'description')
        }),
        (_('Schedule'), {
            'fields': ('scheduled_at', 'started_at', 'ended_at')
        }),
        (_('Agora Configuration'), {
            'fields': ('agora_channel_id', 'agora_channel_name')
        }),
        (_('Recording'), {
            'fields': ('is_recorded', 'recording_url')
        }),
        (_('Status & Notes'), {
            'fields': ('status', 'teacher_notes')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


class EnrollmentInline(admin.TabularInline):
    model = LessonEnrollment
    extra = 1
    fields = ['student', 'role', 'status', 'paid', 'joined_at', 'left_at']
    raw_id_fields = ['student']


@admin.register(LessonEnrollment)
class LessonEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'role', 'status', 'paid', 'joined_at']
    list_filter = ['status', 'role', 'paid', 'lesson', 'joined_at']
    search_fields = ['student__username', 'lesson__title']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['student', 'lesson']
    
    fieldsets = (
        (_('Lesson & Student'), {
            'fields': ('lesson', 'student', 'role')
        }),
        (_('Agora'), {
            'fields': ('agora_uid',)
        }),
        (_('Attendance'), {
            'fields': ('joined_at', 'left_at', 'status')
        }),
        (_('Payment'), {
            'fields': ('paid',)
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(LessonMaterial)
class LessonMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'material_type', 'order', 'created_at']
    list_filter = ['material_type', 'lesson', 'created_at']
    search_fields = ['title', 'lesson__title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['lesson', 'order']


@admin.register(Whiteboard)
class WhiteboardAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'is_locked', 'last_modified_by', 'last_modified_at']
    list_filter = ['is_locked', 'last_modified_at']
    search_fields = ['lesson__title']
    readonly_fields = ['last_modified_at', 'created_at', 'updated_at']


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1
    fields = ['question_text', 'question_type', 'points', 'order']


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 1
    fields = ['answer_text', 'is_correct', 'order']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'difficulty', 'passing_score', 'is_active', 'created_at']
    list_filter = ['difficulty', 'is_active', 'show_before_lesson', 'show_during_lesson', 'show_after_lesson']
    search_fields = ['title', 'lesson__title']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [QuizQuestionInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('lesson', 'title', 'description')
        }),
        (_('Quiz Settings'), {
            'fields': ('difficulty', 'time_limit_minutes', 'passing_score')
        }),
        (_('Display Options'), {
            'fields': ('show_before_lesson', 'show_during_lesson', 'show_after_lesson')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['order', 'quiz', 'question_type', 'points', 'created_at']
    list_filter = ['question_type', 'quiz', 'created_at']
    search_fields = ['question_text', 'quiz__title']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [QuizAnswerInline]
    ordering = ['quiz', 'order']


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['order', 'question', 'is_correct', 'created_at']
    list_filter = ['is_correct', 'question__quiz', 'created_at']
    search_fields = ['answer_text', 'question__question_text']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['question', 'order']


class StudentQuestionResponseInline(admin.TabularInline):
    model = StudentQuestionResponse
    extra = 0
    fields = ['question', 'selected_answer', 'text_response', 'is_correct', 'points_earned']
    readonly_fields = ['question', 'selected_answer', 'text_response', 'is_correct', 'points_earned']
    can_delete = False


@admin.register(StudentQuizAttempt)
class StudentQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'score', 'passed', 'started_at', 'submitted_at']
    list_filter = ['passed', 'quiz', 'started_at', 'submitted_at']
    search_fields = ['student__username', 'quiz__title']
    readonly_fields = ['started_at', 'submitted_at', 'created_at', 'updated_at']
    inlines = [StudentQuestionResponseInline]
    
    fieldsets = (
        (_('Quiz & Student'), {
            'fields': ('quiz', 'student', 'lesson_enrollment')
        }),
        (_('Scoring'), {
            'fields': ('score', 'total_points', 'earned_points', 'passed')
        }),
        (_('Timing'), {
            'fields': ('started_at', 'submitted_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(StudentQuestionResponse)
class StudentQuestionResponseAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct', 'points_earned', 'response_time_seconds']
    list_filter = ['is_correct', 'attempt__quiz', 'created_at']
    search_fields = ['attempt__student__username', 'question__question_text']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'status', 'minutes_attended', 'expected_at']
    list_filter = ['status', 'lesson', 'expected_at']
    search_fields = ['student__username', 'lesson__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Lesson & Student'), {
            'fields': ('lesson', 'student')
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Timing'), {
            'fields': ('expected_at', 'actual_joined_at', 'left_at', 'minutes_attended')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'criteria_type', 'color', 'created_at']
    list_filter = ['criteria_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ['student', 'badge', 'earned_at']
    list_filter = ['badge', 'earned_at']
    search_fields = ['student__username', 'badge__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'attendance_percentage', 'average_quiz_score', 'badges_earned', 'last_updated']
    list_filter = ['course', 'attendance_percentage', 'last_updated']
    search_fields = ['student__username', 'course__title']
    readonly_fields = ['lessons_completed', 'lessons_attended', 'attendance_percentage',
                       'average_quiz_score', 'total_points', 'badges_earned',
                       'last_updated', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Student & Course'), {
            'fields': ('student', 'course')
        }),
        (_('Lesson Statistics'), {
            'fields': ('total_lessons', 'lessons_completed', 'lessons_attended', 'attendance_percentage')
        }),
        (_('Quiz Statistics'), {
            'fields': ('average_quiz_score', 'total_points')
        }),
        (_('Achievements'), {
            'fields': ('badges_earned',)
        }),
        (_('Update'), {
            'fields': ('last_updated',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AgoraToken)
class AgoraTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'privilege', 'expires_at', 'is_revoked', 'is_valid']
    list_filter = ['privilege', 'is_revoked', 'expires_at', 'generated_at']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['token', 'generated_at', 'created_at', 'updated_at']
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = _('Is Valid')
