from rest_framework import serializers

from .models import GameLevel, GameStage, WordPair, WordTopic


class GameLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameLevel
        fields = (
            "id",
            "code",
            "title",
            "description",
            "audience",
            "order",
            "is_active",
            "updated_at",
        )


class GameStageSerializer(serializers.ModelSerializer):
    level = serializers.SlugRelatedField(read_only=True, slug_field="code")

    class Meta:
        model = GameStage
        fields = (
            "id",
            "code",
            "title",
            "level",
            "order",
            "min_difficulty",
            "max_difficulty",
            "pairs_per_round",
            "rounds_to_unlock",
            "max_mistakes",
            "time_limit_seconds",
            "is_active",
            "updated_at",
        )


class WordTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordTopic
        fields = ("id", "code", "title", "order", "is_active", "updated_at")


class WordPairSerializer(serializers.ModelSerializer):
    level = serializers.SlugRelatedField(read_only=True, slug_field="code")
    topic = serializers.SlugRelatedField(read_only=True, slug_field="code")

    class Meta:
        model = WordPair
        fields = (
            "id",
            "en",
            "fa",
            "level",
            "topic",
            "difficulty",
            "is_active",
            "updated_at",
        )


class SyncQuerySerializer(serializers.Serializer):
    updated_after = serializers.DateTimeField(required=False)


class StageListQuerySerializer(serializers.Serializer):
    level = serializers.SlugField(required=False)


class WordListQuerySerializer(serializers.Serializer):
    level = serializers.SlugField(required=False)
    topic = serializers.SlugField(required=False)
    min_difficulty = serializers.IntegerField(required=False, min_value=1, max_value=100)
    max_difficulty = serializers.IntegerField(required=False, min_value=1, max_value=100)

    def validate(self, attrs):
        min_value = attrs.get("min_difficulty")
        max_value = attrs.get("max_difficulty")
        if min_value is not None and max_value is not None and min_value > max_value:
            raise serializers.ValidationError("min_difficulty نمی‌تواند از max_difficulty بزرگ‌تر باشد.")
        return attrs


class RoundQuerySerializer(serializers.Serializer):
    stage = serializers.SlugField()
    count = serializers.IntegerField(required=False, min_value=2, max_value=12)
    topic = serializers.SlugField(required=False)
    exclude = serializers.CharField(required=False, allow_blank=True)

    def validate_exclude(self, value):
        if not value:
            return []

        result = []
        for raw_item in value.split(","):
            raw_item = raw_item.strip()
            if not raw_item:
                continue
            try:
                result.append(int(raw_item))
            except ValueError as exc:
                raise serializers.ValidationError("exclude باید فهرستی از شناسه‌های عددی باشد.") from exc
        return result[:100]
