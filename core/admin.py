from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import *
from account.models import User
import jdatetime
from django.db.models import Count

original_index = admin.site.index

def custom_index(request, extra_context=None):
    extra_context = extra_context or {}

    stats = {
        "users": User.objects.filter(role='user').count(),
        "teachers": User.objects.filter(role='teacher').count(),
        "articles": Article.objects.count(),
        "messages": ContactMessage.objects.count(),
    }

    extra_context.update({
        "stats": stats,
    })

    return original_index(request, extra_context=extra_context)

admin.site.index = custom_index


@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    list_display = ("title", "image_tag", "created_at_display", "updated_at_display", "admin_actions")
    search_fields = ("title", "content", "title_fa", "content_fa", "title_en", "content_en")
    ordering = ("-created_at",)
    
    fieldsets = (
        (_("Title"), {"fields": ("title", "title_en", "title_fa")}),
        (_("Media"), {"fields": ("image",)}), 
        (_("Content"), {"fields": ("content", "content_en", "content_fa")}),
    )

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="border-radius: 10px;"/>', obj.image.url)
        return format_html("<span style='color: red;'>{}</span>", _("No image"))
    image_tag.short_description = _("Image preview")
        
    def admin_actions(self, obj):
        edit_url = reverse('admin:core_about_change', args=[obj.id])
        delete_url = reverse('admin:core_about_delete', args=[obj.id])
        
        return format_html(
            '<a href="{}" class="button" style="margin-right:10px; padding:5px;">✏️ {}</a>'
            '<a href="{}" class="button" style="margin-right: 5px; padding:5px; background-color: #ba2121;">🗑 {}</a>',
            edit_url, _("Edit"), delete_url, _("Delete")
        )
    admin_actions.short_description = _("Actions")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at_display", "updated_at_display", "admin_actions")
    search_fields = ("title", "content", "title_fa", "content_fa", "title_en", "content_en")
    ordering = ("-created_at",)
    fieldsets = (
        (_("Title"), {"fields": ("title", "title_en", "title_fa")}),
        (_("Content"), {"fields": ("content", "content_en", "content_fa")}),
    )

    def admin_actions(self, obj):
        edit_url = reverse('admin:core_term_change', args=[obj.id])
        delete_url = reverse('admin:core_term_delete', args=[obj.id])
        
        return format_html(
            '<a href="{}" class="button" style="margin-right:10px; padding:5px;">✏️ {}</a>'
            '<a href="{}" class="button" style="margin-right: 5px; padding:5px; background-color: #ba2121;">🗑 {}</a>',
            edit_url, _("Edit"), delete_url, _("Delete")
        )
    admin_actions.short_description = _("Actions")


