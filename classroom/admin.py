from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import (
    TeacherAvailability, TeachingSubject, ClassBooking,
    TeacherWallet, ClassRevenue, WithdrawalRequest, WalletTransaction,
    StudentTransaction, PlatformSettings, Attendance, SupportMessage, SupportMessageAttachment, CourseEnrollment, Course
)
import jdatetime
from datetime import datetime
import csv
from io import StringIO
import json
from django.utils.translation import get_language
from django.utils.safestring import mark_safe
from account.models import User 


def format_date(date_obj):
    """تبدیل تاریخ به فرمت مناسب بر اساس زبان فعال"""
    if not date_obj:
        return '-'
    
    current_language = get_language()
    
    if current_language == 'fa':
        # اگر date_obj فقط date است، به datetime تبدیل کن
        if not isinstance(date_obj, datetime):
            date_obj = datetime.combine(date_obj, datetime.min.time())
        
        jalali_date = jdatetime.datetime.fromgregorian(datetime=date_obj)
        return jalali_date.strftime('%Y/%m/%d %H:%M')
    else:
        if isinstance(date_obj, datetime):
            return date_obj.strftime('%Y-%m-%d %H:%M')
        else:
            return date_obj.strftime('%Y-%m-%d')
        

def get_jalali_date(date_obj):
    """تبدیل تاریخ میلادی به شمسی"""
    if not date_obj:
        return '-'
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    jalali = jdatetime.datetime.fromgregorian(datetime=datetime.combine(date_obj, datetime.min.time()))
    return jalali.strftime('%Y/%m/%d')


class BilingualModelAdmin(admin.ModelAdmin):
    """Base class برای مدل‌های دوزبانه - فیلدهای انگلیسی را خودکار readonly می‌کند"""
    
    def get_readonly_fields(self, request, obj=None):
        """فیلدهای انگلیسی را خودکار readonly کن"""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # فقط هنگام ویرایش
            # تمام فیلدهای با پسوند _en را readonly کن
            for field in self.model._meta.get_fields():
                if field.name.endswith('_en'):
                    if field.name not in readonly:
                        readonly.append(field.name)
        return readonly


# ===== TeacherAvailability Admin =====
@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'jalali_date', 'start_time', 'end_time', 'price', 'discount_price', 'is_available_badge', 'is_booked_badge']
    list_filter = ['teacher', 'date', 'is_available', 'is_booked']
    search_fields = ['teacher__name', 'teacher__username']
    ordering = ['-date', 'start_time']
    
    # تمامی فیلدها به عنوان readonly
    readonly_fields = ['teacher', 'date', 'jalali_date_display', 'start_time', 'end_time', 'price', 'discount_price', 'is_available', 'is_booked', 'notes', 'created_at_display', 'updated_at_display']
    
    # غیرفعال کردن قابلیت‌های افزودن، ویرایش، و حذف
    def has_add_permission(self, request, obj=None):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False
        
    def jalali_date(self, obj):
        return get_jalali_date(obj.date)
    jalali_date.short_description = _('تاریخ میلادی')
    
    def jalali_date_display(self, obj):
        return get_jalali_date(obj.date)
    jalali_date_display.short_description = _('تاریخ شمسی')
    
    def is_available_badge(self, obj):
        color = '#28a745' if obj.is_available else '#dc3545'
        text = _('دسترسی‌پذیر') if obj.is_available else _('غیردسترسی‌پذیر')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_available_badge.short_description = _('در دسترس')
    
    def is_booked_badge(self, obj):
        color = '#ff6b6b' if obj.is_booked else '#95e1d3'
        text = _('رزرو‌شده') if obj.is_booked else _('آزاد')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_booked_badge.short_description = _('وضعیت رزرو')
    
# @admin.register(TeacherAvailability)
# class TeacherAvailabilityAdmin(admin.ModelAdmin):
#     list_display = ['teacher', 'jalali_date', 'start_time', 'end_time', 'price', 'discount_price', 'is_available_badge', 'is_booked_badge']
#     list_filter = ['teacher', 'date', 'is_available', 'is_booked']
#     search_fields = ['teacher__name', 'teacher__username']
#     ordering = ['-date', 'start_time']
#     readonly_fields = ['created_at_display', 'updated_at_display', 'jalali_date_display']
#     actions = ['mark_available', 'mark_unavailable', 'bulk_delete']
#     change_list_template = 'admin/classroom/teacherAvailability/change_list.html'
    
#     fieldsets = (
#         (_('معلم و تاریخ'), {
#             'fields': ('teacher', 'date', 'jalali_date_display')
#         }),
#         (_('ساعات'), {
#             'fields': ('start_time', 'end_time')
#         }),
#         (_('قیمت‌گذاری'), {
#             'fields': ('price', 'discount_price')
#         }),
#         (_('وضعیت'), {
#             'fields': ('is_available', 'is_booked')
#         }),
#         (_('یادداشت'), {
#             'fields': ('notes',)
#         }),
#         (_('اطلاعات سیستم'), {
#             'fields': ('created_at_display', 'updated_at_display'),
#             'classes': ('collapse',)
#         }),
#     )
    
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('bulk-create/', self.admin_site.admin_view(self.bulk_create_view), name='classroom_availability_bulk_create'),
#         ]
#         return custom_urls + urls
    
