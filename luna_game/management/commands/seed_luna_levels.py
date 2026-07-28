from django.core.management.base import BaseCommand
from django.db import transaction

from luna_game.models import GameLevel, GameStage


LEVELS = [
    {
        "code": "kids-starter",
        "title": "کودک مقدماتی",
        "audience": "child",
        "order": 10,
        "stages": [
            ("kids-starter-1", "مرحله ۱", 10, 1, 10, 4, 2, 8),
            ("kids-starter-2", "مرحله ۲", 20, 6, 18, 6, 3, 7),
            ("kids-starter-3", "مرحله ۳", 30, 12, 25, 8, 3, 6),
        ],
    },
    {
        "code": "kids-advanced",
        "title": "کودک پیشرفته",
        "audience": "child",
        "order": 20,
        "stages": [
            ("kids-advanced-1", "مرحله ۱", 10, 20, 35, 8, 3, 6),
            ("kids-advanced-2", "مرحله ۲", 20, 30, 45, 8, 4, 5),
        ],
    },
    {
        "code": "teen",
        "title": "نوجوان",
        "audience": "teen",
        "order": 30,
        "stages": [
            ("teen-1", "مرحله ۱", 10, 40, 58, 8, 4, 5),
            ("teen-2", "مرحله ۲", 20, 52, 70, 10, 4, 4),
        ],
    },
    {
        "code": "adult",
        "title": "بزرگسال",
        "audience": "adult",
        "order": 40,
        "stages": [
            ("adult-1", "مرحله ۱", 10, 65, 82, 10, 5, 4),
            ("adult-2", "مرحله ۲", 20, 78, 92, 10, 5, 3),
            ("adult-3", "مرحله نهایی", 30, 88, 100, 12, 6, 2),
        ],
    },
]


class Command(BaseCommand):
    help = "Create the default Luna game levels and stages from child to adult."

    @transaction.atomic
    def handle(self, *args, **options):
        for item in LEVELS:
            level_data = {key: value for key, value in item.items() if key != "stages"}
            stages = item["stages"]
            level, _ = GameLevel.objects.update_or_create(
                code=level_data["code"],
                defaults=level_data,
            )
            for code, title, order, min_diff, max_diff, pairs, rounds, mistakes in stages:
                GameStage.objects.update_or_create(
                    code=code,
                    defaults={
                        "level": level,
                        "title": title,
                        "order": order,
                        "min_difficulty": min_diff,
                        "max_difficulty": max_diff,
                        "pairs_per_round": pairs,
                        "rounds_to_unlock": rounds,
                        "max_mistakes": mistakes,
                        "is_active": True,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Luna levels and stages were created successfully."))
