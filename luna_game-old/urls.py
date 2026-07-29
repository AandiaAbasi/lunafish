from django.urls import path

from .views import (
    GameLevelListAPIView,
    GameManifestAPIView,
    GameRoundAPIView,
    GameStageListAPIView,
    GameSyncAPIView,
    GameTopicListAPIView,
    GameWordListAPIView,
)

app_name = "luna_game"

urlpatterns = [
    path("api/luna-game/manifest/", GameManifestAPIView.as_view(), name="manifest"),
    path("api/luna-game/sync/", GameSyncAPIView.as_view(), name="sync"),
    path("api/luna-game/levels/", GameLevelListAPIView.as_view(), name="levels"),
    path("api/luna-game/stages/", GameStageListAPIView.as_view(), name="stages"),
    path("api/luna-game/topics/", GameTopicListAPIView.as_view(), name="topics"),
    path("api/luna-game/words/", GameWordListAPIView.as_view(), name="words"),
    path("api/luna-game/round/", GameRoundAPIView.as_view(), name="round"),
]
