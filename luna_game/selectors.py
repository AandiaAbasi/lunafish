from __future__ import annotations

from datetime import datetime

from django.db.models import QuerySet

from .models import GameLevel, GameStage, WordPair, WordTopic


def get_active_levels() -> QuerySet[GameLevel]:
    return GameLevel.objects.active().order_by("order", "id")


def get_active_stages(level_code: str | None = None) -> QuerySet[GameStage]:
    queryset = GameStage.objects.active().filter(level__is_active=True).select_related("level")
    if level_code:
        queryset = queryset.filter(level__code=level_code)
    return queryset.order_by("level__order", "order", "id")


def get_active_topics() -> QuerySet[WordTopic]:
    return WordTopic.objects.active().order_by("order", "title", "id")


def get_stage_by_code(stage_code: str) -> GameStage:
    return get_active_stages().get(code=stage_code)


def get_words_for_stage(stage: GameStage, *, topic_code: str | None = None) -> QuerySet[WordPair]:
    queryset = (
        WordPair.objects.active()
        .filter(
            level=stage.level,
            level__is_active=True,
            difficulty__gte=stage.min_difficulty,
            difficulty__lte=stage.max_difficulty,
        )
        .select_related("level", "topic")
    )
    if topic_code:
        queryset = queryset.filter(topic__code=topic_code, topic__is_active=True)
    return queryset.order_by("id")


def get_words(
    *,
    level_code: str | None = None,
    topic_code: str | None = None,
    min_difficulty: int | None = None,
    max_difficulty: int | None = None,
) -> QuerySet[WordPair]:
    queryset = WordPair.objects.active().filter(level__is_active=True).select_related("level", "topic")
    if level_code:
        queryset = queryset.filter(level__code=level_code)
    if topic_code:
        queryset = queryset.filter(topic__code=topic_code, topic__is_active=True)
    if min_difficulty is not None:
        queryset = queryset.filter(difficulty__gte=min_difficulty)
    if max_difficulty is not None:
        queryset = queryset.filter(difficulty__lte=max_difficulty)
    return queryset.order_by("level__order", "difficulty", "id")


def get_sync_querysets(*, updated_after: datetime | None, cutoff: datetime):
    models_and_querysets = {
        "levels": GameLevel.objects.all(),
        "stages": GameStage.objects.select_related("level").all(),
        "topics": WordTopic.objects.all(),
        "words": WordPair.objects.select_related("level", "topic").all(),
    }

    if updated_after is None:
        return {
            "levels": models_and_querysets["levels"].filter(is_active=True, updated_at__lte=cutoff),
            "stages": models_and_querysets["stages"].filter(
                is_active=True,
                level__is_active=True,
                updated_at__lte=cutoff,
            ),
            "topics": models_and_querysets["topics"].filter(is_active=True, updated_at__lte=cutoff),
            "words": models_and_querysets["words"].filter(
                is_active=True,
                level__is_active=True,
                updated_at__lte=cutoff,
            ),
        }

    return {
        key: queryset.filter(updated_at__gt=updated_after, updated_at__lte=cutoff)
        for key, queryset in models_and_querysets.items()
    }
