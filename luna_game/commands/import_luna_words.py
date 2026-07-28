import json
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from luna_game.models import GameLevel, GameStage, WordPair, WordTopic


AUDIENCES = {"child", "teen", "adult"}


def as_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


class Command(BaseCommand):
    help = (
        "Import Luna words. Each JSON item may define stage, level, topic, "
        "difficulty and active status."
    )

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, help="Path to a UTF-8 JSON array.")
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update topic, difficulty and active status when the exact pair already exists.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and show the result without committing database changes.",
        )
        parser.add_argument("--default-level", default="kids-starter")
        parser.add_argument("--default-level-title", default="کودک مقدماتی")
        parser.add_argument("--default-topic", default="general")
        parser.add_argument("--default-topic-title", default="عمومی")
        parser.add_argument("--default-difficulty", type=int, default=10)

    def handle(self, *args, **options):
        path = Path(options["json_path"]).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise CommandError(f"JSON file not found: {path}")

        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Invalid JSON file: {exc}") from exc

        if not isinstance(payload, list):
            raise CommandError("The JSON root must be an array of word objects.")

        with transaction.atomic():
            stats = self._import(payload, options)
            if options["dry_run"]:
                transaction.set_rollback(True)

        mode = "DRY RUN" if options["dry_run"] else "IMPORT"
        self.stdout.write(self.style.SUCCESS(
            f"{mode} finished | Created: {stats['created']} | "
            f"Updated: {stats['updated']} | Skipped: {stats['skipped']} | "
            f"Invalid: {stats['invalid']}"
        ))

        if stats["by_stage"]:
            self.stdout.write("Per stage:")
            for stage_code, count in sorted(stats["by_stage"].items()):
                self.stdout.write(f"  {stage_code}: {count}")

        if stats["errors"]:
            self.stdout.write(self.style.WARNING("Validation errors:"))
            for message in stats["errors"][:30]:
                self.stdout.write(self.style.WARNING(f"  - {message}"))
            if len(stats["errors"]) > 30:
                self.stdout.write(self.style.WARNING(
                    f"  ... and {len(stats['errors']) - 30} more errors"
                ))

        if stats["invalid"]:
            raise CommandError(
                "Some rows were invalid and were not imported. Fix the messages above and run again."
            )

    def _import(self, payload, options):
        created = updated = skipped = invalid = 0
        errors = []
        by_stage = Counter()
        seen = set()

        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                invalid += 1
                errors.append(f"Row {index}: item must be an object.")
                continue

            en = str(item.get("en", "")).strip()
            fa = str(item.get("fa", "")).strip()
            if not en or not fa:
                invalid += 1
                errors.append(f"Row {index}: both en and fa are required.")
                continue

            stage_code = str(item.get("stage", "")).strip()
            level_code = str(item.get("level", options["default_level"])).strip()
            level_title = str(item.get("level_title", options["default_level_title"])).strip()
            audience = str(item.get("audience", "child")).strip().lower()
            level_order = self._positive_int(item.get("level_order", 1), fallback=1)

            if audience not in AUDIENCES:
                invalid += 1
                errors.append(
                    f"Row {index} ({en}): audience must be child, teen or adult."
                )
                continue

            stage = None
            if stage_code:
                stage = GameStage.objects.select_related("level").filter(code=stage_code).first()
                if stage is None:
                    invalid += 1
                    errors.append(
                        f"Row {index} ({en}): stage '{stage_code}' does not exist. "
                        "Run python manage.py seed_luna_levels first."
                    )
                    continue

                if level_code and level_code != stage.level.code:
                    invalid += 1
                    errors.append(
                        f"Row {index} ({en}): level '{level_code}' does not match "
                        f"stage '{stage_code}' level '{stage.level.code}'."
                    )
                    continue

                level = stage.level
            else:
                safe_level_code = slugify(level_code, allow_unicode=False)
                if not safe_level_code:
                    invalid += 1
                    errors.append(f"Row {index} ({en}): invalid level code.")
                    continue

                level, _ = GameLevel.objects.update_or_create(
                    code=safe_level_code[:50],
                    defaults={
                        "title": level_title[:100] or safe_level_code[:50],
                        "audience": audience,
                        "order": level_order,
                        "is_active": True,
                    },
                )

            difficulty = self._positive_int(
                item.get("difficulty", options["default_difficulty"]),
                fallback=options["default_difficulty"],
            )
            difficulty = max(1, min(difficulty, 100))

            if stage and not (stage.min_difficulty <= difficulty <= stage.max_difficulty):
                invalid += 1
                errors.append(
                    f"Row {index} ({en}): difficulty {difficulty} is outside "
                    f"stage '{stage_code}' range "
                    f"{stage.min_difficulty}-{stage.max_difficulty}."
                )
                continue

            pair_key = (level.id, en.casefold(), fa)
            if pair_key in seen:
                skipped += 1
                errors.append(f"Row {index} ({en}): duplicate inside JSON file; skipped.")
                continue
            seen.add(pair_key)

            topic_code = str(item.get("topic", options["default_topic"])).strip()
            topic_title = str(item.get("topic_title", options["default_topic_title"])).strip()
            topic_order = self._positive_int(item.get("topic_order", 1), fallback=1)
            safe_topic_code = slugify(topic_code, allow_unicode=False) or options["default_topic"]

            topic, _ = WordTopic.objects.update_or_create(
                code=safe_topic_code[:50],
                defaults={
                    "title": topic_title[:100] or safe_topic_code[:50],
                    "order": topic_order,
                    "is_active": True,
                },
            )

            defaults = {
                "topic": topic,
                "difficulty": difficulty,
                "is_active": as_bool(item.get("is_active"), default=True),
                "admin_note": str(
                    item.get("admin_note") or (f"مرحله هدف: {stage_code}" if stage_code else "")
                )[:255],
            }

            existing = WordPair.objects.filter(level=level, en=en, fa=fa).first()
            if existing:
                if options["update_existing"]:
                    changed = False
                    for field, value in defaults.items():
                        if getattr(existing, field) != value:
                            setattr(existing, field, value)
                            changed = True
                    if changed:
                        existing.save()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
            else:
                WordPair.objects.create(level=level, en=en, fa=fa, **defaults)
                created += 1

            by_stage[stage_code or level.code] += 1

        return {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "invalid": invalid,
            "errors": errors,
            "by_stage": by_stage,
        }

    @staticmethod
    def _positive_int(value, fallback):
        try:
            result = int(value)
        except (TypeError, ValueError):
            return fallback
        return result if result >= 0 else fallback
