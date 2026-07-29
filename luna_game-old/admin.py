from django.contrib import admin

from .models import GameLevel, GameStage, WordPair, WordTopic


class GameStageInline(admin.TabularInline):
    model = GameStage
    extra = 0
    fields = (
        "title",
        "code",
        "order",
        "min_difficulty",
        "max_difficulty",
        "pairs_per_round",
        "rounds_to_unlock",
        "max_mistakes",
        "is_active",
    )
    show_change_link = True


@admin.register(GameLevel)
class GameLevelAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "audience", "order", "is_active", "updated_at")
    list_filter = ("audience", "is_active")
    search_fields = ("title", "code", "description")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"code": ("title",)}
    inlines = (GameStageInline,)
    ordering = ("order",)


@admin.register(GameStage)
class GameStageAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "level",
        "order",
        "difficulty_range",
        "pairs_per_round",
        "rounds_to_unlock",
        "max_mistakes",
        "is_active",
    )
    list_filter = ("level", "is_active")
    search_fields = ("title", "code", "level__title")
    list_editable = ("order", "pairs_per_round", "rounds_to_unlock", "max_mistakes", "is_active")
    prepopulated_fields = {"code": ("title",)}
    autocomplete_fields = ("level",)
    ordering = ("level__order", "order")

    @admin.display(description="بازه سختی")
    def difficulty_range(self, obj):
        return f"{obj.min_difficulty} تا {obj.max_difficulty}"


@admin.register(WordTopic)
class WordTopicAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "order", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "code")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"code": ("title",)}
    ordering = ("order", "title")


@admin.register(WordPair)
class WordPairAdmin(admin.ModelAdmin):
    list_display = ("en", "fa", "level", "topic", "difficulty", "is_active", "updated_at")
    list_filter = ("is_active", "level", "topic", "difficulty")
    search_fields = ("en", "fa", "admin_note", "level__title", "topic__title")
    list_editable = ("difficulty", "is_active")
    autocomplete_fields = ("level", "topic")
    list_select_related = ("level", "topic")
    ordering = ("level__order", "difficulty", "id")
    list_per_page = 50
