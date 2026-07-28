import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from luna_game.models import GameLevel, WordPair, WordTopic


class Command(BaseCommand):
    help = "Import the existing words-fa-en JSON file into Luna Game models."

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str)
        parser.add_argument("--level", default="kids-starter")
        parser.add_argument("--level-title", default="کودک مقدماتی")
        parser.add_argument("--topic", default="general")
        parser.add_argument("--topic-title", default="عمومی")
        parser.add_argument("--difficulty", type=int, default=10)

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["json_path"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Invalid JSON file: {exc}") from exc

        if not isinstance(payload, list):
            raise CommandError("The JSON root must be an array.")

        level, _ = GameLevel.objects.get_or_create(
            code=options["level"],
            defaults={"title": options["level_title"], "order": 1},
        )
        default_topic, _ = WordTopic.objects.get_or_create(
            code=options["topic"],
            defaults={"title": options["topic_title"], "order": 1},
        )

        created = 0
        skipped = 0
        for item in payload:
            en = str(item.get("en", "")).strip()
            fa = str(item.get("fa", "")).strip()
            if not en or not fa:
                skipped += 1
                continue

            topic = default_topic
            item_topic = str(item.get("topic", "")).strip()
            if item_topic:
                topic_code = slugify(item_topic, allow_unicode=False) or options["topic"]
                topic, _ = WordTopic.objects.get_or_create(
                    code=topic_code[:50],
                    defaults={"title": item_topic[:100], "order": 1},
                )

            difficulty = item.get("difficulty", options["difficulty"])
            try:
                difficulty = max(1, min(int(difficulty), 100))
            except (TypeError, ValueError):
                difficulty = options["difficulty"]

            _, was_created = WordPair.objects.get_or_create(
                level=level,
                en=en,
                fa=fa,
                defaults={"topic": topic, "difficulty": difficulty},
            )
            created += int(was_created)
            skipped += int(not was_created)

        self.stdout.write(self.style.SUCCESS(f"Created: {created} | Skipped: {skipped}"))
