from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from django import forms
from .models import User, OTP, VerificationToken, AvatarTemplate, ParentProfile, ParentAppUsageLog
from .utils import send_sms, format_phone_display, send_sms_general
import random
import string
import jdatetime
from django.utils.translation import gettext_lazy as _


class TeacherCreationForm(forms.ModelForm):
    """Custom form for creating teachers without password requirement"""
    class Meta:
        model = User
        fields = ('username', 'email', 'phone')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(_("Email is required."))
        return email

    def clean_phone(self):
        """Convert phone to E164 format and make it required"""
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError(_("Phone number is required."))
        if phone.startswith('09'):
            import phonenumbers
            try:
                phone_obj = phonenumbers.parse(phone, "IR")
                phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
            except Exception:
                raise forms.ValidationError(_("Invalid phone number."))
        return phone


class RegularUserAdmin(BaseUserAdmin):
    """Admin for regular users only"""
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(role='user')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def created_at_display(self, obj):
        if obj.created_at:
            jalali = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return jalali.strftime('%Y/%m/%d %H:%M')
        return '-'
    created_at_display.short_description = _('Registration Date')
    
    def updated_at_display(self, obj):
        if obj.updated_at:
            jalali = jdatetime.datetime.fromgregorian(datetime=obj.updated_at)
            return jalali.strftime('%Y/%m/%d %H:%M')
        return '-'
    updated_at_display.short_description = _('Last Update')
    
    def last_login_jalali(self, obj):
        if obj.last_login:
            jalali = jdatetime.datetime.fromgregorian(datetime=obj.last_login)
            return jalali.strftime('%Y/%m/%d %H:%M')
        return '-'
    last_login_jalali.short_description = _('Last Login')
    
    def admin_actions(self, obj):
        edit_url = reverse('admin:account_regularuserproxy_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">{}</a>',
            edit_url, _('Edit')
        )
    admin_actions.short_description = _('Actions')
    
    list_display = ['username', 'email', 'phone', 'is_active', 'created_at_display', 'admin_actions']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Main Info'), {'fields': ('username', 'email', 'phone', 'role')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Personal Info'), {'fields': ('profile_photo_path', 'bio', 'name')}),
        (_('Dates'), {'fields': ('last_login_jalali', 'created_at_display', 'updated_at_display'), 'classes': ('collapse',)}),
    )
    
    readonly_fields = [
        'username', 'email', 'phone',
        'profile_photo_path',
        'created_at_display', 'updated_at_display', 'last_login_jalali'
    ]
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


