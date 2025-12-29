from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
from .models import Field, FieldDetail, CategoryField, Order, OrderDetail
import json


# ===== Field Admin (سؤال) =====
@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ['title', 'type_badge', 'is_required_badge', 'sort']
    list_filter = ['type', 'is_required', 'created_at']
    search_fields = ['title', 'des']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('اطلاعات پایه'), {
            'fields': ('title', 'type', 'sort')
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
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def type_badge(self, obj):
        colors = {
            'text': '#007bff',
            'choice': '#28a745',
            'multichoice': '#ffc107',
            'essay': '#17a2b8',
            'matching': '#6c757d',
            'ordering': '#e83e8c'
        }
        color = colors.get(obj.type, '#6c757d')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, obj.type)
    type_badge.short_description = _('نوع سؤال')
    
    def is_required_badge(self, obj):
        if obj.is_required is None:
            return '-'
        color = '#28a745' if obj.is_required else '#dc3545'
        text = _('الزامی') if obj.is_required else _('اختیاری')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_required_badge.short_description = _('الزامی/اختیاری')
    
    def has_delete_permission(self, request, obj=None):
        """منع حذف سؤالات که در نتایج استفاده شده‌اند"""
        if obj and obj.order_details.exists():
            return False
        return super().has_delete_permission(request, obj)


# ===== FieldDetail Admin (گزینه) =====
class FieldDetailInline(admin.TabularInline):
    model = FieldDetail
    extra = 1
    fields = ['title', 'second_title', 'is_correct_badge', 'sort', 'image_path']
    readonly_fields = ['is_correct_badge', 'created_at', 'updated_at']
    
    def is_correct_badge(self, obj):
        if obj.is_correct == -1:
            return '-'
        color = '#28a745' if obj.is_correct == 1 else '#dc3545'
        text = _('صحیح') if obj.is_correct == 1 else _('غلط')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_correct_badge.short_description = _('صحیح؟')


@admin.register(FieldDetail)
class FieldDetailAdmin(admin.ModelAdmin):
    list_display = ['field', 'title', 'is_correct_display', 'sort']
    list_filter = ['is_correct', 'created_at']
    search_fields = ['title', 'field__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('سؤال'), {
            'fields': ('field',)
        }),
        (_('عنوان و توصیف'), {
            'fields': ('title', 'second_title', 'des')
        }),
        (_('درستی'), {
            'fields': ('is_correct',)
        }),
        (_('رسانه'), {
            'fields': ('image_path',)
        }),
        (_('راهنمایی'), {
            'fields': ('guide',)
        }),
        (_('ترتیب'), {
            'fields': ('sort',)
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_correct_display(self, obj):
        if obj.is_correct == -1:
            return format_html('<span style="color:#6c757d">-</span>')
        color = '#28a745' if obj.is_correct == 1 else '#dc3545'
        text = _('✓ صحیح') if obj.is_correct == 1 else _('✗ غلط')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_correct_display.short_description = _('درستی')


# ===== CategoryField Admin (آزمون) =====
@admin.register(CategoryField)
class CategoryFieldAdmin(admin.ModelAdmin):
    list_display = ['teachingsubject', 'field', 'step', 'sort', 'is_conditional_badge']
    list_filter = ['teachingsubject', 'is_conditional', 'created_at']
    search_fields = ['field__title', 'teachingsubject__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('کلاس و سؤال'), {
            'fields': ('teachingsubject', 'field')
        }),
        (_('ترتیب'), {
            'fields': ('step', 'sort')
        }),
        (_('شرط'), {
            'fields': ('is_conditional', 'type')
        }),
        (_('اطلاعات سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_conditional_badge(self, obj):
        color = '#ffc107' if obj.is_conditional else '#28a745'
        text = _('شرطی') if obj.is_conditional else _('عادی')
        return format_html('<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>', color, text)
    is_conditional_badge.short_description = _('نوع')


# ===== Order Admin (تلاش) =====
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'teachingsubject', 'score_display', 'progress_badge']
    list_filter = ['teachingsubject', 'created_at']
    search_fields = ['user__name', 'user__username', 'teachingsubject__title']
    readonly_fields = ['created_at', 'updated_at', 'score_display', 'progress_display', 'user', 'teachingsubject', 'score', 'correct', 'incorrect']
    
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
        (_('اطلاعات سیستم'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        """فقط نمایش جزئیات، بدون ویرایش"""
        return False
    
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


# ===== OrderDetail Admin (پاسخ) =====
@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ['order', 'field', 'value_display', 'score_badge']
    list_filter = ['order__teachingsubject', 'created_at']
    search_fields = ['field__title', 'order__user__name']
    readonly_fields = ['order', 'field', 'field_detail', 'value', 'score', 'created_at', 'updated_at']
    
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
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        """فقط نمایش جزئیات، بدون ویرایش"""
        return False
    
    def value_display(self, obj):
        return obj.value or '-'
    value_display.short_description = _('پاسخ')
    
    def score_badge(self, obj):
        color = '#28a745' if obj.score > 0 else '#dc3545'
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color, obj.score
        )
    score_badge.short_description = _('امتیاز')