#     def bulk_create_view(self, request):
#         """صفحه برای افزودن گروهی بازه‌های زمانی"""
#         if request.method == 'POST':
#             from django import forms
#             from account.models import User
            
#             teacher_id = request.POST.get('teacher')
#             sd_raw = request.POST.get('start_date')
#             ed_raw = request.POST.get('end_date')
#             daily_start_str = request.POST.get('daily_start_time')
#             daily_end_str = request.POST.get('daily_end_time')
#             session_minutes_str = request.POST.get('session_duration')
#             break_minutes_str = request.POST.get('break_duration')
#             price_str = request.POST.get('price')
#             discount_price_str = request.POST.get('discount_price')
            
#             # تبدیل تاریخ‌های شمسی به میلادی
#             try:
#                 start_date = jdatetime.datetime.strptime(sd_raw, '%Y/%m/%d').togregorian().date()
#                 end_date = jdatetime.datetime.strptime(ed_raw, '%Y/%m/%d').togregorian().date()
#             except Exception as e:
#                 messages.error(request, _('فرمت تاریخ نادرست است'))
#                 return render(request, 'admin/classroom/teacherAvailability/bulk_create.html', {
#                     'title': _('افزودن گروهی بازه‌های زمانی'),
#                     'opts': self.model._meta,
#                 })
            
#             # تبدیل زمان‌ها و مدت‌های زمانی
#             try:
#                 daily_start = datetime.strptime(daily_start_str, '%H:%M').time()
#                 daily_end = datetime.strptime(daily_end_str, '%H:%M').time()
#                 session_minutes = int(session_minutes_str) if session_minutes_str else 30
#                 break_minutes = int(break_minutes_str) if break_minutes_str else 10
#                 price = int(price_str) if price_str else 0
#                 discount_price = int(discount_price_str) if discount_price_str else 0
#             except Exception as e:
#                 messages.error(request, _('خطا در پردازش داده‌های وقت یا قیمت'))
#                 return render(request, 'admin/classroom/teacherAvailability/bulk_create.html', {
#                     'title': _('افزودن گروهی بازه‌های زمانی'),
#                     'opts': self.model._meta,
#                 })
            
#             # ایجاد بازه‌های زمانی برای هر روز
#             created = 0
#             cur_date = start_date
#             import datetime as _dt
            
#             while cur_date <= end_date:
#                 cursor = _dt.datetime.combine(cur_date, daily_start)
#                 day_end = _dt.datetime.combine(cur_date, daily_end)
                
#                 while cursor + _dt.timedelta(minutes=session_minutes) <= day_end:
#                     slot_start = cursor.time()
#                     slot_end = (cursor + _dt.timedelta(minutes=session_minutes)).time()
                    
#                     # بررسی تکراری نبودن - اگر موجود باشد skip می‌کنیم
#                     if not TeacherAvailability.objects.filter(
#                         teacher_id=teacher_id,
#                         date=cur_date,
#                         start_time=slot_start,
#                         end_time=slot_end
#                     ).exists():
#                         TeacherAvailability.objects.create(
#                             teacher_id=teacher_id,
#                             date=cur_date,
#                             start_time=slot_start,
#                             end_time=slot_end,
#                             price=price,
#                             discount_price=discount_price,
#                             is_available=True
#                         )
#                         created += 1
                    
#                     cursor += _dt.timedelta(minutes=(session_minutes + break_minutes))
                
#                 cur_date = cur_date + _dt.timedelta(days=1)
            
#             # پیام خوب حتی اگر 0 بازه اضافه شود
#             if created == 0:
#                 messages.warning(request, _(f'هیچ بازه زمانی جدیدی اضافه نشد. احتمالاً تمام این بازه‌ها قبلاً ثبت شده بودند.'))
#             else:
#                 messages.success(request, _(f'ایجاد شد: {created} بازه زمانی'))
            
#             return redirect('admin:classroom_teacheravailability_changelist')
        
#         from account.models import User
#         teachers = User.objects.filter(role='teacher')
        
#         return render(request, 'admin/classroom/teacherAvailability/bulk_create.html', {
#             'title': _('افزودن گروهی بازه‌های زمانی'),
#             'teachers': teachers,
#             'opts': self.model._meta,
#         })
    
#     def jalali_date(self, obj):
#         return get_jalali_date(obj.date)
#     jalali_date.short_description = _('تاریخ')
    
#     def jalali_date_display(self, obj):
#         return get_jalali_date(obj.date)
#     jalali_date_display.short_description = _('تاریخ شمسی')
    
