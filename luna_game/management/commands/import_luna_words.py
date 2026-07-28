import json
from collections import Counter, defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from luna_game.models import GameLevel, GameStage, WordPair, WordTopic


COMMAND_VERSION = "4.0.0"
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
        "Import Luna words using the JSON level as the source of truth. "
        "It can repair stage-level relations and move previously imported words "
        "from the wrong level to the correct level."
    )

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, nargs="?", help="Path to a UTF-8 JSON array.")
        parser.add_argument(
            "--command-version",
            action="store_true",
            help="Print the Luna importer command version and exit.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and simulate changes without committing them.",
        )
        parser.add_argument(
            "--repair-structure",
            action="store_true",
            help="Repair GameStage.level according to each JSON row before importing.",
        )
        parser.add_argument(
            "--repair-existing",
            action="store_true",
            help="Move an existing exact word pair from a wrong level to the JSON level.",
        )
        parser.add_argument(
            "--deactivate-wrong-duplicates",
            action="store_true",
            help="Deactivate duplicate exact pairs that remain in other levels.",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update topic, difficulty, active status and admin note for existing pairs.",
        )

    def handle(self, *args, **options):
        if options.get("command_version"):
            self.stdout.write(f"Luna importer v{COMMAND_VERSION}")
            return

        if not options.get("json_path"):
            raise CommandError("json_path is required unless --command-version is used.")

        path = Path(options["json_path"]).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise CommandError(f"JSON file not found: {path}")

        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Invalid JSON file: {exc}") from exc

        if not isinstance(payload, list):
            raise CommandError("The JSON root must be an array of word objects.")

        self._validate_json_stage_mapping(payload)

        with transaction.atomic():
            stats = self._import(payload, options)
            if options["dry_run"]:
                transaction.set_rollback(True)

        mode = "DRY RUN" if options["dry_run"] else "IMPORT"
        self.stdout.write(self.style.SUCCESS(
            f"{mode} finished | Created: {stats['created']} | "
            f"Moved: {stats['moved']} | Updated: {stats['updated']} | "
            f"Deactivated duplicates: {stats['deactivated']} | "
            f"Skipped: {stats['skipped']} | Invalid: {stats['invalid']} | "
            f"Stages repaired: {stats['stages_repaired']}"
        ))

        self.stdout.write("Per level:")
        for level_code, count in sorted(stats["by_level"].items()):
            self.stdout.write(f"  {level_code}: {count}")

        self.stdout.write("Per stage:")
        for stage_code, count in sorted(stats["by_stage"].items()):
            self.stdout.write(f"  {stage_code}: {count}")

        if stats["errors"]:
            self.stdout.write(self.style.WARNING("Validation errors:"))
            for message in stats["errors"][:50]:
                self.stdout.write(self.style.WARNING(f"  - {message}"))
            if len(stats["errors"]) > 50:
                self.stdout.write(self.style.WARNING(
                    f"  ... and {len(stats['errors']) - 50} more errors"
                ))

        if stats["invalid"]:
            raise CommandError(
                "Some rows were invalid and were not imported. Fix the messages above and run again."
            )

    def _validate_json_stage_mapping(self, payload):
        mapping = defaultdict(set)
        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                continue
            stage_code = str(item.get("stage", "")).strip()
            level_code = str(item.get("level", "")).strip()
            if stage_code and level_code:
                mapping[stage_code].add(level_code)

        conflicts = {
            stage_code: sorted(level_codes)
            for stage_code, level_codes in mapping.items()
            if len(level_codes) > 1
        }
        if conflicts:
            details = "; ".join(
                f"{stage}: {', '.join(levels)}" for stage, levels in sorted(conflicts.items())
            )
            raise CommandError(f"JSON has conflicting level mappings for stages: {details}")

    def _import(self, payload, options):
        stats = {
            "created": 0,
            "moved": 0,
            "updated": 0,
            "deactivated": 0,
            "skipped": 0,
            "invalid": 0,
            "stages_repaired": 0,
            "errors": [],
            "by_level": Counter(),
            "by_stage": Counter(),
        }
        seen = set()
        repaired_stage_ids = set()

        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                self._invalid(stats, f"Row {index}: item must be an object.")
                continue

            en = str(item.get("en", "")).strip()
            fa = str(item.get("fa", "")).strip()
            level_code = str(item.get("level", "")).strip()
            level_title = str(item.get("level_title", level_code)).strip()
            audience = str(item.get("audience", "child")).strip().lower()
            level_order = self._positive_int(item.get("level_order", 1), fallback=1)
            stage_code = str(item.get("stage", "")).strip()

            if not en or not fa:
                self._invalid(stats, f"Row {index}: both en and fa are required.")
                continue
            if not level_code:
                self._invalid(stats, f"Row {index} ({en}): level is required in JSON.")
                continue
            if audience not in AUDIENCES:
                self._invalid(
                    stats,
                    f"Row {index} ({en}): audience must be child, teen or adult.",
                )
                continue

            safe_level_code = slugify(level_code, allow_unicode=False)
            if not safe_level_code:
                self._invalid(stats, f"Row {index} ({en}): invalid level code.")
                continue

            level, _ = GameLevel.objects.update_or_create(
                code=safe_level_code[:50],
                defaults={
                    "title": (level_title or safe_level_code)[:100],
                    "audience": audience,
                    "order": level_order,
                    "is_active": True,
                },
            )

            stage = None
            if stage_code:
                stage = GameStage.objects.select_related("level").filter(code=stage_code).first()
                if stage is None:
                    self._invalid(
                        stats,
                        f"Row {index} ({en}): stage '{stage_code}' does not exist. "
                        "Run seed_luna_levels first.",
                    )
                    continue

                if stage.level_id != level.id:
                    if options["repair_structure"]:
                        stage.level = level
                        stage.save(update_fields=["level", "updated_at"])
                        if stage.id not in repaired_stage_ids:
                            repaired_stage_ids.add(stage.id)
                            stats["stages_repaired"] += 1
                    else:
                        self._invalid(
                            stats,
                            f"Row {index} ({en}): stage '{stage_code}' is linked to "
                            f"'{stage.level.code}', but JSON requires '{level.code}'. "
                            "Run again with --repair-structure.",
                        )
                        continue

            difficulty = self._positive_int(item.get("difficulty"), fallback=0)
            if not 1 <= difficulty <= 100:
                self._invalid(
                    stats,
                    f"Row {index} ({en}): difficulty must be between 1 and 100.",
                )
                continue

            if stage and not (stage.min_difficulty <= difficulty <= stage.max_difficulty):
                self._invalid(
                    stats,
                    f"Row {index} ({en}): difficulty {difficulty} is outside "
                    f"stage '{stage_code}' range "
                    f"{stage.min_difficulty}-{stage.max_difficulty}.",
                )
                continue

            unique_key = (en.casefold(), fa)
            if unique_key in seen:
                stats["skipped"] += 1
                stats["errors"].append(
                    f"Row {index} ({en}): duplicate exact pair inside JSON; skipped."
                )
                continue
            seen.add(unique_key)

            topic_code = str(item.get("topic", "general")).strip()
            topic_title = str(item.get("topic_title", topic_code)).strip()
            topic_order = self._positive_int(item.get("topic_order", 1), fallback=1)
            safe_topic_code = slugify(topic_code, allow_unicode=False) or "general"

            topic, _ = WordTopic.objects.update_or_create(
                code=safe_topic_code[:50],
                defaults={
                    "title": (topic_title or safe_topic_code)[:100],
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

            target = WordPair.objects.filter(
                level=level,
                en__iexact=en,
                fa=fa,
            ).order_by("id").first()

            wrong_level_qs = WordPair.objects.filter(
                en__iexact=en,
                fa=fa,
            ).exclude(level=level).order_by("id")
            wrong_level_rows = list(wrong_level_qs)

            if target is None and wrong_level_rows and options["repair_existing"]:
                target = wrong_level_rows.pop(0)
                target.level = level
                for field, value in defaults.items():
                    setattr(target, field, value)
                try:
                    target.save()
                except IntegrityError as exc:
                    self._invalid(
                        stats,
                        f"Row {index} ({en}): could not move existing pair to "
                        f"'{level.code}': {exc}",
                    )
                    continue
                stats["moved"] += 1
            elif target is None:
                WordPair.objects.create(level=level, en=en, fa=fa, **defaults)
                target = WordPair.objects.filter(
                    level=level,
                    en__iexact=en,
                    fa=fa,
                ).order_by("id").first()
                stats["created"] += 1
            elif options["update_existing"]:
                changed = False
                for field, value in defaults.items():
                    if getattr(target, field) != value:
                        setattr(target, field, value)
                        changed = True
                if changed:
                    target.save()
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            else:
                stats["skipped"] += 1

            if options["deactivate_wrong_duplicates"]:
                for duplicate in wrong_level_rows:
                    if duplicate.is_active:
                        duplicate.is_active = False
                        duplicate.admin_note = (
                            f"غیرفعال شد؛ رکورد صحیح در سطح {level.code} قرار دارد."
                        )[:255]
                        duplicate.save(update_fields=["is_active", "admin_note", "updated_at"])
                        stats["deactivated"] += 1

            stats["by_level"][level.code] += 1
            stats["by_stage"][stage_code or level.code] += 1

        return stats

    @staticmethod
    def _invalid(stats, message):
        stats["invalid"] += 1
        stats["errors"].append(message)

    @staticmethod
    def _positive_int(value, fallback):
        try:
            result = int(value)
        except (TypeError, ValueError):
            return fallback
        return result if result >= 0 else fallback