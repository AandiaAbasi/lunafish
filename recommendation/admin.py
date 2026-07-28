from urllib.parse import urlencode

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from recommendation.models import (
    EnglishPlacementAssessment,
    PsychologicalTest,
    StudentAnswer,
    StudentTestResponse,
    TestResult,
)
from recommendation.services.placement_service import sync_user_english_level
from recommendation.admin_result_renderer import render_placement_result


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    can_delete = False
    fields = ('question', 'selected_option', 'text_answer', 'answered_at')
    readonly_fields = fields
    ordering = ('question__order',)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PsychologicalTest)
class PsychologicalTestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'responses_count',
        'results_button',
        'edit_button',
        'view_button',
    )
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    list_display_links = None

    def add_view(self, request, form_url='', extra_context=None):
        return redirect(reverse('recommendation:test_create'))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        return redirect(reverse('recommendation:test_edit', args=[object_id]))

    def changelist_view(self, request, extra_context=None):
        if request.GET.get('add'):
            return redirect(reverse('recommendation:test_create'))
        return super().changelist_view(request, extra_context)

    @admin.display(description='شرکت‌کنندگان')
    def responses_count(self, obj):
        return obj.student_responses.count()

    @admin.display(description='نتایج')
    def results_button(self, obj):
        url = reverse('admin:recommendation_studenttestresponse_changelist')
        query = urlencode({'test__id__exact': obj.id})
        return format_html('<a class="button" href="{}?{}">نتایج دانش‌آموزان</a>', url, query)

    @admin.display(description='ویرایش')
    def edit_button(self, obj):
        url = reverse('recommendation:test_edit', args=[obj.id])
        return format_html('<a class="button" href="{}">ویرایش</a>', url)

    @admin.display(description='مشاهده')
    def view_button(self, obj):
        url = reverse('recommendation:test_detail', args=[obj.id])
        return format_html('<a class="button" href="{}">مشاهده</a>', url)


@admin.register(StudentTestResponse)
class StudentTestResponseAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_name',
        'test',
        'status',
        'current_suggested_level',
        'current_final_level',
        'started_at',
        'completed_at',
    )
    list_filter = ('status', 'test', 'test__test_type', 'completed_at')
    search_fields = ('user__name', 'test__title')
    raw_id_fields = ('user', 'test')
    readonly_fields = (
        'started_at',
        'completed_at',
        'placement_result_preview',
        'placement_history_link',
    )
    inlines = (StudentAnswerInline,)
    actions = ('recalculate_selected_results',)
    list_select_related = ('user', 'test')

    @admin.display(description='دانش‌آموز')
    def student_name(self, obj):
        return getattr(obj.user, 'name', None) or str(obj.user)

    def _latest_assessment(self, obj):
        return obj.placement_assessments.order_by('-created_at').first()

    @admin.display(description='سطح پیشنهادی')
    def current_suggested_level(self, obj):
        assessment = self._latest_assessment(obj)
        return assessment.get_suggested_level_display() if assessment and assessment.suggested_level else '-'

    @admin.display(description='سطح نهایی')
    def current_final_level(self, obj):
        assessment = self._latest_assessment(obj)
        return assessment.get_final_level_display() if assessment and assessment.final_level else '-'

    @admin.display(description='نتیجه تعیین سطح')
    def placement_result_preview(self, obj):
        result = getattr(obj, 'result', None)
        if not result:
            return format_html(
                '<div style="padding:12px;border:1px solid #fde68a;background:#fffbeb;border-radius:10px;">'
                'هنوز نتیجه‌ای برای این پاسخ محاسبه نشده است.'
                '</div>'
            )

        latest = self._latest_assessment(obj)
        final_level = latest.final_level if latest else None
        return render_placement_result(
            raw_scores=result.raw_scores,
            summary=result.summary,
            final_level=final_level,
        )

    @admin.display(description='تاریخچه تعیین سطح')
    def placement_history_link(self, obj):
        url = reverse('admin:recommendation_englishplacementassessment_changelist')
        query = urlencode({'response__id__exact': obj.id})
        return format_html('<a class="button" href="{}?{}">مشاهده تاریخچه</a>', url, query)

    @admin.action(description='محاسبه مجدد نتیجه‌های انتخاب‌شده')
    def recalculate_selected_results(self, request, queryset):
        success = 0
        for response in queryset:
            if response.calculate_result():
                success += 1
        self.message_user(request, f'{success} نتیجه محاسبه شد.', messages.SUCCESS)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_name', 'test_name', 'suggested_level', 'calculated_at')
    list_filter = ('response__test', 'response__test__test_type', 'calculated_at')
    search_fields = ('response__user__name', 'response__test__title')
    raw_id_fields = ('response',)
    fields = ('response', 'calculated_at', 'placement_result_preview')
    readonly_fields = ('response', 'calculated_at', 'placement_result_preview')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='دانش‌آموز')
    def student_name(self, obj):
        return getattr(obj.response.user, 'name', None) or str(obj.response.user)

    @admin.display(description='آزمون')
    def test_name(self, obj):
        return obj.response.test

    @admin.display(description='سطح پیشنهادی')
    def suggested_level(self, obj):
        return (obj.summary or {}).get('suggested_level', '-')

    @admin.display(description='نتیجه تعیین سطح')
    def placement_result_preview(self, obj):
        latest = obj.response.placement_assessments.order_by('-created_at').first()
        final_level = latest.final_level if latest else None
        return render_placement_result(
            raw_scores=obj.raw_scores,
            summary=obj.summary,
            final_level=final_level,
        )