@admin.register(Privacy)
class PrivacyAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at_display", "updated_at_display", "admin_actions")
    search_fields = ("title", "content", "title_fa", "content_fa", "title_en", "content_en")
    ordering = ("-created_at",)
    fieldsets = (
        (_("Title"), {"fields": ("title", "title_en", "title_fa")}),
        (_("Content"), {"fields": ("content", "content_en", "content_fa")}),
    )

    def admin_actions(self, obj):
        edit_url = reverse('admin:core_privacy_change', args=[obj.id])
        delete_url = reverse('admin:core_privacy_delete', args=[obj.id])
        
        return format_html(
            '<a href="{}" class="button" style="margin-right:10px; padding:5px;">✏️ {}</a>'
            '<a href="{}" class="button" style="margin-right: 5px; padding:5px; background-color: #ba2121;">🗑 {}</a>',
            edit_url, _("Edit"), delete_url, _("Delete")
        )
    admin_actions.short_description = _("Actions")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "value", "link", "created_at_display", "admin_actions")
    list_filter = ["type"]
    search_fields = ("title", "value", "title_fa", "value_fa", "title_en", "value_en")
    ordering = ("-created_at",)
    fieldsets = (
        (_("Contact Details"), {"fields": ("title", "title_en", "title_fa", "link", "value", "value_en", "value_fa", "type")}),
    )

    def admin_actions(self, obj):
        edit_url = reverse('admin:core_contact_change', args=[obj.id])
        delete_url = reverse('admin:core_contact_delete', args=[obj.id])
        
        return format_html(
            '<a href="{}" class="button" style="margin-right:10px; padding:5px;">✏️ {}</a>'
            '<a href="{}" class="button" style="margin-right: 5px; padding:5px; background-color: #ba2121;">🗑 {}</a>',
            edit_url, _("Edit"), delete_url, _("Delete")
        )
    admin_actions.short_description = _("Actions")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "subject", "message", "created_at_display", "view_details")
    readonly_fields = ("name", "phone", "subject", "message")
    search_fields = ("name", "phone", "subject")
    actions = None
    list_display_links = ("view_details",)
    list_filter = ("created_at",)
    ordering = ("-created_at",)

    fieldsets = (
        (_("Contact Information"), {"fields": ("name", "phone")}),
        (_("Message Details"), {"fields": ("subject", "message")}),
    )
    
    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def view_details(self, obj):
        url = reverse("admin:core_contactmessage_change", args=[obj.id])
        return format_html('<a href="{}"> {}</a>', url, _("View details"))
    view_details.short_description = _("View details")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "image_tag", "created_at_display", "updated_at_display", "admin_actions")
    search_fields = ("title", "content", "title_fa", "content_fa", "title_en", "content_en")
    list_filter = ("created_at", "updated_at")
    ordering = ("-created_at",)
    readonly_fields = ("image_tag",)
    fieldsets = (
        (_("Main Information"), {"fields": ("title", "title_en", "title_fa", "short_description", "short_description_en", "short_description_fa", "content", "content_en", "content_fa")}),
        (_("Media"), {"fields": ("image", "image_tag")}),
    )

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="border-radius: 10px;"/>'.format(obj.image.url))
        return _("No image")
    image_tag.short_description = _("Image preview")
        
    def admin_actions(self, obj):
        edit_url = reverse('admin:core_article_change', args=[obj.id])
        delete_url = reverse('admin:core_article_delete', args=[obj.id])
        
        return format_html(
            '<a href="{}" class="button" style="margin-right:10px; padding:5px;">✏️ {}</a>'
            '<a href="{}" class="button" style="margin-right: 5px; padding:5px; background-color: #ba2121;">🗑 {}</a>',
            edit_url, _("Edit"), delete_url, _("Delete")
        )
    admin_actions.short_description = _("Actions")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "updated_at_display", "admin_actions")
    search_fields = ("question", "answer", "question_fa", "answer_fa", "question_en", "answer_en")
    list_filter = ("is_active", "created_at")
    ordering = ("-created_at",)
    fieldsets = (
        (_("Question"), {"fields": ("question", "question_en", "question_fa")}),
        (_("Answer"), {"fields": ("answer", "answer_en", "answer_fa", "is_active")}),
    )
        
    def admin_actions(self, obj):
        edit_url = reverse('admin:core_faq_change', args=[obj.id])
        delete_url = reverse('admin:core_faq_delete', args=[obj.id])
        
        return format_html(
            '<a href="{}" class="button" style="margin-right:10px; padding:5px;">✏️ {}</a>'
            '<a href="{}" class="button" style="margin-right: 5px; padding:5px; background-color: #ba2121;">🗑 {}</a>',
            edit_url, _("Edit"), delete_url, _("Delete")
        )
    admin_actions.short_description = _("Actions")


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = (
        "title", 
        "placement_display", 
        "image_tag", 
        "is_active_display",
        "sort", 
        "created_at_display", 
        "admin_actions"
    )
    search_fields = ("title", "sub_title", "link", "title_fa", "sub_title_fa", "title_en", "sub_title_en")
    list_filter = ("placement", "is_active", "created_at")
    ordering = ("placement", "sort", "-created_at")
    list_editable = ("sort",)
    readonly_fields = ("created_at_display", "updated_at_display")
    
    fieldsets = (
        (_("Main Information"), {
            "fields": ("title", "title_en", "title_fa", "sub_title", "sub_title_en", "sub_title_fa", "placement", "link")
        }),
        (_("Media"), {
            "fields": ("image",)
        }),
        (_("Display Settings"), {
            "fields": ("is_active", "sort")
        }),
        (_("History"), {
            "fields": ("created_at_display", "updated_at_display"),
            "classes": ("collapse",)
        }),
    )

    def image_tag(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" style="border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"/>',
                obj.image.url
            )
        return format_html("<span style='color: red;'>{}</span>", _("No image"))
    image_tag.short_description = _("Preview")
    
    def placement_display(self, obj):
        colors = {
            'home': '#28a745',
            'app_home': '#fd7e14',
        }
        color = colors.get(obj.placement, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_placement_display()
        )
    placement_display.short_description = _("Placement")
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ {}</span>',
                _("Active")
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ {}</span>',
                _("Inactive")
            )
    is_active_display.short_description = _("Status")
        
    def admin_actions(self, obj):
        edit_url = reverse('admin:core_banner_change', args=[obj.id])
        delete_url = reverse('admin:core_banner_delete', args=[obj.id])
        return format_html(
            '<a href="{}" class="button" style="margin-right:10px; padding:5px;">✏️ {}</a>'
            '<a href="{}" class="button" style="margin-right: 5px; padding:5px; background-color: #ba2121;">🗑 {}</a>',
            edit_url, _("Edit"), delete_url, _("Delete")
        )
    admin_actions.short_description = _("Actions")
