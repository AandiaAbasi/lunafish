from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import PsychologicalTest
from django.shortcuts import redirect


@admin.register(PsychologicalTest)
class PsychologicalTestAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "edit_button", "view_button")
    list_display_links = None

    def add_view(self, request, form_url='', extra_context=None):
        return redirect(reverse("recommendation:test_create"))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        from django.shortcuts import redirect
        return redirect(reverse('recommendation:test_edit', args=[object_id]))

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect
        if request.GET.get("add"):
            return redirect(reverse("recommendation:test_create"))
        return super().changelist_view(request, extra_context)

    def edit_button(self, obj):
        url = reverse("recommendation:test_edit", args=[obj.id])
        return format_html('<a class="button" href="{}">ویرایش</a>', url)

    edit_button.short_description = "ویرایش"

    def view_button(self, obj):
        url = reverse("recommendation:test_detail", args=[obj.id])
        return format_html('<a class="button" href="{}">مشاهده</a>', url)

    view_button.short_description = "مشاهده"