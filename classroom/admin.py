from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import (
    TeacherAvailability, TeachingSubject, DiscountCode, ClassBooking,
    TeacherWallet, ClassRevenue, WithdrawalRequest, WalletTransaction,
    StudentTransaction, PlatformSettings
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


# ===== TeacherAvailability Admin =====
@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'jalali_date', 'start_time', 'end_time', 'price', 'is_available_badge', 'is_booked_badge']
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
            'fields': ('price',)
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
                    
                    # بررسی تکراری نبودن
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
                            is_available=True
                        )
                        created += 1
                    
                    cursor += _dt.timedelta(minutes=(session_minutes + break_minutes))
                
                cur_date = cur_date + _dt.timedelta(days=1)
            
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
    is_available_badge.short_description = _('دسترسی‌پذیری')
    
    def is_booked_badge(self, obj):
        color = '#ff6b6b' if obj.is_booked else '#95e1d3'
        text = _('رزرو‌شده') if obj.is_booked else _('آزاد')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_booked_badge.short_description = _('وضعیت رزرو')
    
    def mark_available(self, request, queryset):
        """انتخاب بازه‌های زمانی برای دسترسی‌پذیری"""
        updated = queryset.filter(is_booked=False).update(is_available=True)
        self.message_user(request, _(f'{updated} بازه زمانی به عنوان دسترسی‌پذیر علامت‌گذاری شد'))
    mark_available.short_description = _('علامت‌گذاری به عنوان دسترسی‌پذیر')
    
    def mark_unavailable(self, request, queryset):
        """انتخاب بازه‌های زمانی برای غیردسترسی‌پذیری"""
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


# ===== TeachingSubject Admin =====
@admin.register(TeachingSubject)
class TeachingSubjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'level', 'is_active_badge']
    list_filter = ['level', 'is_active', 'created_at']
    search_fields = ['title', 'teacher__name', 'teacher__username']
    readonly_fields = ['created_at', 'updated_at']
    
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


# ===== DiscountCode Admin =====
@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type_display', 'discount_value', 'jalali_valid_from', 'is_active_badge', 'used_count_display']
    list_filter = ['discount_type', 'is_active', 'valid_from']
    search_fields = ['code']
    readonly_fields = ['used_count', 'created_at', 'updated_at', 'jalali_valid_from_display', 'jalali_valid_until_display']
    
    fieldsets = (
        (_('کد و نوع'), {
            'fields': ('code', 'discount_type')
        }),
        (_('مقدار تخفیف'), {
            'fields': ('discount_value', 'maximum_discount')
        }),
        (_('محدودیت‌ها'), {
            'fields': ('minimum_purchase', 'usage_limit', 'used_count')
        }),
        (_('تاریخ اعتبار'), {
            'fields': ('valid_from', 'valid_until', 'jalali_valid_from_display', 'jalali_valid_until_display')
        }),
        (_('توصیف'), {
            'fields': ('description',)
        }),
        (_('وضعیت'), {
            'fields': ('is_active',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def discount_type_display(self, obj):
        return obj.get_discount_type_display()
    discount_type_display.short_description = _('نوع تخفیف')
    
    def jalali_valid_from(self, obj):
        if obj.valid_from:
            jalali = jdatetime.datetime.fromgregorian(datetime=obj.valid_from)
            return jalali.strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_valid_from.short_description = _('معتبر از')
    
    def jalali_valid_from_display(self, obj):
        return self.jalali_valid_from(obj)
    jalali_valid_from_display.short_description = _('معتبر از (شمسی)')
    
    def jalali_valid_until_display(self, obj):
        if obj.valid_until:
            jalali = jdatetime.datetime.fromgregorian(datetime=obj.valid_until)
            return jalali.strftime('%Y/%m/%d %H:%M')
        return '-'
    jalali_valid_until_display.short_description = _('معتبر تا (شمسی)')
    
    def used_count_display(self, obj):
        limit = obj.usage_limit or '∞'
        return f"{obj.used_count}/{limit}"
    used_count_display.short_description = _('استفاده شده')
    
    def is_active_badge(self, obj):
        color = '#28a745' if obj.is_active else '#dc3545'
        text = _('فعال') if obj.is_active else _('غیرفعال')
        return format_html(f'<span style="background-color:{color}; color:white; padding:3px 8px; border-radius:3px;">{text}</span>')
    is_active_badge.short_description = _('وضعیت')


# ===== ClassBooking Admin =====
@admin.register(ClassBooking)
class ClassBookingAdmin(admin.ModelAdmin):
    list_display = ['subject', 'teacher', 'student', 'status_badge', 'final_price']
    list_filter = ['status', 'created_at']
    search_fields = ['subject__title', 'teacher__name', 'student__name']
    readonly_fields = ['created_at', 'updated_at']
    
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
    readonly_fields = ['balance', 'total_earned', 'total_withdrawn', 'verified_at', 'created_at', 'updated_at']
    
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
class ClassRevenueAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'booking', 'total_amount_display', 'teacher_share_display', 'is_confirmed_badge']
    list_filter = ['is_confirmed', 'is_settled', 'created_at']
    search_fields = ['teacher__name', 'booking__subject__title']
    readonly_fields = ['platform_fee', 'teacher_share', 'created_at', 'updated_at', 'confirmed_at', 'settled_at']
    
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
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'amount_display', 'status_badge', 'payment_method_display', 'jalali_created']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['teacher__name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'jalali_created_display']
    
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
class WalletTransactionAdmin(admin.ModelAdmin):
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
class StudentTransactionAdmin(admin.ModelAdmin):
    list_display = ['student', 'transaction_type_badge', 'amount_display', 'status_badge']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['student__name', 'student__username']
    readonly_fields = ['payment_date', 'created_at', 'updated_at']
    
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

