from urllib.parse import urlencode

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from recommendation.admin_result_renderer import render_placement_result
from recommendation.admin_utils import format_jalali_datetime
from recommendation.models import (
    EnglishPlacementAssessment,
    PsychologicalTest,
    StudentAnswer,
    StudentTestResponse,
    TestResult,
)
from recommendation.services.placement_service import sync_user_english_level


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    can_delete = False
    fields = ('question', 'selected_option', 'text_answer', 'answered_at_jalali')
    readonly_fields = fields
    ordering = ('question__order',)

    @admin.display(description=_('زمان پاسخ'), ordering='answered_at')
    def answered_at_jalali(self, obj):
        return format_jalali_datetime(getattr(obj, 'answered_at', None))

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

    @admin.display(description=_('شرکت‌کنندگان'))
    def responses_count(self, obj):
        return obj.student_responses.count()

    @admin.display(description=_('نتایج'))
    def results_button(self, obj):
        url = reverse('admin:recommendation_studenttestresponse_changelist')
        query = urlencode({'test__id__exact': obj.id})
        return format_html(
            '<a class="button" href="{}?{}">{}</a>',
            url,
            query,
            _('نتایج تعیین سطح دانش‌آموزان'),
        )

    @admin.display(description=_('ویرایش'))
    def edit_button(self, obj):
        url = reverse('recommendation:test_edit', args=[obj.id])
        return format_html('<a class="button" href="{}">{}</a>', url, _('ویرایش'))

    @admin.display(description=_('مشاهده'))
    def view_button(self, obj):
        url = reverse('recommendation:test_detail', args=[obj.id])
        return format_html('<a class="button" href="{}">{}</a>', url, _('مشاهده'))


@admin.register(StudentTestResponse)
class StudentTestResponseAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_name',
        'test',
        'status',
        'current_suggested_level',
        'current_final_level',
        'started_at_jalali',
        'completed_at_jalali',
    )
    list_filter = ('status', 'test', 'completed_at')
    search_fields = ('user__name', 'user__username', 'test__title')
    raw_id_fields = ('user', 'test')
    readonly_fields = (
        'started_at_jalali',
        'completed_at_jalali',
        'placement_result_preview',
        'placement_history_link',
    )
    fieldsets = (
        (_('اطلاعات دانش‌آموز و آزمون تعیین سطح'), {
            'fields': ('user', 'test', 'status'),
        }),
        (_('زمان‌بندی آزمون'), {
            'fields': ('started_at_jalali', 'completed_at_jalali'),
        }),
        (_('نتیجه تعیین سطح زبان انگلیسی'), {
            'fields': ('placement_result_preview', 'placement_history_link'),
        }),
    )
    inlines = (StudentAnswerInline,)
    actions = ('recalculate_selected_results',)
    list_select_related = ('user', 'test')

    def has_add_permission(self, request):
        return False

    @admin.display(description=_('دانش‌آموز'))
    def student_name(self, obj):
        return getattr(obj.user, 'name', None) or str(obj.user)

    def _latest_assessment(self, obj):
        return obj.placement_assessments.order_by('-created_at').first()

    @admin.display(description=_('سطح پیشنهادی'))
    def current_suggested_level(self, obj):
        assessment = self._latest_assessment(obj)
        return assessment.get_suggested_level_display() if assessment and assessment.suggested_level else '-'

    @admin.display(description=_('سطح نهایی'))
    def current_final_level(self, obj):
        assessment = self._latest_assessment(obj)
        return assessment.get_final_level_display() if assessment and assessment.final_level else '-'

    @admin.display(description=_('زمان شروع'), ordering='started_at')
    def started_at_jalali(self, obj):
        return format_jalali_datetime(getattr(obj, 'started_at', None))

    @admin.display(description=_('زمان تکمیل'), ordering='completed_at')
    def completed_at_jalali(self, obj):
        return format_jalali_datetime(getattr(obj, 'completed_at', None))

    @admin.display(description=_('نتیجه تعیین سطح'))
    def placement_result_preview(self, obj):
        result = getattr(obj, 'result', None)
        if not result:
            return format_html(
                '<div style="padding:12px;border:1px solid #fde68a;background:#fffbeb;border-radius:10px;">{}</div>',
                _('هنوز نتیجه‌ای برای این پاسخ محاسبه نشده است.'),
            )

        latest = self._latest_assessment(obj)
        final_level = latest.final_level if latest else None
        return render_placement_result(
            raw_scores=result.raw_scores,
            summary=result.summary,
            final_level=final_level,
        )

    @admin.display(description=_('تاریخچه تعیین سطح'))
    def placement_history_link(self, obj):
        url = reverse('admin:recommendation_englishplacementassessment_changelist')
        query = urlencode({'response__id__exact': obj.id})
        return format_html(
            '<a class="button" href="{}?{}">{}</a>',
            url,
            query,
            _('مشاهده تاریخچه تعیین سطح'),
        )

    @admin.action(description=_('محاسبه مجدد نتیجه‌های انتخاب‌شده'))
    def recalculate_selected_results(self, request, queryset):
        success = 0
        for response in queryset:
            if response.calculate_result():
                success += 1
        self.message_user(
            request,
            _('%(count)s نتیجه تعیین سطح مجدداً محاسبه شد.') % {'count': success},
            messages.SUCCESS,
        )


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_name', 'test_name', 'suggested_level', 'calculated_at_jalali')
    list_filter = ('response__test', 'calculated_at')
    search_fields = ('response__user__name', 'response__user__username', 'response__test__title')
    raw_id_fields = ('response',)
    fields = ('response', 'calculated_at_jalali', 'placement_result_preview')
    readonly_fields = ('response', 'calculated_at_jalali', 'placement_result_preview')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_('دانش‌آموز'))
    def student_name(self, obj):
        return getattr(obj.response.user, 'name', None) or str(obj.response.user)

    @admin.display(description=_('آزمون تعیین سطح'))
    def test_name(self, obj):
        return obj.response.test

    @admin.display(description=_('سطح پیشنهادی'))
    def suggested_level(self, obj):
        return (obj.summary or {}).get('suggested_level', '-')

    @admin.display(description=_('زمان محاسبه'), ordering='calculated_at')
    def calculated_at_jalali(self, obj):
        return format_jalali_datetime(getattr(obj, 'calculated_at', None))

    @admin.display(description=_('نتیجه تعیین سطح'))
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
    # list_display و سایر تنظیمات فعلی خودت...

    def save_model(self, request, obj, form, change):
        if obj.final_level:
            obj.status = EnglishPlacementAssessment.Status.CONFIRMED
            obj.source = EnglishPlacementAssessment.Source.ADMIN
            obj.assessed_by = request.user
            obj.assessed_at = timezone.now()

        super().save_model(request, obj, form, change)

        if obj.final_level:
            sync_user_english_level(obj)