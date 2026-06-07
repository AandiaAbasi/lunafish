from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import translation
import jdatetime
from django.utils.safestring import mark_safe

# Import models
from .models import (
    Field,
    FieldDetail,
    CategoryField,
    Order,
    OrderDetail,
    StudentRating,
    StudentMedal
)


def format_date(dt):
    """تاریخ را بر اساس زبان فعال فرمت می‌کند"""
    if not dt:
        return '-'
    
    current_lang = translation.get_language()
    
    if current_lang == 'fa':
        # تبدیل به تاریخ شمسی
        jdate = jdatetime.datetime.fromgregorian(datetime=dt)
        return jdate.strftime('%Y/%m/%d %H:%M')
    else:
        # تاریخ میلادی
        return dt.strftime('%Y-%m-%d %H:%M')


class BilingualModelAdmin(admin.ModelAdmin):
    """Base class برای مدل‌های دوزبانه - فیلدهای انگلیسی را خودکار readonly می‌کند"""
    
    def get_readonly_fields(self, request, obj=None):
        """فیلدهای انگلیسی را خودکار readonly کن"""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # فقط هنگام ویرایش
            # تمام فیلدهای با پسوند _en را readonly کن
            for field in self.model._meta.get_fields():
                if hasattr(field, 'name') and field.name.endswith('_en'):
                    if field.name not in readonly:
                        readonly.append(field.name)
        return readonly


# ===== Inline Classes =====

class FieldDetailInline(admin.TabularInline):
    model = FieldDetail
    extra = 0
    can_delete = False
    fields = ['title', 'is_correct_display', 'sort', 'image_path']
    readonly_fields = ['title', 'is_correct_display', 'sort', 'image_path']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def is_correct_display(self, obj):
        if obj.is_correct == -1:
            return format_html('<span style="color:#6c757d">-</span>')
        color = '#28a745' if obj.is_correct == 1 else '#dc3545'
        text = _('✓') if obj.is_correct == 1 else _('✗')
        return format_html('<span style="background-color:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>', color, text)
    is_correct_display.short_description = _('درستی')


class CategoryFieldInline(admin.TabularInline):
    model = CategoryField
    extra = 0
    can_delete = False
    fields = ['teachingsubject', 'step', 'sort', 'type_badge', 'is_conditional']
    readonly_fields = ['teachingsubject', 'step', 'sort', 'type_badge', 'is_conditional']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def type_badge(self, obj):
        colors = {
            'input': '#007bff',
            'checkbox': '#28a745',
            'radioButton': '#ffc107',
        }
        labels = {
            'input': _('تایپی'),
            'checkbox': _('چند گزینه'),
            'radioButton': _('تک گزینه'),
        }
        color = colors.get(obj.type, '#6c757d')
        label = labels.get(obj.type, obj.type)
        return format_html('<span style="background-color:{}; color:white; padding:2px 6px; border-radius:3px; font-size:11px;">{}</span>', color, label)
    type_badge.short_description = _('نوع')


class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0
    can_delete = False
    fields = ['field', 'value_display', 'score_badge']
    readonly_fields = ['field', 'value_display', 'score_badge']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def value_display(self, obj):
        if obj.value:
            return obj.value[:30] + '...' if len(obj.value) > 30 else obj.value
        return '-'
    value_display.short_description = _('پاسخ')
    
    def score_badge(self, obj):
        color = '#28a745' if obj.score > 0 else '#dc3545'
        return format_html(
            '<span style="background-color:{}; color:white; padding:2px 6px; border-radius:3px;">{}</span>',
            color, obj.score
        )
    score_badge.short_description = _('امتیاز')


class StudentRatingInline(admin.StackedInline):
    model = StudentRating
    extra = 0
    can_delete = False
    fields = ['teacher', 'rating_type', 'score', 'stars_display', 'comment']
    readonly_fields = ['teacher', 'rating_type', 'score', 'stars_display', 'comment']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def stars_display(self, obj):
        stars = '⭐' * obj.stars
        return format_html('<span style="font-size:16px">{}</span>', stars)
    stars_display.short_description = _('ستاره')


