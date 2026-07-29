from django.urls import reverse
from rest_framework.test import APITestCase

from luna_game.models import GameLevel, GameStage, WordPair, WordTopic


class LunaGameAPITests(APITestCase):
    def setUp(self):
        self.level = GameLevel.objects.create(code="kids", title="کودک", order=1)
        self.stage = GameStage.objects.create(
            level=self.level,
            code="kids-1",
            title="مرحله ۱",
            order=1,
            min_difficulty=1,
            max_difficulty=20,
            pairs_per_round=2,
        )
        self.topic = WordTopic.objects.create(code="general", title="عمومی")
        WordPair.objects.create(level=self.level, topic=self.topic, en="apple", fa="سیب", difficulty=5)
        WordPair.objects.create(level=self.level, topic=self.topic, en="book", fa="کتاب", difficulty=8)

    def test_sync_does_not_require_authentication(self):
        response = self.client.get(reverse("luna_game:sync"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["words"]), 2)
        self.assertTrue(response.data["sync"]["full"])

    def test_round_returns_plain_array_compatible_with_current_component(self):
        response = self.client.get(reverse("luna_game:round"), {"stage": self.stage.code, "count": 2})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(set(response.data[0].keys()) >= {"id", "en", "fa", "level", "topic"}, True)
