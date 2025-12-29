from django.contrib import admin
from .models import (
    TeacherAvailability, TeachingSubject, DiscountCode, ClassBooking,
    TeacherWallet, ClassRevenue, WithdrawalRequest, WalletTransaction,
    StudentTransaction, PlatformSettings
)


@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'date', 'start_time', 'end_time', 'price', 'is_available', 'is_booked']
    list_filter = ['teacher', 'date', 'is_available', 'is_booked', 'created_at']
    search_fields = ['teacher__name', 'teacher__username']
    ordering = ['-date', 'start_time']
    fieldsets = (
        ('معلم و تاریخ', {
            'fields': ('teacher', 'date')
        }),
        ('ساعات', {
            'fields': ('start_time', 'end_time')
        }),
        ('قیمت‌گذاری', {
            'fields': ('price',)
        }),
        ('وضعیت', {
            'fields': ('is_available', 'is_booked')
        }),
        ('یادداشت', {
            'fields': ('notes',)
        }),
    )

