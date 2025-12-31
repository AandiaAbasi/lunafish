from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from django.template.response import TemplateResponse
from .models import (
    TeacherAvailability, TeachingSubject, ClassBooking,
    TeacherWallet, ClassRevenue, WithdrawalRequest, WalletTransaction,
    StudentTransaction, PlatformSettings, Attendance, SupportMessage, SupportMessageAttachment
)
import jdatetime
from datetime import datetime
import csv
from io import StringIO


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
    list_filter = ['teacher', 'date', 'is_available', 'is_booked', 'created_at']
    search_fields = ['teacher__name', 'teacher__username']
    ordering = ['-date', 'start_time']
    readonly_fields = ['created_at', 'updated_at', 'jalali_date_display']
    actions = ['mark_available', 'mark_unavailable', 'bulk_delete']
    change_list_template = 'admin/classroom/teacherAvailability/change_list.html'
    
    fieldsets = (
        (_('معلم و تاریخ'), {
            'fields': ('teacher', 'date', 'jalali_date_display')
        }),
        (_('ساعات'), {
            'fields': ('start_time', 'end_time')
        }),
        (_('قیمت‌گذاری'), {
            'fields': ('price', 'discount_price')
        }),
        (_('وضعیت'), {
            'fields': ('is_available', 'is_booked')
        }),
        (_('یادداشت'), {
            'fields': ('notes',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-create/', self.admin_site.admin_view(self.bulk_create_view), name='classroom_availability_bulk_create'),
        ]
        return custom_urls + urls
    
    def bulk_create_view(self, request):
        """صفحه برای افزودن گروهی بازه‌های زمانی"""
        if request.method == 'POST':
            from django import forms
            from account.models import User
            
            teacher_id = request.POST.get('teacher')
            sd_raw = request.POST.get('start_date')
            ed_raw = request.POST.get('end_date')
            daily_start_str = request.POST.get('daily_start_time')
            daily_end_str = request.POST.get('daily_end_time')
            session_minutes_str = request.POST.get('session_duration')
            break_minutes_str = request.POST.get('break_duration')
            price_str = request.POST.get('price')
            discount_price_str = request.POST.get('discount_price')
            
            # تبدیل تاریخ‌های شمسی به میلادی
            try:
                start_date = jdatetime.datetime.strptime(sd_raw, '%Y/%m/%d').togregorian().date()
                end_date = jdatetime.datetime.strptime(ed_raw, '%Y/%m/%d').togregorian().date()
            except Exception as e:
                messages.error(request, _('فرمت تاریخ نادرست است'))
                return render(request, 'admin/classroom/teacherAvailability/bulk_create.html', {
                    'title': _('افزودن گروهی بازه‌های زمانی'),
                    'opts': self.model._meta,
                })
            
            # تبدیل زمان‌ها و مدت‌های زمانی
            try:
                daily_start = datetime.strptime(daily_start_str, '%H:%M').time()
                daily_end = datetime.strptime(daily_end_str, '%H:%M').time()
                session_minutes = int(session_minutes_str) if session_minutes_str else 30
                break_minutes = int(break_minutes_str) if break_minutes_str else 10
                price = int(price_str) if price_str else 0
                discount_price = int(discount_price_str) if discount_price_str else 0
            except Exception as e:
                messages.error(request, _('خطا در پردازش داده‌های وقت یا قیمت'))
                return render(request, 'admin/classroom/teacherAvailability/bulk_create.html', {
                    'title': _('افزودن گروهی بازه‌های زمانی'),
                    'opts': self.model._meta,
                })
            
            # ایجاد بازه‌های زمانی برای هر روز
            created = 0
            cur_date = start_date
            import datetime as _dt
            
            while cur_date <= end_date:
                cursor = _dt.datetime.combine(cur_date, daily_start)
                day_end = _dt.datetime.combine(cur_date, daily_end)
                
                while cursor + _dt.timedelta(minutes=session_minutes) <= day_end:
                    slot_start = cursor.time()
                    slot_end = (cursor + _dt.timedelta(minutes=session_minutes)).time()
                    
                    # بررسی تکراری نبودن - اگر موجود باشد skip می‌کنیم
                    if not TeacherAvailability.objects.filter(
                        teacher_id=teacher_id,
                        date=cur_date,
                        start_time=slot_start,
                        end_time=slot_end
                    ).exists():
                        TeacherAvailability.objects.create(
                            teacher_id=teacher_id,
                            date=cur_date,
                            start_time=slot_start,
                            end_time=slot_end,
                            price=price,
                            discount_price=discount_price,
                            is_available=True
                        )
                        created += 1
                    
                    cursor += _dt.timedelta(minutes=(session_minutes + break_minutes))
                
                cur_date = cur_date + _dt.timedelta(days=1)
            
            # پیام خوب حتی اگر 0 بازه اضافه شود
            if created == 0:
                messages.warning(request, _(f'هیچ بازه زمانی جدیدی اضافه نشد. احتمالاً تمام این بازه‌ها قبلاً ثبت شده بودند.'))
            else:
                messages.success(request, _(f'ایجاد شد: {created} بازه زمانی'))
            
            return redirect('admin:classroom_teacheravailability_changelist')
        
        from account.models import User
        teachers = User.objects.filter(role='teacher')
        
        return render(request, 'admin/classroom/teacherAvailability/bulk_create.html', {
            'title': _('افزودن گروهی بازه‌های زمانی'),
            'teachers': teachers,
            'opts': self.model._meta,
        })
    
    def jalali_date(self, obj):
        return get_jalali_date(obj.date)
    jalali_date.short_description = _('تاریخ')
    
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
    
    def mark_available(self, request, queryset):
        """انتخاب بازه‌های زمانی برای در دسترس"""
        updated = queryset.filter(is_booked=False).update(is_available=True)
        self.message_user(request, _(f'{updated} بازه زمانی به عنوان دسترسی‌پذیر علامت‌گذاری شد'))
    mark_available.short_description = _('علامت‌گذاری به عنوان دسترسی‌پذیر')
    
    def mark_unavailable(self, request, queryset):
        """انتخاب بازه‌های زمانی برای غیردر دسترس"""
        updated = queryset.update(is_available=False)
        self.message_user(request, _(f'{updated} بازه زمانی به عنوان غیردسترسی‌پذیر علامت‌گذاری شد'))
    mark_unavailable.short_description = _('علامت‌گذاری به عنوان غیردسترسی‌پذیر')
    
    def bulk_delete(self, request, queryset):
        """حذف گروهی بازه‌های زمانی آزاد (رزرو‌نشده)"""
        # فقط بازه‌های زمانی آزاد می‌توانند حذف شوند
        deletable = queryset.filter(is_booked=False)
        count, _ = deletable.delete()
        self.message_user(request, _(f'{count} بازه زمانی حذف شد'))
    bulk_delete.short_description = _('حذف بازه های آزاد')
    
    def has_delete_permission(self, request, obj=None):
        """منع حذف مستقیم - فقط از طریق bulk_delete"""
        return False


# ===== TeachingSubject Admin =====
@admin.register(TeachingSubject)
class TeachingSubjectAdmin(BilingualModelAdmin):
    list_display = ['title', 'teacher', 'level', 'is_active_badge']
    list_filter = ['level', 'is_active', 'created_at']
    search_fields = ['title', 'teacher__name', 'teacher__username']
    readonly_fields = ['created_at', 'updated_at', 'teacher']
    
    fieldsets = (
        (_('اطلاعات اساسی'), {
            'fields': ('teacher', 'title', 'level', 'is_active')
        }),
        (_('توصیف'), {
            'fields': ('description',)
        }),
        (_('رسانه'), {
            'fields': ('cover_image', 'demo_video')
        }),
        (_('محدودیت سن'), {
            'fields': ('min_age', 'max_age')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_badge(self, obj):
        color = '#28a745' if obj.is_active else '#dc3545'
        text = _('فعال') if obj.is_active else _('غیرفعال')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_active_badge.short_description = _('وضعیت')


# ===== ClassBooking Admin =====
@admin.register(ClassBooking)
class ClassBookingAdmin(admin.ModelAdmin):
    list_display = ['subject', 'teacher', 'student', 'status_badge', 'final_price']
    list_filter = ['status', 'created_at']
    search_fields = ['subject__title', 'teacher__name', 'student__name']
    readonly_fields = ['created_at', 'updated_at', 'teacher', 'student', 'subject', 'availability', 'price', 'discount_amount', 'final_price']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        (_('طرف‌های کلاس'), {
            'fields': ('teacher', 'student', 'subject', 'availability')
        }),
        (_('قیمت‌گذاری'), {
            'fields': ('price', 'discount_code', 'discount_amount', 'final_price')
        }),
        (_('وضعیت'), {
            'fields': ('status',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at', 'updated_at'),
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


# ===== TeacherWallet Admin =====
@admin.register(TeacherWallet)
class TeacherWalletAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'available_balance_display', 'pending_balance_display', 'is_verified_badge', 'is_active_badge']
    list_filter = ['is_verified', 'is_active', 'created_at']
    search_fields = ['teacher__name', 'teacher__username']
    readonly_fields = ['balance', 'total_earned', 'total_withdrawn', 'verified_at', 'created_at', 'updated_at', 'available_balance', 'pending_balance']
    
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
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def available_balance_display(self, obj):
        return format_html('<strong style="color:#28a745">{:,.0f}</strong> تومان', obj.available_balance)
    available_balance_display.short_description = _('موجودی قابل برداشت')
    
    def pending_balance_display(self, obj):
        return format_html('<strong style="color:#ffc107">{:,.0f}</strong> تومان', obj.pending_balance)
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
    list_filter = ['is_confirmed', 'is_settled', 'created_at']
    search_fields = ['teacher__name', 'booking__subject__title']
    readonly_fields = ['platform_fee', 'teacher_share', 'created_at', 'updated_at', 'confirmed_at', 'settled_at', 'teacher', 'booking', 'original_price', 'discount_amount', 'total_amount']
    
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
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_amount_display(self, obj):
        return format_html('<strong style="color:#007bff">{:,.0f}</strong> تومان', obj.total_amount)
    total_amount_display.short_description = _('مبلغ کل')
    
    def teacher_share_display(self, obj):
        return format_html('<strong style="color:#28a745">{:,.0f}</strong> تومان', obj.teacher_share)
    teacher_share_display.short_description = _('سهم معلم')
    
    def is_confirmed_badge(self, obj):
        color = '#28a745' if obj.is_confirmed else '#dc3545'
        text = _('تایید شده') if obj.is_confirmed else _('تایید نشده')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_confirmed_badge.short_description = _('تایید')


# ===== WithdrawalRequest Admin =====
@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(BilingualModelAdmin):
    list_display = ['teacher', 'amount_display', 'status_badge', 'payment_method_display', 'jalali_created']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['teacher__name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'jalali_created_display', 'teacher', 'amount', 'revenues', 'account_info']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        (_('درخواست کننده'), {
            'fields': ('teacher', 'amount')
        }),
        (_('درآمدهای انتخاب‌شده'), {
            'fields': ('revenues',)
        }),
        (_('روش پرداخت'), {
            'fields': ('payment_method', 'account_info')
        }),
        (_('وضعیت'), {
            'fields': ('status', 'completed_at')
        }),
        (_('تراکنش'), {
            'fields': ('transaction_id',)
        }),
        (_('یادداشت‌ها'), {
            'fields': ('notes', 'admin_notes')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at', 'updated_at', 'jalali_created_display'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        return format_html('<strong style="color:#dc3545">{:,.0f}</strong> تومان', obj.amount)
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
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__teacher__name', 'description']
    readonly_fields = ['wallet', 'transaction_type', 'amount', 'balance_before', 'balance_after', 'created_at', 'updated_at']
    
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
            'fields': ('created_at', 'updated_at'),
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
        return format_html('<strong style="color:{}\">{}{:,.0f}</strong> تومان', color, sign, obj.amount)
    amount_display.short_description = _('مبلغ')
    
    def jalali_created(self, obj):
        if obj.created_at:
            jalali = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return jalali.strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_created.short_description = _('تاریخ')


# ===== StudentTransaction Admin =====
@admin.register(StudentTransaction)
class StudentTransactionAdmin(BilingualModelAdmin):
    list_display = ['student', 'transaction_type_badge', 'amount_display', 'status_badge']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['student__name', 'student__username']
    readonly_fields = ['payment_date', 'created_at', 'updated_at', 'student', 'transaction_type', 'amount', 'booking']
    
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
            'fields': ('status', 'payment_date')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
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
        return format_html('<strong style="color:#007bff\">{:,.0f}</strong> تومان', obj.amount)
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
    list_display = ['commission_rate_class']
    readonly_fields = ['updated_at', 'updated_by']
    
    fieldsets = (
        (_('کمیسیون'), {
            'fields': ('commission_rate_class',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# ===== Attendance Admin =====
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'subject_title', 'status', 'marked_at']
    list_filter = ['status', 'marked_at', 'student']
    search_fields = ['student__name', 'student__username', 'booking__subject__title']
    readonly_fields = ['marked_at']
    ordering = ['-marked_at']
    
    fieldsets = (
        (_('اطلاعات'), {
            'fields': ('booking', 'student', 'status')
        }),
        (_('سیستم'), {
            'fields': ('marked_at',),
            'classes': ('collapse',)
        }),
    )
    
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
    readonly_fields = ['created_at', 'file_preview']
    fields = ['file', 'file_preview', 'created_at']
    
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
    list_display = ['teacher_name', 'unread_count', 'last_message_preview', 'last_message_time', 'open_chat']
    list_filter = ['status', 'created_at', 'teacher']
    search_fields = ['teacher__name', 'teacher__username', 'message_text']
    ordering = ['-created_at']
    change_list_template = 'admin/support_message_grouped_list.html'
    
    def changelist_view(self, request, extra_context=None):
        """نمایش پیام‌ها گروپ‌شده بر اساس معلم"""
        from django.db.models import Count, Max, Q
        from account.models import User
        from django.template.response import TemplateResponse
        
        teachers = User.objects.filter(role='teacher').annotate(
            message_count=Count('support_messages'),
            unread_count=Count('support_messages', filter=Q(support_messages__status='sent')),
            last_message_time=Max('support_messages__created_at')
        ).filter(message_count__gt=0).order_by('-last_message_time')
        
        context = self.admin_site.each_context(request)
        context.update({
            'teachers': teachers,
            'title': _('مدیریت پیام‌های پشتیبانی'),
        })
        
        return TemplateResponse(
            request,
            'admin/support_message_grouped_list.html',
            context
        )
    
    def get_urls(self):
        """اضافه کردن URL برای صفحه چت و API"""
        from django.urls import reverse
        urls = super().get_urls()
        custom_urls = [
            path('chat/<int:teacher_id>/', self.admin_site.admin_view(self.chat_detail_view), name='supportmessage_chat_detail'),
            path('api/messages/<int:teacher_id>/', self.admin_site.admin_view(self.api_get_messages), name='supportmessage_api_messages'),
            path('api/reply/', self.admin_site.admin_view(self.api_send_reply), name='supportmessage_api_reply'),
        ]
        return custom_urls + urls
    
    def chat_detail_view(self, request, teacher_id):
        """نمایش صفحه چت برای یک معلم خاص"""
        from account.models import User
        try:
            teacher = User.objects.get(id=teacher_id, role='teacher')
        except User.DoesNotExist:
            from django.http import Http404
            raise Http404(_("معلم یافت نشد"))
        
        SupportMessage.objects.filter(teacher=teacher, status='sent').update(status='read', read_at=timezone.now())
        
        context = self.admin_site.each_context(request)
        context['title'] = _('چت با {}').format(teacher.name or teacher.username)
        context['teacher'] = teacher
        context['messages'] = SupportMessage.objects.filter(teacher=teacher).order_by('created_at')
        return render(request, 'admin/support_message_detail_chat.html', context)
    
    def api_get_messages(self, request, teacher_id):
        """API برای دریافت پیام‌های چت"""
        from django.http import JsonResponse
        from account.models import User
        import json
        
        try:
            teacher = User.objects.get(id=teacher_id, role='teacher')
        except User.DoesNotExist:
            return JsonResponse({'error': 'Teacher not found'}, status=404)
        
        messages = SupportMessage.objects.filter(teacher=teacher).order_by('created_at')
        data = []
        for msg in messages:
            data.append({
                'id': msg.id,
                'sender_name': msg.sender.name if msg.sender else teacher.name,
                'sender_role': msg.sender.role if msg.sender else 'teacher',
                'message': msg.message_text,
                'created_at': msg.created_at.isoformat(),
                'attachments': [{'id': att.id, 'url': att.file.url} for att in msg.attachments.all()]
            })
        
        return JsonResponse({'messages': data})
    
    def api_send_reply(self, request):
        """API برای ارسال پاسخ"""
        from django.http import JsonResponse
        from account.models import User
        import json
        
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            data = json.loads(request.body)
            teacher_id = data.get('teacher_id')
            message_text = data.get('message')
            
            teacher = User.objects.get(id=teacher_id, role='teacher')
            
            msg = SupportMessage.objects.create(
                teacher=teacher,
                sender=request.user,
                message_text=message_text,
                status='sent'
            )
            
            return JsonResponse({
                'success': True,
                'message_id': msg.id,
                'created_at': msg.created_at.isoformat()
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def teacher_name(self, obj):
        """نام معلم"""
        return obj.name or obj.username
    teacher_name.short_description = _('معلم')
    
    def unread_count(self, obj):
        """تعداد پیام‌های خوانده‌نشده"""
        unread = obj.support_messages.filter(status='sent').count()
        if unread > 0:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
                unread
            )
        return '0'
    unread_count.short_description = _('پیام‌های جدید')
    
    def last_message_preview(self, obj):
        """پیش‌نمایش آخرین پیام"""
        last_msg = obj.support_messages.order_by('-created_at').first()
        if last_msg:
            if last_msg.message_text:
                text = last_msg.message_text[:40]
                if len(last_msg.message_text) > 40:
                    text += '...'
                return text
            else:
                return _('(فقط فایل)')
        return '-'
    last_message_preview.short_description = _('آخرین پیام')
    
    def last_message_time(self, obj):
        """زمان آخرین پیام"""
        last_msg = obj.support_messages.order_by('-created_at').first()
        if last_msg:
            import jdatetime
            created = jdatetime.datetime.fromgregorian(
                datetime=last_msg.created_at.replace(tzinfo=None)
            ).strftime('%H:%M %Y/%m/%d')
            return created
        return '-'
    last_message_time.short_description = _('آخرین فعالیت')
    
    def open_chat(self, obj):
        """دکمه باز کردن چت"""
        return format_html(
            '<a class="button" href="{}" style="background-color: #417690; color: white; text-decoration: none; padding: 5px 12px; border-radius: 4px; display: inline-block;">' 
            '💬 باز کردن چت</a>',
            reverse('admin:supportmessage_chat_detail', args=[obj.id])
        )
    open_chat.short_description = _('عملیات')