class StudentMedalInline(admin.TabularInline):
    model = StudentMedal
    extra = 0
    can_delete = False
    fields = ['teacher', 'medal_type_badge', 'title', 'description']
    readonly_fields = ['teacher', 'medal_type_badge', 'title', 'description']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def medal_type_badge(self, obj):
        icons = {
            'gold': '🥇',
            'silver': '🥈',
            'bronze': '🥉',
            'star': '⭐',
            'heart': '❤️',
            'trophy': '🏆',
            'certificate': '📜',
            'badge': '🎖️',
            'achievement': '🏅',
            'custom': '🎁'
        }
        icon = icons.get(obj.medal_type, '🏅')
        label = obj.get_medal_type_display()
        return format_html('{} {}', icon, label)
    medal_type_badge.short_description = _('نوع مدال')


# ===== Field Admin (سؤال) =====
@admin.register(Field)
class FieldAdmin(BilingualModelAdmin):
    list_display = ['title', 'teacher_name', 'type_badge', 'is_required_badge', 'sort', 'created_at_display', 'detail_button']
    list_filter = ['type', 'is_required']
    search_fields = ['title', 'des', 'teacher__name', 'teacher__username']
    readonly_fields = ['teacher', 'title', 'sort', 'type', 'is_required', 'image_path', 'audio_path', 'video_path', 'icon_name', 'guide', 'des', 'created_at_display', 'updated_at_display']
    inlines = [FieldDetailInline, CategoryFieldInline]
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('teacher', 'title', 'type', 'sort')
        }),
        (_('نیاز'), {
            'fields': ('is_required',)
        }),
        (_('توصیف'), {
            'fields': ('des', 'guide')
        }),
        (_('رسانه'), {
            'fields': ('image_path', 'audio_path', 'video_path', 'icon_name')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def teacher_name(self, obj):
        return obj.teacher.name or obj.teacher.username
    teacher_name.short_description = _('معلم')
    
    def type_badge(self, obj):
        colors = {
            'input': '#007bff',
            'checkbox': '#28a745',
            'radioButton': '#ffc107',
        }
        labels = {
            'input': _('تایپی'),
            'checkbox': _('چند گزینه ای'),
            'radioButton': _('تک گزینه ای'),
        }
        color = colors.get(obj.type, '#6c757d')
        label = labels.get(obj.type, obj.type)
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, label)
    type_badge.short_description = _('نوع سؤال')
    
    def is_required_badge(self, obj):
        if obj.is_required is None:
            return '-'
        color = '#28a745' if obj.is_required else '#dc3545'
        text = _('الزامی') if obj.is_required else _('اختیاری')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_required_badge.short_description = _('الزامی/اختیاری')
    
    def created_at_display(self, obj):
        return format_date(obj.created_at)
    created_at_display.short_description = _('تاریخ ایجاد')
    
    def detail_button(self, obj):
        url = reverse('admin:exercise_field_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="padding:5px 10px; background:#007bff; color:white; text-decoration:none; border-radius:3px;">جزئیات</a>',
            url
        )
    detail_button.short_description = _('عملیات')


# ===== FieldDetail Admin (گزینه) =====
@admin.register(FieldDetail)
class FieldDetailAdmin(admin.ModelAdmin):
    list_display = ['field', 'title', 'is_correct_display', 'sort', 'created_at_display', 'detail_button']
    list_filter = ['is_correct', ]
    search_fields = ['title', 'field__title']
    readonly_fields = ['field', 'title', 'second_title', 'is_required', 'image_path', 'is_correct', 'correct_answer', 'guide', 'des', 'sort', 'created_at_display', 'updated_at_display']
    
    fieldsets = (
        (_('سؤال'), {
            'fields': ('field',)
        }),
        (_('عنوان و توصیف'), {
            'fields': ('title', 'second_title', 'des')
        }),
        (_('درستی'), {
            'fields': ('is_correct', 'correct_answer')
        }),
        (_('رسانه'), {
            'fields': ('image_path',)
        }),
        (_('راهنمایی'), {
            'fields': ('guide', 'is_required')
        }),
        (_('ترتیب'), {
            'fields': ('sort',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def is_correct_display(self, obj):
        if obj.is_correct == -1:
            return mark_safe('<span style="color:#6c757d">-</span>')
        color = '#28a745' if obj.is_correct == 1 else '#dc3545'
        text = _('✓ صحیح') if obj.is_correct == 1 else _('✗ غلط')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_correct_display.short_description = _('درستی')
    
    def created_at_display(self, obj):
        return format_date(obj.created_at)
    created_at_display.short_description = _('تاریخ ایجاد')
    
    def detail_button(self, obj):
        url = reverse('admin:exercise_fielddetail_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="padding:5px 10px; background:#007bff; color:white; text-decoration:none; border-radius:3px;">جزئیات</a>',
            url
        )
    detail_button.short_description = _('عملیات')


# ===== CategoryField Admin (آزمون) =====
@admin.register(CategoryField)
class CategoryFieldAdmin(admin.ModelAdmin):
    list_display = ['teachingsubject', 'field', 'step', 'sort', 'type_badge', 'is_conditional_badge', 'created_at_display', 'detail_button']
    list_filter = ['teachingsubject', 'is_conditional', 'type']
    search_fields = ['field__title', 'teachingsubject__title']
    readonly_fields = ['teachingsubject', 'field', 'step', 'sort', 'type', 'is_conditional', 'created_at_display', 'updated_at_display']
    
    fieldsets = (
        (_('کلاس و سؤال'), {
            'fields': ('teachingsubject', 'field')
        }),
        (_('ترتیب'), {
            'fields': ('step', 'sort')
        }),
        (_('شرط'), {
            'fields': ('type', 'is_conditional')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def type_badge(self, obj):
        colors = {
            'input': '#007bff',
            'checkbox': '#28a745',
            'radioButton': '#ffc107',
        }
        labels = {
            'input': _('تایپی'),
            'checkbox': _('چند گزینه ای'),
            'radioButton': _('تک گزینه ای'),
        }
        color = colors.get(obj.type, '#6c757d')
        label = labels.get(obj.type, obj.type)
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, label)
    type_badge.short_description = _('نوع')
    
    def is_conditional_badge(self, obj):
        color = '#ffc107' if obj.is_conditional else '#28a745'
        text = _('شرطی') if obj.is_conditional else _('عادی')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_conditional_badge.short_description = _('شرط')
    
    def created_at_display(self, obj):
        return format_date(obj.created_at)
    created_at_display.short_description = _('تاریخ ایجاد')
    
    def detail_button(self, obj):
        url = reverse('admin:exercise_categoryfield_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="padding:5px 10px; background:#007bff; color:white; text-decoration:none; border-radius:3px;">جزئیات</a>',
            url
        )
    detail_button.short_description = _('عملیات')


# ===== Order Admin (تلاش) =====
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_name', 'teachingsubject', 'score_display', 'progress_badge', 'rating_display', 'medals_display', 'created_at_display', 'detail_button']
    list_filter = ['teachingsubject',]
    search_fields = ['user__name', 'user__username', 'teachingsubject__title']
    readonly_fields = ['user', 'teachingsubject', 'score', 'correct', 'incorrect', 'score_display', 'progress_display', 'rating_info', 'medals_info', 'created_at_display', 'updated_at_display']
    inlines = [OrderDetailInline, StudentRatingInline, StudentMedalInline]
    
    fieldsets = (
        (_('دانش‌آموز'), {
            'fields': ('user',)
        }),
        (_('کلاس'), {
            'fields': ('teachingsubject',)
        }),
        (_('نتایج'), {
            'fields': ('score_display', 'correct', 'incorrect', 'progress_display')
        }),
        (_('امتیاز و مدال'), {
            'fields': ('rating_info', 'medals_info')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def user_name(self, obj):
        return obj.user.name or obj.user.username
    user_name.short_description = _('دانش‌آموز')
    
    def score_display(self, obj):
        return format_html('<strong style="color:#007bff; font-size:16px">{}</strong>', obj.score)
    score_display.short_description = _('امتیاز')
    
    def progress_display(self, obj):
        total = obj.correct + obj.incorrect
        if total == 0:
            return '-'
        percentage = (obj.correct / total) * 100
        color = '#28a745' if percentage >= 70 else '#ffc107' if percentage >= 50 else '#dc3545'
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{:.0f}% ({}/{})</span>',
            color, percentage, obj.correct, total
        )
    progress_display.short_description = _('پیشرفت')
    
    def progress_badge(self, obj):
        total = obj.correct + obj.incorrect
        if total == 0:
            return '-'
        percentage = (obj.correct / total) * 100
        color = '#28a745' if percentage >= 70 else '#ffc107' if percentage >= 50 else '#dc3545'
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{:.0f}%</span>',
            color, percentage
        )
    progress_badge.short_description = _('درصد')
    
    def rating_display(self, obj):
        if obj.has_rating():
            rating = obj.get_rating()
            stars = '⭐' * rating.stars
            return format_html(
                '<span style="color:#ffc107">{}</span> <span style="color:#007bff">{}/100</span>',
                stars, rating.score
            )
        return '-'
    rating_display.short_description = _('امتیاز معلم')
    
    def medals_display(self, obj):
        if obj.has_medals():
            count = obj.medals.count()
            return format_html(
                '<span style="background-color:#ffc107; color:white; padding:3px 8px; border-radius:3px;">🏅 {}</span>',
                count
            )
        return '-'
    medals_display.short_description = _('مدال‌ها')
    
    def rating_info(self, obj):
        stats = obj.get_rating_stats()
        if stats:
            stars = '⭐' * stats['stars']
            html = f"""
            <div style="padding:10px; background:#f8f9fa; border-radius:5px;">
                <p><strong>امتیاز:</strong> {stats['score']}/100</p>
                <p><strong>ستاره:</strong> {stars}</p>
                <p><strong>معلم:</strong> {stats['teacher_name']}</p>
                <p><strong>نوع:</strong> {stats['rating_type']}</p>
                {f"<p><strong>نظر:</strong> {stats['comment']}</p>" if stats['comment'] else ""}
            </div>
            """
            return mark_safe(html)
        return mark_safe('<span style="color:#6c757d">امتیازی ثبت نشده</span>')
    rating_info.short_description = _('جزئیات امتیاز')
    
    def medals_info(self, obj):
        medals = obj.get_medals()
        if medals.exists():
            html = '<div style="padding:10px; background:#f8f9fa; border-radius:5px;">'
            for medal in medals:
                html += f'<p>🏅 <strong>{medal.title}</strong> ({medal.get_medal_type_display()})</p>'
            html += '</div>'
            return mark_safe(html)
        return mark_safe('<span style="color:#6c757d">مدالی ثبت نشده</span>')
    medals_info.short_description = _('جزئیات مدال‌ها')
    
    def created_at_display(self, obj):
        return format_date(obj.created_at)
    created_at_display.short_description = _('تاریخ ایجاد')
    
    def detail_button(self, obj):
        url = reverse('admin:exercise_order_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="padding:5px 10px; background:#007bff; color:white; text-decoration:none; border-radius:3px;">جزئیات</a>',
            url
        )
    detail_button.short_description = _('عملیات')


# ===== OrderDetail Admin (پاسخ) =====
@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'field_title', 'value_display', 'score_badge', 'created_at_display', 'detail_button']
    list_filter = ['order__teachingsubject',]
    search_fields = ['field__title', 'order__user__name', 'value']
    readonly_fields = ['order', 'field', 'field_detail', 'value', 'score', 'created_at_display', 'updated_at_display']
    
    fieldsets = (
        (_('تلاش'), {
            'fields': ('order',)
        }),
        (_('سؤال'), {
            'fields': ('field',)
        }),
        (_('پاسخ'), {
            'fields': ('field_detail', 'value')
        }),
        (_('نتیجه'), {
            'fields': ('score',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def order_id(self, obj):
        return f"#{obj.order.id}"
    order_id.short_description = _('تلاش')
    
    def field_title(self, obj):
        return obj.field.title
    field_title.short_description = _('سؤال')
    
    def value_display(self, obj):
        if obj.value:
            return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
        return '-'
    value_display.short_description = _('پاسخ')
    
    def score_badge(self, obj):
        color = '#28a745' if obj.score > 0 else '#dc3545'
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color, obj.score
        )
    score_badge.short_description = _('امتیاز')
    
    def created_at_display(self, obj):
        return format_date(obj.created_at)
    created_at_display.short_description = _('تاریخ ایجاد')
    
    def detail_button(self, obj):
        url = reverse('admin:exercise_orderdetail_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="padding:5px 10px; background:#007bff; color:white; text-decoration:none; border-radius:3px;">جزئیات</a>',
            url
        )
    detail_button.short_description = _('عملیات')


# ===== StudentRating Admin (امتیاز دانش‌آموز) =====
@admin.register(StudentRating)
class StudentRatingAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'teacher_name', 'teachingsubject', 'score_display', 'stars_display', 'rating_type', 'created_at_display', 'detail_button']
    list_filter = ['rating_type', 'teachingsubject']
    search_fields = ['student__name', 'student__username', 'teacher__name', 'teacher__username', 'teachingsubject__title']
    readonly_fields = ['teacher', 'student', 'teachingsubject', 'order', 'rating_type', 'score', 'stars', 'comment', 'created_at_display', 'updated_at_display']
    
    fieldsets = (
        (_('معلم و دانش‌آموز'), {
            'fields': ('teacher', 'student')
        }),
        (_('کلاس و تمرین'), {
            'fields': ('teachingsubject', 'order')
        }),
        (_('امتیاز'), {
            'fields': ('rating_type', 'score', 'stars')
        }),
        (_('نظر'), {
            'fields': ('comment',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def student_name(self, obj):
        return obj.student.name or obj.student.username
    student_name.short_description = _('دانش‌آموز')
    
    def teacher_name(self, obj):
        return obj.teacher.name or obj.teacher.username
    teacher_name.short_description = _('معلم')
    
    def score_display(self, obj):
        color = '#28a745' if obj.score >= 70 else '#ffc107' if obj.score >= 50 else '#dc3545'
        return format_html(
            '<span style="background-color:{}; color:white; padding:5px 10px; border-radius:3px; font-weight:bold;">{}/100</span>',
            color, obj.score
        )
    score_display.short_description = _('امتیاز')
    
    def stars_display(self, obj):
        stars = '⭐' * obj.stars
        return format_html('<span style="font-size:16px">{}</span>', stars)
    stars_display.short_description = _('ستاره')
    
    def created_at_display(self, obj):
        return format_date(obj.created_at)
    created_at_display.short_description = _('تاریخ ایجاد')
    
    def detail_button(self, obj):
        url = reverse('admin:exercise_studentrating_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="padding:5px 10px; background:#007bff; color:white; text-decoration:none; border-radius:3px;">جزئیات</a>',
            url
        )
    detail_button.short_description = _('عملیات')



# ===== StudentMedal Admin (مدال دانش‌آموز) =====
@admin.register(StudentMedal)
class StudentMedalAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'teacher_name', 'title', 'medal_type_badge', 'teachingsubject', 'created_at_display', 'detail_button']
    list_filter = ['medal_type', 'teachingsubject']
    search_fields = ['student__name', 'student__username', 'teacher__name', 'teacher__username', 'title', 'description']
    readonly_fields = ['teacher', 'student', 'teachingsubject', 'order', 'medal_type', 'title', 'description', 'icon_url', 'created_at_display', 'updated_at_display']
    
    fieldsets = (
        (_('معلم و دانش‌آموز'), {
            'fields': ('teacher', 'student')
        }),
        (_('کلاس و تمرین'), {
            'fields': ('teachingsubject', 'order')
        }),
        (_('مدال'), {
            'fields': ('medal_type', 'title', 'description', 'icon_url')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def student_name(self, obj):
        return obj.student.name or obj.student.username
    student_name.short_description = _('دانش‌آموز')
    
    def teacher_name(self, obj):
        return obj.teacher.name or obj.teacher.username
    teacher_name.short_description = _('معلم')
    
    def medal_type_badge(self, obj):
        colors = {
            'gold': '#FFD700',
            'silver': '#C0C0C0',
            'bronze': '#CD7F32',
            'star': '#ffc107',
            'heart': '#dc3545',
            'trophy': '#28a745',
            'certificate': '#007bff',
            'badge': '#6c757d',
            'achievement': '#17a2b8',
            'custom': '#e83e8c'
        }
        icons = {
            'gold': '🥇',
            'silver': '🥈',
            'bronze': '🥉',
            'star': '⭐',
            'heart': '❤️',
            'trophy': '🏆',
            'certificate': '📜',
            'badge': '🎖️',
            'achievement': '🏅',
            'custom': '🎁'
        }
        color = colors.get(obj.medal_type, '#6c757d')
        icon = icons.get(obj.medal_type, '🏅')
        label = obj.get_medal_type_display()
        return format_html(
            '<span style="background-color:{}; color:white; padding:5px 10px; border-radius:3px;">{} {}</span>',
            color, icon, label
        )
    medal_type_badge.short_description = _('نوع مدال')
    
    def created_at_display(self, obj):
        return format_date(obj.created_at)
    created_at_display.short_description = _('تاریخ ایجاد')
    
    def detail_button(self, obj):
        url = reverse('admin:exercise_studentmedal_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="padding:5px 10px; background:#007bff; color:white; text-decoration:none; border-radius:3px;">جزئیات</a>',
            url
        )
    detail_button.short_description = _('عملیات')
