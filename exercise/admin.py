from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    Exercise, Question, QuestionOption,
    StudentExerciseAttempt, StudentQuestionAnswer,
    ExerciseChoice, StudentExerciseChoice
)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'subject', 'exercise_type', 'difficulty', 'is_optional_badge', 'is_published_badge', 'question_count']
    list_filter = ['teacher', 'subject', 'exercise_type', 'difficulty', 'is_optional', 'is_published', 'created_at']
    search_fields = ['title', 'teacher__name', 'subject__title']
    readonly_fields = ['created_at', 'updated_at', 'question_count', 'optional_question_count']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('teacher', 'subject', 'title', 'description')
        }),
        (_('نوع و تنظیمات'), {
            'fields': ('exercise_type', 'difficulty', 'duration_minutes', 'total_points', 'pass_score', 'is_optional')
        }),
        (_('نسخه‌های متفاوت'), {
            'fields': ('parent_exercise', 'variant_order'),
            'classes': ('collapse',),
            'description': _('اگر این تمرین یک نسخه متفاوت از تمرین دیگری است')
        }),
        (_('انتشار'), {
            'fields': ('is_published',)
        }),
        (_('آمار'), {
            'fields': ('question_count', 'optional_question_count'),
            'classes': ('collapse',)
        }),
        (_('سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_optional_badge(self, obj):
        """نشان‌گر اختیاری بودن"""
        if obj.is_optional:
            return '<span style="color: orange;">● اختیاری</span>'
        return '<span style="color: blue;">● الزامی</span>'
    is_optional_badge.short_description = _('نوع')
    is_optional_badge.allow_tags = True
    
    def is_published_badge(self, obj):
        """نشان‌گر منتشر شدن"""
        color = 'green' if obj.is_published else 'red'
        text = 'منتشر شده' if obj.is_published else 'منتشر نشده'
        return f'<span style="color: {color};">● {text}</span>'
    is_published_badge.short_description = _('وضعیت انتشار')
    is_published_badge.allow_tags = True
    
    def question_count(self, obj):
        """تعداد سوالات الزامی"""
        return obj.get_question_count()
    question_count.short_description = _('سوالات الزامی')
    
    def optional_question_count(self, obj):
        """تعداد سوالات اختیاری"""
        return obj.get_optional_question_count()
    optional_question_count.short_description = _('سوالات اختیاری')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'exercise', 'question_type', 'order', 'points', 'option_count']
    list_filter = ['exercise', 'question_type', 'created_at']
    search_fields = ['text', 'exercise__title']
    readonly_fields = ['created_at', 'updated_at', 'option_count']
    ordering = ['exercise', 'order']
    
    fieldsets = (
        (_('سوال'), {
            'fields': ('exercise', 'order', 'question_type', 'text')
        }),
        (_('رسانه‌ها'), {
            'fields': ('image', 'audio', 'video'),
            'classes': ('collapse',)
        }),
        (_('تنظیمات'), {
            'fields': ('points', 'is_required', 'explanation')
        }),
        (_('سیستم'), {
            'fields': ('created_at', 'updated_at', 'option_count'),
            'classes': ('collapse',)
        }),
    )
    
    def question_preview(self, obj):
        """پیش‌نمایش متن سوال"""
        return f"{obj.text[:50]}..." if len(obj.text) > 50 else obj.text
    question_preview.short_description = _('متن سوال')
    
    def option_count(self, obj):
        """تعداد گزینه‌ها"""
        return obj.options.count()
    option_count.short_description = _('تعداد گزینه‌ها')


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'question_preview', 'order', 'is_correct_badge']
    list_filter = ['question__exercise', 'is_correct', 'created_at']
    search_fields = ['text', 'question__text']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['question', 'order']
    
    fieldsets = (
        (_('گزینه'), {
            'fields': ('question', 'order', 'text')
        }),
        (_('رسانه‌ها'), {
            'fields': ('image', 'audio'),
            'classes': ('collapse',)
        }),
        (_('تنظیمات'), {
            'fields': ('is_correct', 'explanation')
        }),
        (_('سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """پیش‌نمایش متن گزینه"""
        return f"{obj.text[:40]}..." if len(obj.text) > 40 else obj.text
    text_preview.short_description = _('متن گزینه')
    
    def question_preview(self, obj):
        """پیش‌نمایش متن سوال"""
        return f"{obj.question.text[:30]}..." if len(obj.question.text) > 30 else obj.question.text
    question_preview.short_description = _('سوال')
    
    def is_correct_badge(self, obj):
        """نشان‌گر صحیح بودن"""
        color = 'green' if obj.is_correct else 'gray'
        text = '✓ صحیح' if obj.is_correct else 'غلط'
        return f'<span style="color: {color};">● {text}</span>'
    is_correct_badge.short_description = _('صحیح/غلط')
    is_correct_badge.allow_tags = True


@admin.register(StudentExerciseAttempt)
class StudentExerciseAttemptAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'exercise', 'status', 'score', 'percentage', 'pass_badge', 'submitted_at']
    list_filter = ['exercise', 'status', 'created_at', 'submitted_at']
    search_fields = ['student__name', 'student__username', 'exercise__title']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'submitted_at', 'graded_at', 'question_summary']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('تلاش'), {
            'fields': ('student', 'exercise', 'status')
        }),
        (_('نمره‌گذاری'), {
            'fields': ('score', 'percentage', 'teacher_notes')
        }),
        (_('زمان‌ها'), {
            'fields': ('started_at', 'submitted_at', 'graded_at'),
            'classes': ('collapse',)
        }),
        (_('سیستم'), {
            'fields': ('created_at', 'updated_at', 'question_summary'),
            'classes': ('collapse',)
        }),
    )
    
    def student_name(self, obj):
        """نام دانش‌آموز"""
        return obj.student.name or obj.student.username
    student_name.short_description = _('دانش‌آموز')
    
    def pass_badge(self, obj):
        """نشان‌گر قبول شدن"""
        if obj.percentage is None:
            return '<span style="color: gray;">- (نمره نشده)</span>'
        color = 'green' if obj.pass_exercise() else 'red'
        text = '✓ قبول' if obj.pass_exercise() else '✗ رد'
        return f'<span style="color: {color};">● {text}</span>'
    pass_badge.short_description = _('قبول/رد')
    pass_badge.allow_tags = True
    
    def question_summary(self, obj):
        """خلاصه پاسخ‌ها"""
        answered = obj.question_answers.filter(answer_text__isnull=False).exclude(answer_text='').count()
        total = obj.exercise.get_question_count()
        return f'{answered} / {total} جواب داده شده'
    question_summary.short_description = _('خلاصه')


