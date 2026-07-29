from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from .models import GameStage, WordPair
from .selectors import get_sync_querysets, get_words_for_stage


@dataclass(frozen=True)
class SyncBundle:
    cutoff: datetime
    is_full: bool
    levels: object
    stages: object
    topics: object
    words: object


class LunaSyncService:
    @staticmethod
    def build(*, updated_after: datetime | None = None) -> SyncBundle:
        cutoff = timezone.now()
        querysets = get_sync_querysets(updated_after=updated_after, cutoff=cutoff)
        return SyncBundle(
            cutoff=cutoff,
            is_full=updated_after is None,
            levels=querysets["levels"],
            stages=querysets["stages"],
            topics=querysets["topics"],
            words=querysets["words"],
        )


class RoundBuilderService:
    MAX_REQUESTED_PAIRS = 12

    @classmethod
    def build(
        cls,
        *,
        stage: GameStage,
        requested_count: int | None = None,
        topic_code: str | None = None,
        exclude_ids: list[int] | None = None,
    ) -> list[WordPair]:
        count = requested_count or stage.pairs_per_round
        count = max(2, min(count, stage.pairs_per_round, cls.MAX_REQUESTED_PAIRS))
        exclude_ids = exclude_ids or []

        queryset = get_words_for_stage(stage, topic_code=topic_code)
        if exclude_ids:
            filtered_queryset = queryset.exclude(id__in=exclude_ids)
            if filtered_queryset.count() >= count:
                queryset = filtered_queryset

        candidate_ids = list(queryset.values_list("id", flat=True))
        if len(candidate_ids) < count:
            count = len(candidate_ids)

        selected_ids = random.sample(candidate_ids, count) if count else []
        selected_map = {
            item.id: item
            for item in WordPair.objects.filter(id__in=selected_ids).select_related("level", "topic")
        }
        return [selected_map[item_id] for item_id in selected_ids if item_id in selected_map]
