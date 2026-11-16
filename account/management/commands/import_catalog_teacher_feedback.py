"""Import authentic teacher feedback into the existing rating model.

CSV columns: teacher_id,teacher_username,rater_username,stars,comment,is_anonymous
Only import feedback actually provided by the identified existing user with
their permission. No reviewer accounts, scores, or comments are generated.

Preview:
    python manage.py import_catalog_teacher_feedback --file /path/to/reviews.csv
Apply as pending moderation:
    python manage.py import_catalog_teacher_feedback --file /path/to/reviews.csv --apply
Apply already-reviewed, approved feedback:
    python manage.py import_catalog_teacher_feedback --file /path/to/reviews.csv --apply --approve
"""
import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from account.models import TeacherRating, User


CATALOG_TEACHERS = {
    9300001: "olivia.hartley",
    9300002: "daniel.whitmore",
    9300003: "maya.bennett",
    9300004: "lucas.reed",
    9300005: "camille.laurent",
    9300006: "julien.moreau",
    9300007: "elise.fournier",
    9300008: "giulia.romano",
    9300009: "matteo.ricci",
    9300010: "sofia.bellini",
    9300011: "lucia.navarro",
    9300012: "mateo.alvarez",
    9300013: "isabel.ortega",
    9300014: "lena.fischer",
    9300015: "tobias.weber",
    9300016: "clara.hoffmann",
    9300017: "yuki.tanaka",
    9300018: "haruto.sato",
    9300019: "minseo.park",
    9300020: "jihoon.kim",
    9300021: "mei.lin",
    9300022: "chen.wei",
    9300023: "beatriz.costa",
    9300024: "rafael.oliveira",
}
REQUIRED_COLUMNS = {
    "teacher_id", "teacher_username", "rater_username",
    "stars", "comment", "is_anonymous",
}


def parse_bool(value, row_number):
    normalized = value.strip().lower()
    if normalized in ("true", "1", "yes"):
        return True
    if normalized in ("false", "0", "no", ""):
        return False
    raise CommandError(f"Line {row_number}: invalid is_anonymous value")


class Command(BaseCommand):
    help = "Import genuine reviews for language-catalog teachers from CSV; dry-run by default"

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="UTF-8 CSV containing genuine feedback")
        parser.add_argument("--apply", action="store_true", help="Write validated reviews")
        parser.add_argument(
            "--approve", action="store_true",
            help="Mark imported reviews as moderated and approved; only for feedback verified by an administrator",
        )

    def handle(self, *args, **options):
        if options["approve"] and not options["apply"]:
            raise CommandError("--approve requires --apply")

        path = Path(options["file"]).expanduser()
        if not path.is_file():
            raise CommandError(f"CSV file not found: {path}")

        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
                raise CommandError(f"Missing CSV columns: {', '.join(sorted(REQUIRED_COLUMNS - set(reader.fieldnames or [])))}")
            records = list(reader)

        if not records:
            raise CommandError("CSV has no reviews")

        validated = []
        seen = set()
        for row_number, record in enumerate(records, start=2):
            try:
                teacher_id = int(record["teacher_id"].strip())
                stars = int(record["stars"].strip())
            except (ValueError, AttributeError, TypeError) as exc:
                raise CommandError(f"Line {row_number}: invalid teacher_id or stars") from exc
            expected_username = CATALOG_TEACHERS.get(teacher_id)
            if not expected_username or record["teacher_username"].strip() != expected_username:
                raise CommandError(f"Line {row_number}: teacher is not in the uploaded language catalog")
            if not 1 <= stars <= 5:
                raise CommandError(f"Line {row_number}: stars must be between 1 and 5")

            rater_username = (record.get("rater_username") or "").strip()
            comment = (record.get("comment") or "").strip()
            if not rater_username or not comment:
                raise CommandError(f"Line {row_number}: reviewer and comment are required")
            pair = (teacher_id, rater_username)
            if pair in seen:
                raise CommandError(f"Line {row_number}: duplicate teacher/reviewer pair")
            seen.add(pair)

            teacher = User.objects.filter(pk=teacher_id, username=expected_username, role="teacher").first()
            rater = User.objects.filter(username=rater_username, role="user", is_active=True).first()
            if teacher is None:
                raise CommandError(f"Line {row_number}: catalog teacher not found in database")
            if rater is None:
                raise CommandError(f"Line {row_number}: active reviewer account not found")
            if rater.pk == teacher.pk:
                raise CommandError(f"Line {row_number}: reviewers cannot rate themselves")
            validated.append((
                teacher, rater, stars, comment,
                parse_bool(record.get("is_anonymous") or "", row_number),
            ))

        existing = {
            (teacher.pk, rater.pk)
            for teacher, rater, _, _, _ in validated
            if TeacherRating.objects.filter(teacher=teacher, rater=rater).exists()
        }
        self.stdout.write(
            f"Validated {len(validated)} genuine review records; "
            f"{len(existing)} already exist; {len(validated) - len(existing)} new."
        )
        if not options["apply"]:
            self.stdout.write("Preview only; no database changes were made.")
            return

        created = 0
        with transaction.atomic():
            for teacher, rater, stars, comment, is_anonymous in validated:
                rating, was_created = TeacherRating.objects.get_or_create(
                    teacher=teacher,
                    rater=rater,
                    defaults={
                        "rater_type": "student",
                        "stars": stars,
                        "comment": comment,
                        "is_anonymous": is_anonymous,
                        "is_verified": options["approve"],
                    },
                )
                if was_created:
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created} reviews. "
                + ("They are approved for display." if options["approve"] else "They await moderation.")
            )
        )