#     def is_available_badge(self, obj):
#         color = '#28a745' if obj.is_available else '#dc3545'
#         text = _('دسترسی‌پذیر') if obj.is_available else _('غیردسترسی‌پذیر')
#         return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
#     is_available_badge.short_description = _('در دسترس')
    
#     def is_booked_badge(self, obj):
#         color = '#ff6b6b' if obj.is_booked else '#95e1d3'
#         text = _('رزرو‌شده') if obj.is_booked else _('آزاد')
#         return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
#     is_booked_badge.short_description = _('وضعیت رزرو')
    
#     def mark_available(self, request, queryset):
#         """انتخاب بازه‌های زمانی برای در دسترس"""
#         updated = queryset.filter(is_booked=False).update(is_available=True)
#         self.message_user(request, _(f'{updated} بازه زمانی به عنوان دسترسی‌پذیر علامت‌گذاری شد'))
#     mark_available.short_description = _('علامت‌گذاری به عنوان دسترسی‌پذیر')
    
#     def mark_unavailable(self, request, queryset):
#         """انتخاب بازه‌های زمانی برای غیردر دسترس"""
#         updated = queryset.update(is_available=False)
#         self.message_user(request, _(f'{updated} بازه زمانی به عنوان غیردسترسی‌پذیر علامت‌گذاری شد'))
#     mark_unavailable.short_description = _('علامت‌گذاری به عنوان غیردسترسی‌پذیر')
    
#     def bulk_delete(self, request, queryset):
#         """حذف گروهی بازه‌های زمانی آزاد (رزرو‌نشده)"""
#         # فقط بازه‌های زمانی آزاد می‌توانند حذف شوند
#         deletable = queryset.filter(is_booked=False)
#         count, _ = deletable.delete()
#         self.message_user(request, _(f'{count} بازه زمانی حذف شد'))
#     bulk_delete.short_description = _('حذف بازه های آزاد')
    
#     def has_delete_permission(self, request, obj=None):
#         """منع حذف مستقیم - فقط از طریق bulk_delete"""
#         return False


