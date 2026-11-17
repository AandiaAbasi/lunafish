from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from luna_game.models import GameLevel, GameStage


class GameStageAdminIframeTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="luna-admin-frame-test", email="admin@example.test", password="admin-test-secret"
        )
        self.client.force_login(self.admin)
        self.level = GameLevel.objects.create(code="test-level-frame", title="Test level")
        self.stage = GameStage.objects.create(
            level=self.level,
            code="test-stage-frame",
            title="Test stage",
            min_difficulty=1, max_difficulty=10,
        )

    def test_stage_change_can_be_embedded_only_by_same_origin(self):
        url = reverse("admin:luna_game_gamestage_change", args=[self.stage.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")

    def test_level_change_retains_default_clickjacking_protection(self):
        url = reverse("admin:luna_game_gamelevel_change", args=[self.level.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