class TeacherUserAdmin(BaseUserAdmin):
    add_form = TeacherCreationForm
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(role='teacher')
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def created_at_display(self, obj):
        if obj.created_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.created_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    created_at_display.short_description = _('Registration Date')
    
    def updated_at_display(self, obj):
        if obj.updated_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.updated_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    updated_at_display.short_description = _('Last Update')
    
    def last_login_jalali(self, obj):
        if obj.last_login:
            return jdatetime.datetime.fromgregorian(datetime=obj.last_login).strftime('%Y/%m/%d %H:%M')
        return '-'
    last_login_jalali.short_description = _('Last Login')
    
    def teacher_verification_requested_at_jalali(self, obj):
        if obj.teacher_verification_requested_at:
            return jdatetime.datetime.fromgregorian(datetime=obj.teacher_verification_requested_at).strftime('%Y/%m/%d %H:%M')
        return '-'
    teacher_verification_requested_at_jalali.short_description = _('Verification Requested At')
    
    def admin_actions(self, obj):
        edit_url = reverse('admin:account_teacheruserproxy_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">{}</a>',
            edit_url, _('Edit')
        )
    admin_actions.short_description = _('Actions')
    
    list_display = ['username', 'email', 'phone', 'is_teacher_verified', 'is_active', 'created_at_display', 'admin_actions']
    list_filter = ['is_teacher_verified', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Main Info'), {'fields': ('name', 'username', 'email', 'phone', 'role')}),
        (_('Teacher Info'), {'fields': ('is_teacher_verified', 'teacher_verification_requested_at_jalali')}),
        (_('Financial Settings'), {'fields': ('commission_rate_override',), 'description': _('Custom commission rate for this teacher. If empty, default rate applies.')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Personal Info'), {'fields': ('profile_photo_path', 'bio')}),
        (_('Dates'), {'fields': ('last_login_jalali', 'created_at_display', 'updated_at_display'), 'classes': ('collapse',)}),
    )
    
    readonly_fields = [
        'username', 'email', 'phone',
        'teacher_verification_requested_at_jalali',
        'profile_photo_path',
        'created_at_display', 'updated_at_display', 'last_login_jalali'
    ]
    
    add_fieldsets = (
        (_('Add New Teacher'), {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone'),
            'description': _('Password will be auto-generated and sent to the teacher via SMS.')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        
        if obj.phone and obj.phone.startswith('09'):
            import phonenumbers
            try:
                phone_obj = phonenumbers.parse(obj.phone, "IR")
                obj.phone = phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
            except Exception as e:
                messages.warning(request, _('Phone conversion error: %s') % str(e))
        
        if not change:
            obj.role = 'teacher'
        
        if is_new:
            password = ''.join(random.choices(string.digits, k=6))
            obj.set_password(password)
            super().save_model(request, obj, form, change)
            
            if obj.phone:
                try:
                    phone_display = format_phone_display(obj.phone)
                    sms_phone = obj.phone
                    if obj.phone.startswith('+98'):
                        import phonenumbers
                        phone_obj = phonenumbers.parse(obj.phone, None)
                        sms_phone = '0' + str(phone_obj.national_number)
                    
                    send_sms_general(
                        sms_phone,
                        "855282",
                        [
                            {"name": "NAME", "value": obj.username},
                            {"name": "PHONE", "value": phone_display},
                            {"name": "PASS", "value": password}
                        ]
                    )
                    messages.success(
                        request,
                        _('Teacher successfully created. Password {password} sent to {phone}.').format(password=password, phone=phone_display)
                    )
                except Exception as e:
                    messages.warning(
                        request,
                        _('Teacher created but SMS failed. Password: {password}').format(password=password)
                    )
        else:
            super().save_model(request, obj, form, change)


# Create proxy models for separate admin entries
class RegularUserProxy(User):
    class Meta:
        proxy = True
        verbose_name = _('User')
        verbose_name_plural = _('User Management')


class TeacherUserProxy(User):
    class Meta:
        proxy = True
        verbose_name = _('Teacher')
        verbose_name_plural = _('Teacher Management')
        

# Register proxy models with separate admins
admin.site.register(RegularUserProxy, RegularUserAdmin)
admin.site.register(TeacherUserProxy, TeacherUserAdmin)

# Hide JWT token models from admin
try:
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
    admin.site.unregister(OutstandingToken)
    admin.site.unregister(BlacklistedToken)
except Exception:
    pass

# Hide authtoken Token model from admin
try:
    from rest_framework.authtoken.models import TokenProxy
    admin.site.unregister(TokenProxy)
except Exception:
    pass


# ========== Avatar Templates ==========
@admin.register(AvatarTemplate)
class AvatarTemplateAdmin(admin.ModelAdmin):
    """Admin interface for avatar templates"""
    list_display = ['id', 'display_image', 'created_at', 'admin_actions']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'display_image']
    
    fieldsets = (
        (_("Avatar Image"), {
            'fields': ('image', 'display_image')
        }),
        (_("Metadata"), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_image(self, obj):
        """Display image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" width="150" height="150" style="border-radius: 10px;" />',
                obj.image.url
            )
        return "-"
    display_image.short_description = _("Preview")

    def admin_actions(self, obj):
        edit_url = reverse('admin:account_avatartemplate_change', args=[obj.id])
        delete_url = reverse('admin:account_avatartemplate_delete', args=[obj.id])
        
        return format_html(
            '<a href="{}" class="button" style="margin-right:10px; padding:5px;">✏️ {}</a>'
            '<a href="{}" class="button" style="margin-right: 5px; padding:5px; background-color: #ba2121;">🗑 {}</a>',
            edit_url, _("Edit"), delete_url, _("Delete")
        )
    admin_actions.short_description = _("Actions")


# ========== Parent Portal Admin ==========
class ParentProfileInline(admin.TabularInline):
    """Inline admin for parent profiles (for student's parents)"""
    model = ParentProfile
    extra = 0
    fields = ('parent_name', 'phone', 'email', 'can_view_class_history', 'can_view_payments', 'can_select_teacher', 'can_set_usage_time', 'is_active')
    readonly_fields = ('created_at', 'updated_at')


class ParentProfileAdmin(admin.ModelAdmin):
    """Admin for managing parent profiles"""
    list_display = ('parent_name', 'student_link', 'phone', 'is_active', 'last_login_at', 'created_at')
    list_filter = ('is_active', 'can_view_class_history', 'can_view_payments', 'can_select_teacher', 'can_set_usage_time', 'created_at')
    search_fields = ('parent_name', 'phone', 'email', 'student__name', 'student__username')
    readonly_fields = ('created_at', 'updated_at', 'last_login_at')
    
    fieldsets = (
        (_('Student & Contact'), {
            'fields': ('student', 'parent_name', 'phone', 'email')
        }),
        (_('Permissions'), {
            'fields': ('can_view_class_history', 'can_view_payments', 'can_select_teacher', 'can_set_usage_time')
        }),
        (_('Usage Time Control'), {
            'fields': ('daily_usage_limit_minutes', 'allowed_start_time', 'allowed_end_time'),
            'classes': ('collapse',)
        }),
        (_('Status'), {
            'fields': ('is_active', 'last_login_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def student_link(self, obj):
        """Link to student"""
        url = reverse('admin:account_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.name or obj.student.username)
    student_link.short_description = _('Student')
    
    actions = ['activate_parents', 'deactivate_parents']
    
    def activate_parents(self, request, queryset):
        """Activate selected parents"""
        count = queryset.update(is_active=True)
        messages.success(request, _("{} parent profiles activated").format(count))
    activate_parents.short_description = _("Activate selected parents")
    
    def deactivate_parents(self, request, queryset):
        """Deactivate selected parents"""
        count = queryset.update(is_active=False)
        messages.success(request, _("{} parent profiles deactivated").format(count))
    deactivate_parents.short_description = _("Deactivate selected parents")


class ParentAppUsageLogAdmin(admin.ModelAdmin):
    """Admin for viewing parent usage logs"""
    list_display = ('parent_link', 'date', 'total_minutes', 'session_count')
    list_filter = ('date', 'created_at')
    search_fields = ('parent__parent_name', 'parent__student__name', 'parent__student__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        (_('Parent'), {
            'fields': ('parent',)
        }),
        (_('Usage'), {
            'fields': ('date', 'total_minutes', 'session_count')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def parent_link(self, obj):
        """Link to parent"""
        url = reverse('admin:account_parentprofile_change', args=[obj.parent.id])
        return format_html('<a href="{}">{}</a>', url, obj.parent.parent_name)
    parent_link.short_description = _('Parent')
    
    def has_add_permission(self, request):
        """Usage logs are created automatically"""
        return False


# Register Parent Admin
admin.site.register(ParentProfile, ParentProfileAdmin)
admin.site.register(ParentAppUsageLog, ParentAppUsageLogAdmin)