# ===== TeachingSubject Admin =====
@admin.register(TeachingSubject)
class TeachingSubjectAdmin(BilingualModelAdmin):
    list_display = ['title', 'teacher', 'level', 'status_badge', 'is_active_badge', 'cover_image_preview']
    list_filter = ['status', 'level', 'is_active']
    search_fields = ['title', 'teacher__name', 'teacher__username']

    fieldsets = (
        (_('اطلاعات اساسی'), {
            'fields': ('teacher', 'title', 'level', 'is_active')
        }),
        (_('وضعیت تایید'), {
            'fields': ('status', 'rejection_reason')
        }),
        (_('توصیف'), {
            'fields': ('description',)
        }),
        (_('رسانه'), {
            'fields': ('cover_image', 'cover_image_preview', 'demo_video')
        }),
        (_('محدودیت سن'), {
            'fields': ('min_age', 'max_age')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [
            'teacher',
            'title',
            'level',
            'is_active',
            'description',
            'cover_image',
            'cover_image_preview',
            'demo_video',
            'min_age',
            'max_age',
            'created_at_display',
            'updated_at_display',
        ]

    def cover_image_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 120px; max-width: 200px; border-radius: 8px;" />',
                obj.cover_image.url
            )
        return _("تصویری وجود ندارد")
    cover_image_preview.short_description = _("پیش‌نمایش عکس کاور")

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        text = obj.get_status_display()
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color,
            text
        )
    status_badge.short_description = _('وضعیت تایید')

    def is_active_badge(self, obj):
        color = '#28a745' if obj.is_active else '#dc3545'
        text = _('فعال') if obj.is_active else _('غیرفعال')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color,
            text
        )
    is_active_badge.short_description = _('وضعیت')

    def save_model(self, request, obj, form, change):
        if obj.status == 'rejected' and not obj.rejection_reason:
            messages.error(request, _('علت رد کردن الزامی است.'))
            return
        super().save_model(request, obj, form, change)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'subject',
        'teacher_name',
        'price',
        'discounted_price',
        'session_count',
        'status_badge',
        'is_active_badge',
        'created_at_display',
    ]
    list_filter = ['status', 'is_active', 'subject']
    search_fields = ['title', 'description']
    list_select_related = ["subject", "subject__teacher"]
    readonly_fields = [
        'created_at_display',
        'updated_at_display',
        'subject',
        'title',
        'description',
        'cover_image',
        'price',
        'discounted_price',
        'session_count',
        'is_active',
    ]
    
    fieldsets = (
        (_('اطلاعات اصلی'), {
            'fields': ('subject', 'title', 'description', 'cover_image')
        }),
        (_('قیمت‌گذاری'), {
            'fields': ('price', 'discounted_price')
        }),
        (_('تنظیمات'), {
            'fields': ('session_count', 'is_active')
        }),
        (_('وضعیت تایید'), {
            'fields': ('status', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        (_('تاریخچه'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description=_("معلم"), ordering="subject__teacher")
    def teacher_name(self, obj):
        teacher = getattr(getattr(obj, "subject", None), "teacher", None)

        if not teacher:
            return "-"

        full_name = ""
        if hasattr(teacher, "get_full_name"):
            full_name = teacher.get_full_name().strip()

        if full_name:
            return full_name

        if getattr(teacher, "username", None):
            return teacher.username

        if getattr(teacher, "phone", None):
            return teacher.phone

        if getattr(teacher, "email", None):
            return teacher.email

        return str(teacher) or "-"
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'approved': '#28a745',
            'rejected': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        display = obj.get_status_display() or obj.status
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            display
        )
    status_badge.short_description = _("وضعیت تایید")
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">{}</span>', '✓ فعال')
        return format_html('<span style="color: red;">{}</span>', '✗ غیرفعال')
    is_active_badge.short_description = _("وضعیت")
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'rejected' and not obj.rejection_reason:
            messages.error(request, _('علت رد کردن الزامی است.'))
            return
        super().save_model(request, obj, form, change)
        
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'paid_amount', 'payment_status_badge', 'formatted_paid_at', 'created_at_display']
    list_filter = ['payment_status', 'paid_at']
    search_fields = ['student__name', 'student__email', 'course__title', 'payment_ref']
    readonly_fields = ['created_at_display', 'updated_at_display', 'formatted_paid_at', 'course', 'student', 'paid_amount', 'payment_status', 'payment_ref']
    
    fieldsets = (
        (_('اطلاعات ثبت‌نام'), {
            'fields': ('course', 'student')
        }),
        (_('پرداخت'), {
            'fields': ('paid_amount', 'payment_status', 'payment_ref', 'formatted_paid_at')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_change_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def formatted_paid_at(self, obj):
        """نمایش تاریخ پرداخت بر اساس زبان فعال"""
        return format_date(obj.paid_at)
    formatted_paid_at.short_description = _('تاریخ پرداخت')
    
    def payment_status_badge(self, obj):
        colors = {
            'not_paid': '#ffc107',
            'paid': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.payment_status, '#6c757d')
        text = obj.get_payment_status_display()
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color, text
        )
    payment_status_badge.short_description = _('وضعیت پرداخت')
    
    actions = ['mark_as_paid']
    
    def mark_as_paid(self, request, queryset):
        """تایید پرداخت دسته‌ای"""
        from django.utils import timezone
        
        count = 0
        for enrollment in queryset.filter(payment_status='not_paid'):
            try:
                enrollment.confirm_payment(payment_ref=f'ADMIN_{timezone.now().timestamp()}')
                count += 1
            except Exception as e:
                self.message_user(request, f'خطا در ثبت‌نام {enrollment}: {str(e)}', level='error')
        
        self.message_user(request, f'{count} ثبت‌نام با موفقیت تایید شد.')
    mark_as_paid.short_description = _('تایید پرداخت و ایجاد رزروها')  
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
    

# ===== ClassBooking Admin =====
@admin.register(ClassBooking)
class ClassBookingAdmin(admin.ModelAdmin):
    list_display = ['subject', 'teacher', 'student', 'status_badge', 'final_price']
    list_filter = ['status',]
    search_fields = ['subject__title', 'teacher__name', 'student__name']
    readonly_fields = ['created_at_display', 'updated_at_display', 'teacher', 'student', 'subject', 'availability', 'price', 'discount_amount', 'final_price', 'enrollment', 'status']
    
    def has_add_permission(self, request):
        return False
    
    fieldsets = (
        (_('طرف‌های کلاس'), {
            'fields': ('teacher', 'student', 'subject', 'availability', 'enrollment')
        }),
        (_('قیمت‌گذاری'), {
            'fields': ('price', 'discount_amount', 'final_price')  # discount_code حذف شد
        }),
        (_('وضعیت'), {
            'fields': ('status',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'reserved': '#ffc107',
            'completed': '#28a745',
            'cancelled': '#dc3545',
            'no_show': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        text = obj.get_status_display()
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    status_badge.short_description = _('وضعیت')
    
    def has_delete_permission(self, request, obj=None):
        return False


# ===== TeacherWallet Admin =====
@admin.register(TeacherWallet)
class TeacherWalletAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'available_balance_display', 'pending_balance_display', 'is_verified_badge', 'is_active_badge']
    list_filter = ['is_verified', 'is_active']
    search_fields = ['teacher__name', 'teacher__username']
    readonly_fields = ['balance', 'total_earned', 'total_withdrawn', 'verified_at', 'created_at_display', 'updated_at_display', 'available_balance', 'pending_balance', 'teacher', 'bank_name', 'account_number', 'iban', 'card_number', 'account_holder_name']
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        (_('معلم'), {
            'fields': ('teacher', 'is_active')
        }),
        (_('موجودی'), {
            'fields': ('balance', 'available_balance', 'pending_balance')
        }),
        (_('درآمد'), {
            'fields': ('total_earned', 'total_withdrawn')
        }),
        (_('اطلاعات بانکی'), {
            'fields': ('bank_name', 'account_number', 'iban', 'card_number', 'account_holder_name')
        }),
        (_('تنظیمات تسویه'), {
            'fields': ('minimum_settlement_amount', 'next_settlement_date')
        }),
        (_('تایید'), {
            'fields': ('is_verified', 'verified_at')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def available_balance_display(self, obj):
        # 1. ابتدا عدد را به صورت دستی فرمت می‌کنیم (تبدیل به رشته با جداکننده)
        amount = float(obj.available_balance or 0)
        formatted_amount = "{:,.0f}".format(amount)
        
        # 2. حالا رشته آماده شده را در HTML قرار می‌دهیم
        return format_html(
            '<strong style="color:#28a745">{}</strong> تومان', 
            formatted_amount
        )
    available_balance_display.short_description = _('موجودی قابل برداشت')
    
    def pending_balance_display(self, obj):
        # 1. ابتدا عدد را به صورت دستی فرمت می‌کنیم
        amount = float(obj.pending_balance or 0)
        formatted_amount = "{:,.0f}".format(amount)
        
        # 2. حالا رشته آماده شده را در HTML قرار می‌دهیم
        return format_html(
            '<strong style="color:#ffc107">{}</strong> تومان', 
            formatted_amount
        )
    pending_balance_display.short_description = _('موجودی در انتظار')
    
    
    def is_verified_badge(self, obj):
        color = '#28a745' if obj.is_verified else '#dc3545'
        text = _('تایید شده') if obj.is_verified else _('تایید نشده')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_verified_badge.short_description = _('تایید')
    
    def is_active_badge(self, obj):
        color = '#28a745' if obj.is_active else '#dc3545'
        text = _('فعال') if obj.is_active else _('غیرفعال')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_active_badge.short_description = _('وضعیت')


# ===== ClassRevenue Admin =====
@admin.register(ClassRevenue)
class ClassRevenueAdmin(BilingualModelAdmin):
    list_display = ['teacher', 'booking', 'total_amount_display', 'teacher_share_display', 'is_confirmed_badge']
    list_filter = ['is_confirmed', 'is_settled']
    search_fields = ['teacher__name', 'booking__subject__title']
    readonly_fields = ['platform_fee', 'teacher_share', 'created_at_display', 'updated_at_display', 'confirmed_at', 'settled_at', 'teacher', 'booking', 'original_price', 'discount_amount', 'total_amount']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        (_('درآمد'), {
            'fields': ('teacher', 'booking')
        }),
        (_('مبالغ'), {
            'fields': ('original_price', 'discount_amount', 'total_amount')
        }),
        (_('کارمزد و سهم'), {
            'fields': ('platform_fee_percentage', 'platform_fee', 'teacher_share')
        }),
        (_('تایید'), {
            'fields': ('is_confirmed', 'confirmed_at')
        }),
        (_('تسویه'), {
            'fields': ('is_settled', 'settled_at')
        }),
        (_('یادداشت'), {
            'fields': ('notes',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def total_amount_display(self, obj):
        formatted_amount = f'{float(obj.total_amount):,.0f}'
        return format_html('<strong style="color:#007bff">{} تومان</strong>', formatted_amount)
    total_amount_display.short_description = _('مبلغ کل')
    
    def teacher_share_display(self, obj):
        formatted_share = f'{float(obj.teacher_share):,.0f}'
        return format_html('<strong style="color:#28a745">{} تومان</strong>', formatted_share)
    teacher_share_display.short_description = _('سهم معلم')
    
    def is_confirmed_badge(self, obj):
        color = '#28a745' if obj.is_confirmed else '#dc3545'
        text = str(_('تایید شده')) if obj.is_confirmed else str(_('تایید نشده'))
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_confirmed_badge.short_description = _('تایید')
    
    

# ===== WithdrawalRequest Admin =====
@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(BilingualModelAdmin):
    list_display = ['teacher', 'amount_display', 'status_badge', 'payment_method_display', 'jalali_created']
    list_filter = ['status', 'payment_method']
    search_fields = ['teacher__name']
    readonly_fields = ['created_at_display', 'updated_at_display', 'completed_at', 'jalali_created_display', 
                       'teacher', 'amount', 'revenues', 'account_info_display', 'receipt_preview']
    actions = ['approve_withdrawal', 'reject_withdrawal']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def save_model(self, request, obj, form, change):
        """Override save to handle withdrawal completion"""
        if change:
            old_obj = WithdrawalRequest.objects.get(pk=obj.pk)
            
            # ✅ تایید درخواست
            if old_obj.status != 'completed' and obj.status == 'completed':
                receipt_image = form.cleaned_data.get('receipt_image') or obj.receipt_image
                
                if not receipt_image:
                    messages.error(request, _("لطفاً قبل از تایید، فیش واریزی را آپلود کنید"))
                    obj.status = old_obj.status
                    super().save_model(request, obj, form, change)
                    return
                
                # ✅ برگردوندن وضعیت به حالت قبلی
                obj.status = old_obj.status
                
                # ✅ اول فیش رو save کن
                super().save_model(request, obj, form, change)
                
                # ✅ بعد complete_withdrawal صدا بزن (که خودش status رو completed میکنه و save و SMS می‌فرسته)
                success, message = obj.complete_withdrawal()
                
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)
                return
            
            # ✅ رد درخواست
            if old_obj.status != 'cancelled' and obj.status == 'cancelled':
                # ✅ برگردوندن وضعیت به حالت قبلی
                obj.status = old_obj.status
                
                # ✅ اول save کن
                super().save_model(request, obj, form, change)
                
                # ✅ مستقیم cancel_withdrawal صدا بزن (که خودش status رو cancelled میکنه و save و SMS می‌فرسته)
                success, message = obj.cancel_withdrawal()
                
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)
                return
        
        super().save_model(request, obj, form, change)
    
    @admin.action(description=_('تایید و پرداخت درخواست‌های انتخاب‌شده'))
    def approve_withdrawal(self, request, queryset):
        """تایید و پرداخت درخواست برداشت"""
        success_count = 0
        error_messages = []
        
        for withdrawal in queryset.filter(status='pending'):
            if not withdrawal.receipt_image:
                error_messages.append(f"{withdrawal.teacher.name}: فیش واریزی آپلود نشده است")
                continue
            
            success, message = withdrawal.complete_withdrawal()
            if success:
                success_count += 1
            else:
                error_messages.append(f"{withdrawal.teacher.name}: {message}")
        
        if success_count > 0:
            self.message_user(
                request,
                _('%(count)d درخواست با موفقیت تایید و پرداخت شد و SMS ارسال شد') % {'count': success_count},
                messages.SUCCESS
            )
        
        if error_messages:
            self.message_user(
                request,
                _('خطاها: ') + ' | '.join(error_messages),
                messages.ERROR
            )
    
    @admin.action(description=_('رد کردن درخواست‌های انتخاب‌شده'))
    def reject_withdrawal(self, request, queryset):
        """رد کردن درخواست برداشت"""
        success_count = 0
        error_messages = []
        
        for withdrawal in queryset.filter(status='pending'):
            success, message = withdrawal.cancel_withdrawal()
            if success:
                success_count += 1
            else:
                error_messages.append(f"{withdrawal.teacher.name}: {message}")
        
        if success_count > 0:
            self.message_user(
                request,
                _('%(count)d درخواست رد شد و SMS ارسال شد') % {'count': success_count},
                messages.SUCCESS
            )
        
        if error_messages:
            self.message_user(
                request,
                _('خطاها: ') + ' | '.join(error_messages),
                messages.ERROR
            )
    
    fieldsets = (
        (_('درخواست کننده'), {
            'fields': ('teacher', 'amount')
        }),
        (_('درآمدهای انتخاب‌شده'), {
            'fields': ('revenues',)
        }),
        (_('روش پرداخت'), {
            'fields': ('payment_method', 'account_info_display')
        }),
        (_('وضعیت'), {
            'fields': ('status', 'completed_at')
        }),
        (_('تراکنش'), {
            'fields': ('transaction_id',)
        }),
        # ✅ فیلد فیش واریزی
        (_('فیش واریزی'), {
            'fields': ('receipt_image', 'receipt_preview')
        }),
        (_('یادداشت‌ها'), {
            'fields': ('notes', 'admin_notes')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display', 'jalali_created_display'),
            'classes': ('collapse',)
        }),
    )
    
    # ✅ نمایش پیش‌نمایش فیش
    def receipt_preview(self, obj):
        if obj.receipt_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-width: 300px; max-height: 300px; border: 1px solid #ddd; padding: 5px;"/></a>',
                obj.receipt_image.url,
                obj.receipt_image.url
            )
        return '-'
    receipt_preview.short_description = _('پیش‌نمایش فیش')
    
    def account_info_display(self, obj):
        if not obj.account_info:
            return '-'
        
        try:
            data = obj.account_info if isinstance(obj.account_info, dict) else json.loads(obj.account_info)
            
            html = '<table style="border-collapse: collapse; width: 100%; max-width: 500px;">'
            
            labels = {
                'card_number': 'شماره کارت',
                'account_number': 'شماره حساب',
                'iban': 'شماره شبا',
                'bank_name': 'نام بانک',
                'account_holder_name': 'نام صاحب حساب'
            }
            
            for key, value in data.items():
                label = labels.get(key, key)
                html += f'<tr><td style="padding: 5px; font-weight: bold; border-bottom: 1px solid #ddd; text-align: right;">{label}:</td>'
                html += f'<td style="padding: 5px; border-bottom: 1px solid #ddd; text-align: left;">{value}</td></tr>'
            
            html += '</table>'
            return mark_safe(html)
        except:
            return str(obj.account_info)
    
    account_info_display.short_description = _('اطلاعات حساب')
    
    def amount_display(self, obj):
        formatted_amount = f"{obj.amount:,.0f}"
        return format_html(
            '<span style="color: green;">{} تومان</span>',
            formatted_amount
        )
    amount_display.short_description = _('مبلغ')
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        text = obj.get_status_display()
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    status_badge.short_description = _('وضعیت')
    
    def payment_method_display(self, obj):
        return obj.get_payment_method_display()
    payment_method_display.short_description = _('روش پرداخت')
    
    def jalali_created(self, obj):
        if obj.created_at:
            jalali = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return jalali.strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created.short_description = _('تاریخ درخواست')
    
    def jalali_created_display(self, obj):
        return self.jalali_created(obj)
    jalali_created_display.short_description = _('تاریخ درخواست (شمسی)')
    

# ===== WalletTransaction Admin =====
@admin.register(WalletTransaction)
class WalletTransactionAdmin(BilingualModelAdmin):
    list_display = ['wallet', 'transaction_type_badge', 'amount_display', 'jalali_created']
    list_filter = ['transaction_type',]
    search_fields = ['wallet__teacher__name', 'description']
    readonly_fields = ['wallet', 'transaction_type', 'amount', 'balance_before', 'balance_after', 'created_at_display', 'updated_at_display', 'revenue', 'withdrawal', 'description']
    
    fieldsets = (
        (_('کیف پول'), {
            'fields': ('wallet', 'transaction_type')
        }),
        (_('مبالغ'), {
            'fields': ('amount', 'balance_before', 'balance_after')
        }),
        (_('ارجاع'), {
            'fields': ('revenue', 'withdrawal')
        }),
        (_('توصیف'), {
            'fields': ('description', 'admin_note')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def transaction_type_badge(self, obj):
        colors = {
            'revenue': '#28a745',
            'confirmation': '#17a2b8',
            'withdrawal': '#dc3545',
            'refund': '#ffc107',
            'adjustment': '#6c757d',
            'bonus': '#20c997',
            'penalty': '#e83e8c'
        }
        color = colors.get(obj.transaction_type, '#6c757d')
        text = obj.get_transaction_type_display()
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    transaction_type_badge.short_description = _('نوع تراکنش')
    
    def amount_display(self, obj):
        sign = '+' if obj.transaction_type in ['revenue', 'refund', 'bonus'] else '-'
        color = '#28a745' if sign == '+' else '#dc3545'
        formatted_amount = f"{obj.amount:,.0f}"
        return format_html('<strong style="color:{}">{}{}</strong> تومان', color, sign, formatted_amount)
    amount_display.short_description = _('مبلغ')

    
    def jalali_created(self, obj):
        """نمایش تاریخ ایجاد بر اساس زبان فعال"""
        return format_date(obj.created_at)
    jalali_created.short_description = _('تاریخ')


# ===== StudentTransaction Admin =====
@admin.register(StudentTransaction)
class StudentTransactionAdmin(BilingualModelAdmin):
    list_display = ['student', 'transaction_type_badge', 'amount_display', 'status_badge', 'formatted_payment_date']
    list_filter = ['transaction_type', 'status']
    search_fields = ['student__name', 'student__username']
    readonly_fields = ['formatted_payment_date', 'created_at_display','description', 'updated_at_display', 'student', 'transaction_type', 'amount', 'booking']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        (_('دانش‌آموز'), {
            'fields': ('student',)
        }),
        (_('تراکنش'), {
            'fields': ('transaction_type', 'amount')
        }),
        (_('کلاس'), {
            'fields': ('booking',)
        }),
        (_('توصیف'), {
            'fields': ('description',)
        }),
        (_('وضعیت'), {
            'fields': ('status', 'formatted_payment_date')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_payment_date(self, obj):
        return format_date(obj.payment_date)
    formatted_payment_date.short_description = _('تاریخ پرداخت')
    
    def transaction_type_badge(self, obj):
        colors = {
            'class_payment': '#007bff',
            'refund': '#ffc107'
        }
        color = colors.get(obj.transaction_type, '#6c757d')
        text = obj.get_transaction_type_display()
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    transaction_type_badge.short_description = _('نوع تراکنش')
    
    def amount_display(self, obj):
        formatted_amount = f"{obj.amount:,.0f}"
        return format_html('<strong style="color:#007bff">{}</strong> تومان', formatted_amount)
    amount_display.short_description = _('مبلغ')
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'refunded': '#17a2b8'
        }
        color = colors.get(obj.status, '#6c757d')
        text = obj.get_status_display()
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    status_badge.short_description = _('وضعیت')

# ===== PlatformSettings Admin =====
@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    list_display = ['commission_rate_class', 'admin_actions']
    readonly_fields = ['updated_at_display', 'updated_by']
    
    fieldsets = (
        (_('کمیسیون'), {
            'fields': ('commission_rate_class',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('updated_by', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
        
    def admin_actions(self, obj):
        edit_url = reverse('admin:classroom_platformsettings_change', args=[obj.id])
        
        return format_html(
            '<a href="{}" class="button" style="margin-right:10px; padding:5px;">✏️ {}</a>',
            edit_url, _("Edit")
        )
    admin_actions.short_description = _("Actions")


# ===== Attendance Admin =====
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'subject_title', 'status', 'marked_at_display']
    list_filter = ['status', 'marked_at', 'student']
    search_fields = ['student__name', 'student__username', 'booking__subject__title']
    readonly_fields = ['marked_at_display', 'booking', 'student', 'status']
    ordering = ['-marked_at']
    
    fieldsets = (
        (_('اطلاعات'), {
            'fields': ('booking', 'student', 'status')
        }),
        (_('سیستم'), {
            'fields': ('marked_at_display',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False
        
    def has_change_permission(self, request, obj=None):
        return True
    
    def student_name(self, obj):
        return obj.student.name or obj.student.username
    student_name.short_description = _('دانش‌آموز')
    
    def subject_title(self, obj):
        return obj.booking.subject.title
    subject_title.short_description = _('موضوع')

# ===== Support Message Attachments Inline =====
class SupportMessageAttachmentInline(admin.TabularInline):
    model = SupportMessageAttachment
    extra = 1
    readonly_fields = ['created_at_display', 'file_preview']
    fields = ['file', 'file_preview', 'created_at_display']
    
    def file_preview(self, obj):
        """نمایش پیوند دانلود فایل"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.file.url,
                obj.file.name.split('/')[-1]
            )
        return '-'
    file_preview.short_description = _('فایل')


# ===== Support Message Admin =====
@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['teacher_name', 'sender_name', 'status_badge', 'message_preview', 'created_at_display', 'chat_link']
    list_filter = ['status', 'teacher', 'read_at']
    search_fields = ['teacher__name', 'teacher__username', 'sender__name', 'sender__username', 'message_text']
    readonly_fields = ['created_at_display', 'updated_at_display', 'read_at', 'status']
    inlines = [SupportMessageAttachmentInline]
    ordering = ['-created_at']
    
    fieldsets = (
        (_('اطلاعات پیام'), {
            'fields': ('teacher', 'sender', 'message_text', 'status')
        }),
        (_('زمان‌ها'), {
            'fields': ('created_at_display', 'read_at'),
            'classes': ('collapse',)
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        """هدایت نمایش لیست به صفحه چت"""
        return HttpResponseRedirect('/admin/classroom/supportmessage/chat/')
    
    def get_urls(self):
        """اضافه کردن URL برای صفحه مدیریت چت"""
        urls = super().get_urls()
        custom_urls = [
            path('chat/', self.admin_site.admin_view(self.chat_view), name='supportmessage_chat'),
        ]
        return custom_urls + urls
    
    def chat_view(self, request):
        """نمایش صفحه مدیریت چت"""
        context = self.admin_site.each_context(request)
        context['title'] = _('مدیریت پیام‌های پشتیبانی')
        context['view_type'] = 'conversations'  # نشان‌دهنده نوع نمایش
        return render(request, 'admin/support_message_chat.html', context)
    
    def chat_link(self, obj):
        """دکمه لینک به صفحه چت"""
        return format_html(
            '<a class="button" href="{}" style="background-color: #417690; color: white; text-decoration: none; padding: 5px 12px; border-radius: 4px; display: inline-block;">'
            '💬 جزئیات چت</a>',
            '/admin/classroom/supportmessage/chat/'
        )
    chat_link.short_description = _('مدیریت')
    
    def teacher_name(self, obj):
        return obj.teacher.name or obj.teacher.username
    teacher_name.short_description = _('معلم')
    
    def sender_name(self, obj):
        if obj.sender:
            return obj.sender.name or obj.sender.username
        return '-'
    sender_name.short_description = _('فرستنده')
    
    def status_badge(self, obj):
        """نمایش وضعیت با رنگ‌بندی"""
        if obj.status == 'read':
            color = 'green'
            label = _('خوانده‌شده')
        else:
            color = 'blue'
            label = _('ارسال‌شده')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            label
        )
    status_badge.short_description = _('وضعیت')
    
    def message_preview(self, obj):
        """نمایش پیش‌نمایش پیام"""
        if obj.message_text:
            preview = obj.message_text[:50]
            if len(obj.message_text) > 50:
                preview += '...'
            return preview
        else:
            attachments_count = obj.attachments.count()
            return _('بدون متن ({} فایل)').format(attachments_count)
    message_preview.short_description = _('پیام')