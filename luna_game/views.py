from django.http import Http404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GameStage
from .selectors import get_active_levels, get_active_stages, get_active_topics, get_words
from .serializers import (
    GameLevelSerializer,
    GameStageSerializer,
    RoundQuerySerializer,
    StageListQuerySerializer,
    SyncQuerySerializer,
    WordListQuerySerializer,
    WordPairSerializer,
    WordTopicSerializer,
)
from .services import LunaSyncService, RoundBuilderService


class PublicLunaAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()


class GameManifestAPIView(PublicLunaAPIView):
    def get(self, request):
        bundle = LunaSyncService.build()
        return Response(
            {
                "cursor": bundle.cutoff.isoformat(),
                "counts": {
                    "levels": bundle.levels.count(),
                    "stages": bundle.stages.count(),
                    "topics": bundle.topics.count(),
                    "words": bundle.words.count(),
                },
            }
        )


class GameSyncAPIView(PublicLunaAPIView):
    def get(self, request):
        query_serializer = SyncQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        updated_after = query_serializer.validated_data.get("updated_after")

        bundle = LunaSyncService.build(updated_after=updated_after)
        response = Response(
            {
                "sync": {
                    "cursor": bundle.cutoff.isoformat(),
                    "full": bundle.is_full,
                },
                "levels": GameLevelSerializer(bundle.levels, many=True).data,
                "stages": GameStageSerializer(bundle.stages, many=True).data,
                "topics": WordTopicSerializer(bundle.topics, many=True).data,
                "words": WordPairSerializer(bundle.words, many=True).data,
            }
        )
        response["Cache-Control"] = "no-cache"
        return response


class GameLevelListAPIView(PublicLunaAPIView):
    def get(self, request):
        return Response(GameLevelSerializer(get_active_levels(), many=True).data)


class GameStageListAPIView(PublicLunaAPIView):
    def get(self, request):
        query_serializer = StageListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        queryset = get_active_stages(level_code=query_serializer.validated_data.get("level"))
        return Response(GameStageSerializer(queryset, many=True).data)


class GameTopicListAPIView(PublicLunaAPIView):
    def get(self, request):
        return Response(WordTopicSerializer(get_active_topics(), many=True).data)


class GameWordListAPIView(PublicLunaAPIView):
    def get(self, request):
        query_serializer = WordListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        queryset = get_words(
            level_code=query_serializer.validated_data.get("level"),
            topic_code=query_serializer.validated_data.get("topic"),
            min_difficulty=query_serializer.validated_data.get("min_difficulty"),
            max_difficulty=query_serializer.validated_data.get("max_difficulty"),
        )
        return Response(WordPairSerializer(queryset, many=True).data)


class GameRoundAPIView(PublicLunaAPIView):
    def get(self, request):
        query_serializer = RoundQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        data = query_serializer.validated_data

        try:
            stage = get_active_stages().get(code=data["stage"])
        except GameStage.DoesNotExist as exc:
            raise Http404("مرحله فعال پیدا نشد.") from exc

        pairs = RoundBuilderService.build(
            stage=stage,
            requested_count=data.get("count"),
            topic_code=data.get("topic"),
            exclude_ids=data.get("exclude", []),
        )
        if len(pairs) < 2:
            return Response(
                {"detail": "برای این مرحله کلمه کافی تعریف نشده است."},
                status=status.HTTP_409_CONFLICT,
            )

        # Deliberately returns a plain array to match the existing React Native component.
        return Response(WordPairSerializer(pairs, many=True).data)