@admin.register(StudentQuestionAnswer)
class StudentQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'question_preview', 'answer_preview', 'is_correct_badge', 'points_earned']
    list_filter = ['attempt__exercise', 'is_correct', 'created_at']
    search_fields = ['attempt__student__name', 'question__text']
    readonly_fields = ['created_at', 'updated_at', 'answered_at', 'full_answer']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('جواب'), {
            'fields': ('attempt', 'question', 'is_correct', 'points_earned')
        }),
        (_('محتوای جواب'), {
            'fields': ('answer_text', 'selected_option', 'answer_file', 'full_answer'),
            'classes': ('collapse',)
        }),
        (_('بازخورد'), {
            'fields': ('teacher_feedback',)
        }),
        (_('زمان‌ها'), {
            'fields': ('answered_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_name(self, obj):
        """نام دانش‌آموز"""
        return obj.attempt.student.name or obj.attempt.student.username
    student_name.short_description = _('دانش‌آموز')
    
    def question_preview(self, obj):
        """پیش‌نمایش متن سوال"""
        return f"{obj.question.text[:40]}..." if len(obj.question.text) > 40 else obj.question.text
    question_preview.short_description = _('سوال')
    
    def answer_preview(self, obj):
        """پیش‌نمایش جواب"""
        if obj.selected_option:
            return f"گزینه: {obj.selected_option.text[:30]}"
        if obj.answer_text:
            return f"{obj.answer_text[:40]}..." if len(obj.answer_text) > 40 else obj.answer_text
        return '(بدون جواب)'
    answer_preview.short_description = _('جواب')
    
    def is_correct_badge(self, obj):
        """نشان‌گر صحیح بودن"""
        if obj.is_correct is None:
            return '<span style="color: gray;">- (نمره نشده)</span>'
        color = 'green' if obj.is_correct else 'red'
        text = '✓ صحیح' if obj.is_correct else '✗ غلط'
        return f'<span style="color: {color};">● {text}</span>'
    is_correct_badge.short_description = _('صحیح/غلط')
    is_correct_badge.allow_tags = True
    
    def full_answer(self, obj):
        """جواب کامل"""
        if obj.selected_option:
            return f'گزینه انتخاب شده: {obj.selected_option.text}\n\nمتن جواب: {obj.answer_text or "(خالی)"}'
        return obj.answer_text or '(خالی)'
    full_answer.short_description = _('جواب کامل')


@admin.register(ExerciseChoice)
class ExerciseChoiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'subject', 'choice_type', 'exercise_count', 'required_choices', 'is_published_badge']
    list_filter = ['teacher', 'subject', 'choice_type', 'is_published', 'created_at']
    search_fields = ['title', 'teacher__name', 'subject__title']
    filter_horizontal = ['exercises']
    readonly_fields = ['created_at', 'updated_at', 'exercise_count']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('teacher', 'subject', 'title', 'description')
        }),
        (_('تنظیمات'), {
            'fields': ('choice_type', 'required_choices', 'is_published')
        }),
        (_('تمرین‌های موجود'), {
            'fields': ('exercises', 'exercise_count')
        }),
        (_('سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_published_badge(self, obj):
        """نشان‌گر منتشر شدن"""
        color = 'green' if obj.is_published else 'red'
        text = 'منتشر شده' if obj.is_published else 'منتشر نشده'
        return f'<span style="color: {color};">● {text}</span>'
    is_published_badge.short_description = _('وضعیت انتشار')
    is_published_badge.allow_tags = True
    
    def exercise_count(self, obj):
        """تعداد تمرین‌های موجود"""
        return obj.get_exercise_count()
    exercise_count.short_description = _('تعداد تمرین‌ها')


@admin.register(StudentExerciseChoice)
class StudentExerciseChoiceAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'choice_group_title', 'exercise_count', 'confirmed_at']
    list_filter = ['exercise_choice_group', 'confirmed_at', 'created_at']
    search_fields = ['student__name', 'student__username', 'exercise_choice_group__title']
    filter_horizontal = ['selected_exercises']
    readonly_fields = ['confirmed_at', 'created_at', 'updated_at']
    ordering = ['-confirmed_at']
    
    fieldsets = (
        (_('انتخاب'), {
            'fields': ('student', 'exercise_choice_group')
        }),
        (_('تمرین‌های انتخاب‌شده'), {
            'fields': ('selected_exercises',)
        }),
        (_('زمان‌ها'), {
            'fields': ('confirmed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_name(self, obj):
        """نام دانش‌آموز"""
        return obj.student.name or obj.student.username
    student_name.short_description = _('دانش‌آموز')
    
    def choice_group_title(self, obj):
        """عنوان گروه"""
        return obj.exercise_choice_group.title
    choice_group_title.short_description = _('گروه تمرین')
    
    def exercise_count(self, obj):
        """تعداد تمرین‌های انتخاب شده"""
        return obj.selected_exercises.count()
    exercise_count.short_description = _('تمرین‌های انتخاب‌شده')