@admin.register(EnglishPlacementAssessment)
class EnglishPlacementAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_name',
        'test',
        'suggested_level_display',
        'final_level_display',
        'status',
        'source',
        'assessed_by',
        'response_completed_at',
        'assessed_at',
    )
    list_filter = (
        'status',
        'source',
        'suggested_level',
        'final_level',
        'test',
        'response_completed_at',
    )
    search_fields = ('student__name', 'test__title', 'note')
    raw_id_fields = ('student', 'response', 'test', 'assessed_by')
    readonly_fields = (
        'suggested_level',
        'assessed_by',
        'assessed_at',
        'response_completed_at',
        'placement_result_preview',
    )
    actions = ('confirm_suggested_level',)
    date_hierarchy = 'created_at'
    list_select_related = ('student', 'test', 'assessed_by')

    fieldsets = (
        ('دانش‌آموز و آزمون', {
            'fields': ('student', 'test', 'response', 'source'),
        }),
        ('تعیین سطح', {
            'fields': ('suggested_level', 'final_level', 'status', 'note'),
        }),
        ('اطلاعات بررسی', {
            'fields': ('assessed_by', 'assessed_at', 'response_completed_at'),
        }),
        ('Snapshot نتیجه آزمون', {
            'fields': ('placement_result_preview',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='دانش‌آموز')
    def student_name(self, obj):
        return getattr(obj.student, 'name', None) or str(obj.student)

    @admin.display(description='سطح پیشنهادی')
    def suggested_level_display(self, obj):
        return obj.get_suggested_level_display() if obj.suggested_level else '-'

    @admin.display(description='سطح نهایی')
    def final_level_display(self, obj):
        return obj.get_final_level_display() if obj.final_level else '-'

    @admin.display(description='نتیجه ثبت‌شده آزمون')
    def placement_result_preview(self, obj):
        if not obj.raw_scores_snapshot and not obj.result_summary_snapshot:
            return format_html(
                '<div style="padding:12px;border:1px solid #e5e7eb;background:#f8fafc;border-radius:10px;">'
                'این تعیین سطح به‌صورت دستی ثبت شده و نتیجه آزمون ندارد.'
                '</div>'
            )

        return render_placement_result(
            raw_scores=obj.raw_scores_snapshot,
            summary=obj.result_summary_snapshot,
            final_level=obj.final_level,
        )

    def save_model(self, request, obj, form, change):
        if obj.response_id:
            obj.student = obj.response.user
            obj.test = obj.response.test
            if not obj.suggested_level:
                result = getattr(obj.response, 'result', None)
                if result:
                    obj.suggested_level = (result.summary or {}).get('suggested_level')
                    obj.raw_scores_snapshot = dict(result.raw_scores or {})
                    obj.result_summary_snapshot = dict(result.summary or {})
                    obj.response_completed_at = obj.response.completed_at
        elif obj.source == obj.Source.TEST:
            obj.source = obj.Source.ADMIN

        if obj.final_level:
            obj.assessed_by = request.user
            obj.assessed_at = timezone.now()
            obj.status = (
                obj.Status.CONFIRMED
                if obj.final_level == obj.suggested_level
                else obj.Status.OVERRIDDEN
            )

        super().save_model(request, obj, form, change)

        if obj.final_level:
            synced = sync_user_english_level(obj, request.user)
            if not synced:
                self.message_user(
                    request,
                    'سطح نهایی ذخیره شد؛ اما فیلدهای تعیین سطح هنوز به مدل User اضافه نشده‌اند.',
                    messages.WARNING,
                )

    @admin.action(description='تأیید سطح پیشنهادی سیستم')
    def confirm_suggested_level(self, request, queryset):
        confirmed = 0
        not_synced = 0
        for assessment in queryset.select_related('student'):
            if not assessment.suggested_level:
                continue

            assessment.final_level = assessment.suggested_level
            assessment.status = assessment.Status.CONFIRMED
            assessment.assessed_by = request.user
            assessment.assessed_at = timezone.now()
            assessment.save(update_fields=[
                'final_level',
                'status',
                'assessed_by',
                'assessed_at',
                'updated_at',
            ])
            if not sync_user_english_level(assessment, request.user):
                not_synced += 1
            confirmed += 1

        message = f'{confirmed} تعیین سطح تأیید شد.'
        if not_synced:
            message += f' سطح {not_synced} دانش‌آموز به User منتقل نشد چون فیلدهای User هنوز اضافه نشده‌اند.'
        self.message_user(request, message, messages.SUCCESS if not not_synced else messages.WARNING)
