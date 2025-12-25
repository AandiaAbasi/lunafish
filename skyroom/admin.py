from django.contrib import admin
from .models import Service, Room, SkyroomUser, RoomUserAccess, LoginUrl


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'skyroom_id', 'status', 'user_limit', 'video_limit', 'updated_at_display']
    list_filter = ['status', 'updated_at_display']
    search_fields = ['title', 'skyroom_id']
    readonly_fields = ['created_at_display', 'updated_at_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('skyroom_id', 'title', 'status')
        }),
        ('Limits', {
            'fields': ('user_limit', 'video_limit', 'time_limit')
        }),
        ('Usage', {
            'fields': ('time_usage',)
        }),
        ('Timestamps', {
            'fields': ('start_time', 'stop_time', 'created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['title', 'name', 'skyroom_id', 'service', 'status', 'max_users', 'updated_at_display']
    list_filter = ['status', 'service', 'guest_login', 'op_login_first', 'updated_at_display']
    search_fields = ['title', 'name', 'skyroom_id']
    readonly_fields = ['created_at_display', 'updated_at_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('skyroom_id', 'service', 'name', 'title', 'description', 'status')
        }),
        ('Access Control', {
            'fields': ('guest_login', 'guest_limit', 'op_login_first')
        }),
        ('Limits', {
            'fields': ('max_users', 'session_duration', 'time_limit')
        }),
        ('Usage', {
            'fields': ('time_usage', 'time_total')
        }),
        ('Timestamps', {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SkyroomUser)
class SkyroomUserAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'username', 'skyroom_id', 'status', 'is_public', 'updated_at_display']
    list_filter = ['status', 'is_public', 'gender', 'updated_at_display']
    search_fields = ['username', 'nickname', 'email', 'skyroom_id']
    readonly_fields = ['created_at_display', 'updated_at_display']
    
    fieldsets = (
        ('Credentials', {
            'fields': ('skyroom_id', 'username', 'password')
        }),
        ('Personal Information', {
            'fields': ('nickname', 'fname', 'lname', 'gender', 'email')
        }),
        ('Status & Access', {
            'fields': ('status', 'is_public', 'concurrent')
        }),
        ('Time Management', {
            'fields': ('time_limit', 'time_usage', 'time_total', 'expiry_date')
        }),
        ('Timestamps', {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RoomUserAccess)
class RoomUserAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'access', 'created_at_display', 'updated_at_display']
    list_filter = ['access', 'created_at_display', 'room']
    search_fields = ['user__username', 'room__name']
    readonly_fields = ['created_at_display', 'updated_at_display']
    
    fieldsets = (
        ('Access Information', {
            'fields': ('room', 'user', 'access')
        }),
        ('Timestamps', {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoginUrl)
class LoginUrlAdmin(admin.ModelAdmin):
    list_display = ['room', 'user_id', 'nickname', 'access', 'is_active', 'expires_at']
    list_filter = ['is_active', 'access', 'created_at_display', 'room']
    search_fields = ['user_id', 'room__name', 'nickname']
    readonly_fields = ['created_at_display', 'updated_at_display', 'url']
    
    fieldsets = (
        ('Room & User', {
            'fields': ('room', 'user_id', 'nickname')
        }),
        ('Access Settings', {
            'fields': ('access', 'concurrent', 'ttl', 'is_active')
        }),
        ('URL', {
            'fields': ('url',),
            'classes': ('collapse',)
        }),
        ('Expiry', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at_display', 'updated_at_display'),
            'classes': ('collapse',)
        }),
    )
