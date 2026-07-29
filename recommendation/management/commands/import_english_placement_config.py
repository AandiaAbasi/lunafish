import json
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recommendation.models import (
    OptionScaleWeight,
    PsychologicalTest,
    QuestionOption,
    ScaleInterpretation,
    StudentTestResponse,
    TestQuestion,
    TestScale,
)
from recommendation.utils import calculate_test_result


class Command(BaseCommand):
    help = (
        "Import the exact scale definitions, option weights and interpretation "
        "ranges for the 60-question English placement test."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "config_path",
            type=str,
            help="Path to english_placement_60_config.json",
        )
        parser.add_argument(
            "--test-id",
            type=int,
            default=None,
            help="ID of the English placement test to configure.",
        )
        parser.add_argument(
            "--test-title",
            type=str,
            default=None,
            help="Exact test title when --test-id is not supplied.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and apply inside a rolled-back transaction.",
        )
        parser.add_argument(
            "--skip-recalculate",
            action="store_true",
            help="Do not recalculate existing completed responses.",
        )

    def handle(self, *args, **options):
        config_path = Path(options["config_path"]).expanduser().resolve()
        config = self._load_config(config_path)
        test = self._resolve_test(
            test_id=options.get("test_id"),
            test_title=options.get("test_title"),
        )

        self.stdout.write(
            self.style.NOTICE(
                f"Target test: id={test.id}, title={test.title!s}"
            )
        )

        with transaction.atomic():
            stats = self._apply_config(test=test, config=config)

            recalculated = 0
            recalc_errors = 0
            if not options["skip_recalculate"] and not options["dry_run"]:
                recalculated, recalc_errors = self._recalculate_results(test)

            if options["dry_run"]:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(
                        "DRY RUN: validation succeeded; all database changes were rolled back."
                    )
                )

        self.stdout.write(self.style.SUCCESS("Import completed successfully."))
        self.stdout.write(
            "Scales: {scales}; interpretations: {interpretations}; "
            "questions configured: {questions}; weights created: {weights}; "
            "old managed weights removed: {deleted_weights}".format(**stats)
        )

        if not options["skip_recalculate"] and not options["dry_run"]:
            self.stdout.write(
                f"Completed responses recalculated: {recalculated}; errors: {recalc_errors}"
            )

    def _load_config(self, config_path):
        if not config_path.exists():
            raise CommandError(f"Config file does not exist: {config_path}")

        try:
            with config_path.open("r", encoding="utf-8") as config_file:
                config = json.load(config_file)
        except json.JSONDecodeError as exc:
            raise CommandError(
                f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
            ) from exc

        required_keys = {
            "schema_version",
            "managed_scale_codes",
            "scales",
            "questions",
        }
        missing = sorted(required_keys - set(config))
        if missing:
            raise CommandError(
                "Missing required JSON keys: " + ", ".join(missing)
            )

        if config["schema_version"] != 1:
            raise CommandError(
                f"Unsupported schema_version={config['schema_version']}; expected 1."
            )

        return config

    def _resolve_test(self, test_id=None, test_title=None):
        if test_id and test_title:
            raise CommandError("Use only one of --test-id or --test-title.")

        queryset = PsychologicalTest.objects.all()

        if test_id:
            try:
                return queryset.get(pk=test_id)
            except PsychologicalTest.DoesNotExist as exc:
                raise CommandError(f"Test with id={test_id} was not found.") from exc

        if test_title:
            matches = queryset.filter(title=test_title)
            if not matches.exists():
                raise CommandError(
                    f"No test found with exact title: {test_title!r}"
                )
            if matches.count() > 1:
                raise CommandError(
                    "More than one test has this title. Use --test-id instead."
                )
            return matches.get()

        placement_tests = queryset.filter(test_type="english_placement")
        if placement_tests.count() == 1:
            return placement_tests.get()

        if queryset.count() == 1:
            return queryset.get()

        raise CommandError(
            "Could not choose a unique test automatically. Pass --test-id TEST_ID."
        )

    def _apply_config(self, test, config):
        managed_codes = [
            str(code).strip().upper()
            for code in config["managed_scale_codes"]
        ]
        if len(managed_codes) != len(set(managed_codes)):
            raise CommandError("managed_scale_codes contains duplicate values.")

        scale_configs = config["scales"]
        question_configs = config["questions"]

        self._validate_config_scales(scale_configs, managed_codes)
        self._validate_config_questions(question_configs, managed_codes)

        test.test_type = "english_placement"
        test.save(update_fields=["test_type", "updated_at"])

        scales_by_code = self._upsert_scales_and_interpretations(
            test=test,
            scale_configs=scale_configs,
        )

        questions_by_order = self._validate_and_map_database_questions(
            test=test,
            question_configs=question_configs,
        )

        deleted_weights, _ = OptionScaleWeight.objects.filter(
            option__question__test=test,
            scale__code__in=managed_codes,
        ).delete()

        weight_count = 0
        for item in sorted(
            question_configs,
            key=lambda row: int(row["question_order"]),
        ):
            question_order = int(item["question_order"])
            correct_option_order = int(item["correct_option_order"])
            question = questions_by_order[question_order]

            try:
                correct_option = question.options.get(order=correct_option_order)
            except QuestionOption.DoesNotExist as exc:
                raise CommandError(
                    f"Question {question_order}: option order "
                    f"{correct_option_order} does not exist."
                ) from exc
            except QuestionOption.MultipleObjectsReturned as exc:
                raise CommandError(
                    f"Question {question_order}: option order "
                    f"{correct_option_order} is duplicated."
                ) from exc

            weight_items = (
                (item["level_scale"], item["level_weight"]),
                (item["skill_scale"], item["skill_weight"]),
            )

            for scale_code, weight in weight_items:
                normalized_code = str(scale_code).strip().upper()
                scale = scales_by_code[normalized_code]
                OptionScaleWeight.objects.update_or_create(
                    option=correct_option,
                    scale=scale,
                    defaults={"weight": float(weight)},
                )
                weight_count += 1

        return {
            "scales": len(scales_by_code),
            "interpretations": sum(
                len(item.get("interpretations", []))
                for item in scale_configs
            ),
            "questions": len(question_configs),
            "weights": weight_count,
            "deleted_weights": deleted_weights,
        }

    def _validate_config_scales(self, scale_configs, managed_codes):
        codes = [str(item.get("code", "")).strip().upper() for item in scale_configs]

        empty_codes = [index + 1 for index, code in enumerate(codes) if not code]
        if empty_codes:
            raise CommandError(
                f"Scale entries with empty code: rows {empty_codes}"
            )

        duplicate_codes = sorted(
            code for code, count in Counter(codes).items() if count > 1
        )
        if duplicate_codes:
            raise CommandError(
                "Duplicate scale definitions: " + ", ".join(duplicate_codes)
            )

        if set(codes) != set(managed_codes):
            missing = sorted(set(managed_codes) - set(codes))
            extra = sorted(set(codes) - set(managed_codes))
            raise CommandError(
                f"Scale definitions do not match managed_scale_codes. "
                f"Missing={missing}; extra={extra}"
            )

        for item in scale_configs:
            code = str(item["code"]).strip().upper()
            scale_type = item.get("scale_type")
            if scale_type not in {"level", "skill", "general"}:
                raise CommandError(
                    f"Scale {code}: invalid scale_type={scale_type!r}."
                )

            pass_score = float(item.get("pass_score", 0))
            if not 0 <= pass_score <= 100:
                raise CommandError(
                    f"Scale {code}: pass_score must be between 0 and 100."
                )

            interpretations = item.get("interpretations", [])
            self._validate_interpretation_ranges(code, interpretations)

    def _validate_interpretation_ranges(self, scale_code, interpretations):
        if not interpretations:
            raise CommandError(
                f"Scale {scale_code}: at least one interpretation is required."
            )

        ordered = sorted(
            interpretations,
            key=lambda row: (float(row["min_score"]), float(row["max_score"])),
        )

        expected_start = 0.0
        for index, item in enumerate(ordered, start=1):
            min_score = float(item["min_score"])
            max_score = float(item["max_score"])
            if min_score < 0 or max_score > 100 or min_score > max_score:
                raise CommandError(
                    f"Scale {scale_code}, interpretation {index}: invalid range "
                    f"{min_score}-{max_score}."
                )
            if round(min_score - expected_start, 2) != 0:
                raise CommandError(
                    f"Scale {scale_code}: interpretation ranges have a gap or "
                    f"overlap before {min_score}. Expected start={expected_start:.2f}."
                )
            expected_start = round(max_score + 0.01, 2)

        if round(float(ordered[-1]["max_score"]), 2) != 100.0:
            raise CommandError(
                f"Scale {scale_code}: interpretation ranges must end at 100."
            )

    def _validate_config_questions(self, question_configs, managed_codes):
        if len(question_configs) != 60:
            raise CommandError(
                f"JSON must contain exactly 60 question rules; found "
                f"{len(question_configs)}."
            )

        orders = [int(item["question_order"]) for item in question_configs]
        duplicates = sorted(
            order for order, count in Counter(orders).items() if count > 1
        )
        if duplicates:
            raise CommandError(
                f"Duplicate question_order values in JSON: {duplicates}"
            )

        expected_orders = set(range(1, 61))
        if set(orders) != expected_orders:
            missing = sorted(expected_orders - set(orders))
            extra = sorted(set(orders) - expected_orders)
            raise CommandError(
                f"JSON question orders must be exactly 1..60. "
                f"Missing={missing}; extra={extra}"
            )

        for item in question_configs:
            question_order = int(item["question_order"])
            option_order = int(item["correct_option_order"])
            if option_order not in {1, 2, 3, 4}:
                raise CommandError(
                    f"Question {question_order}: correct_option_order must be 1..4."
                )

            for key in ("level_scale", "skill_scale"):
                code = str(item[key]).strip().upper()
                if code not in managed_codes:
                    raise CommandError(
                        f"Question {question_order}: unknown {key}={code}."
                    )

            for key in ("level_weight", "skill_weight"):
                weight = float(item[key])
                if weight <= 0:
                    raise CommandError(
                        f"Question {question_order}: {key} must be positive."
                    )

    def _upsert_scales_and_interpretations(self, test, scale_configs):
        scales_by_code = {}

        for item in scale_configs:
            code = str(item["code"]).strip().upper()
            scale, _ = TestScale.objects.update_or_create(
                test=test,
                code=code,
                defaults={
                    "title": item["title_fa"],
                    "description": item.get("description_fa", ""),
                    "scale_type": item["scale_type"],
                    "rank": item.get("rank"),
                    "pass_score": float(item["pass_score"]),
                },
            )

            self._assign_translation_values(
                scale,
                title_fa=item.get("title_fa"),
                title_en=item.get("title_en"),
                description_fa=item.get("description_fa"),
                description_en=item.get("description_en"),
            )
            scale.save()
            scales_by_code[code] = scale

            # Replace all ranges for a managed scale so obsolete/overlapping rows
            # cannot remain from previous manual setup.
            ScaleInterpretation.objects.filter(scale=scale).delete()

            for interpretation in sorted(
                item["interpretations"],
                key=lambda row: int(row.get("order", 0)),
            ):
                obj = ScaleInterpretation.objects.create(
                    scale=scale,
                    min_score=float(interpretation["min_score"]),
                    max_score=float(interpretation["max_score"]),
                    title=interpretation["title_fa"],
                    description=interpretation["description_fa"],
                    order=int(interpretation.get("order", 0)),
                )
                self._assign_translation_values(
                    obj,
                    title_fa=interpretation.get("title_fa"),
                    title_en=interpretation.get("title_en"),
                    description_fa=interpretation.get("description_fa"),
                    description_en=interpretation.get("description_en"),
                )
                obj.save()

        return scales_by_code

    def _assign_translation_values(
        self,
        instance,
        title_fa=None,
        title_en=None,
        description_fa=None,
        description_en=None,
    ):
        values = {
            "title_fa": title_fa,
            "title_en": title_en,
            "description_fa": description_fa,
            "description_en": description_en,
        }
        changed = False
        for field_name, value in values.items():
            if value is None or not hasattr(instance, field_name):
                continue
            setattr(instance, field_name, value)
            changed = True
        return changed

    def _validate_and_map_database_questions(self, test, question_configs):
        questions = list(
            TestQuestion.objects.filter(test=test)
            .prefetch_related("options")
            .order_by("order", "id")
        )

        if len(questions) != 60:
            raise CommandError(
                f"Test id={test.id} must have exactly 60 questions; found "
                f"{len(questions)}."
            )

        orders = [question.order for question in questions]
        duplicate_orders = sorted(
            order for order, count in Counter(orders).items() if count > 1
        )
        if duplicate_orders:
            raise CommandError(
                f"Database has duplicate TestQuestion.order values: "
                f"{duplicate_orders}"
            )

        expected_orders = {
            int(item["question_order"]) for item in question_configs
        }
        actual_orders = set(orders)
        if actual_orders != expected_orders:
            missing = sorted(expected_orders - actual_orders)
            extra = sorted(actual_orders - expected_orders)
            raise CommandError(
                f"Database question orders must be exactly 1..60. "
                f"Missing={missing}; extra={extra}"
            )

        mapped = {}
        for question in questions:
            options = list(question.options.all().order_by("order", "id"))
            if len(options) != 4:
                raise CommandError(
                    f"Question {question.order} must have exactly 4 options; "
                    f"found {len(options)}."
                )

            option_orders = [option.order for option in options]
            duplicate_option_orders = sorted(
                order
                for order, count in Counter(option_orders).items()
                if count > 1
            )
            if duplicate_option_orders:
                raise CommandError(
                    f"Question {question.order} has duplicate option order values: "
                    f"{duplicate_option_orders}"
                )

            if set(option_orders) != {1, 2, 3, 4}:
                raise CommandError(
                    f"Question {question.order} option orders must be 1,2,3,4; "
                    f"found {sorted(option_orders)}."
                )

            mapped[question.order] = question

        return mapped

    def _recalculate_results(self, test):
        completed_responses = StudentTestResponse.objects.filter(
            test=test,
            status=StudentTestResponse.SubmissionStatus.COMPLETED,
        ).order_by("id")

        success_count = 0
        error_count = 0
        for response in completed_responses.iterator():
            try:
                calculate_test_result(response)
                success_count += 1
            except Exception as exc:  # noqa: BLE001 - report each row and continue
                error_count += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"Could not recalculate response id={response.id}: {exc}"
                    )
                )

        return success_count, error_count
