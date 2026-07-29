from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .admin_utils import format_jalali_datetime
from .models import GameLevel, GameStage, WordPair, WordTopic


class JalaliDateAdminMixin:
    readonly_fields = ('created_at_jalali', 'updated_at_jalali')

    @admin.display(description=_('تاریخ ایجاد'), ordering='created_at')
    def created_at_jalali(self, obj):
        return format_jalali_datetime(getattr(obj, 'created_at', None))

    @admin.display(description=_('آخرین تغییر'), ordering='updated_at')
    def updated_at_jalali(self, obj):
        return format_jalali_datetime(getattr(obj, 'updated_at', None))


class GameStageInline(admin.TabularInline):
    model = GameStage
    extra = 0
    fields = (
        'title',
        'code',
        'order',
        'min_difficulty',
        'max_difficulty',
        'pairs_per_round',
        'rounds_to_unlock',
        'max_mistakes',
        'is_active',
    )
    show_change_link = True


@admin.register(GameLevel)
class GameLevelAdmin(JalaliDateAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'code', 'audience', 'order', 'is_active', 'updated_at_jalali')
    list_filter = ('audience', 'is_active')
    search_fields = ('title', 'code', 'description')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'code': ('title',)}
    inlines = (GameStageInline,)
    ordering = ('order',)


@admin.register(GameStage)
class GameStageAdmin(JalaliDateAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'level',
        'order',
        'difficulty_range',
        'pairs_per_round',
        'rounds_to_unlock',
        'max_mistakes',
        'is_active',
        'updated_at_jalali',
    )
    list_filter = ('level', 'is_active')
    search_fields = ('title', 'code', 'level__title')
    list_editable = ('order', 'pairs_per_round', 'rounds_to_unlock', 'max_mistakes', 'is_active')
    prepopulated_fields = {'code': ('title',)}
    autocomplete_fields = ('level',)
    ordering = ('level__order', 'order')

    @admin.display(description=_('بازه سختی'))
    def difficulty_range(self, obj):
        return _('%(minimum)s تا %(maximum)s') % {
            'minimum': obj.min_difficulty,
            'maximum': obj.max_difficulty,
        }


@admin.register(WordTopic)
class WordTopicAdmin(JalaliDateAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'code', 'order', 'is_active', 'updated_at_jalali')
    list_filter = ('is_active',)
    search_fields = ('title', 'code')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'code': ('title',)}
    ordering = ('order', 'title')


@admin.register(WordPair)
class WordPairAdmin(JalaliDateAdminMixin, admin.ModelAdmin):
    list_display = ('en', 'fa', 'level', 'topic', 'difficulty', 'is_active', 'updated_at_jalali')
    list_filter = ('is_active', 'level', 'topic', 'difficulty')
    search_fields = ('en', 'fa', 'admin_note', 'level__title', 'topic__title')
    list_editable = ('difficulty', 'is_active')
    autocomplete_fields = ('level', 'topic')
    list_select_related = ('level', 'topic')
    ordering = ('level__order', 'difficulty', 'id')
    list_per_page = 50
