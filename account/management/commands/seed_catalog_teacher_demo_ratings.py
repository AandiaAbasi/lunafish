"""Add clearly labeled demonstration reviews for the 24 imported language teachers.

This is NOT a way to import genuine student testimonials. Every seeded review
is visibly marked as DEMO. Nothing is written unless --apply is provided.

Use:
    python manage.py seed_catalog_teacher_demo_ratings
    python manage.py seed_catalog_teacher_demo_ratings --apply
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from account.models import TeacherRating, User


# IDs and usernames are taken from lunafish_english_catalog(2).json.
# Matching both protects unrelated teachers if a database has different IDs.
CATALOG_TEACHERS = ((9300001,"olivia.hartley","Clear pronunciation and natural conversation"),(9300002,"daniel.whitmore","Professional communication and confident presentations"),(9300003,"maya.bennett","Reading fluency and everyday storytelling"),(9300004,"lucas.reed","Discussion skills and advanced vocabulary"),(9300005,"camille.laurent","French phonetics and real-world conversation"),(9300006,"julien.moreau","Travel french and practical listening"),(9300007,"elise.fournier","French literature and precise expression"),(9300008,"giulia.romano","Italian conversation and cultural language"),(9300009,"matteo.ricci","Italian grammar and professional fluency"),(9300010,"sofia.bellini","Beginner-friendly italian and pronunciation"),(9300011,"lucia.navarro","Conversational spanish and natural rhythm"),(9300012,"mateo.alvarez","Storytelling, verbs, and everyday expression"),(9300013,"isabel.ortega","Advanced spanish writing and debate"),(9300014,"lena.fischer","German word order and workplace conversation"),(9300015,"tobias.weber","German listening fluency and exam preparation"),(9300016,"clara.hoffmann","German for everyday life and travel"),(9300017,"yuki.tanaka","Japanese writing systems and polite communication"),(9300018,"haruto.sato","Japanese listening and everyday expression"),(9300019,"minseo.park","Korean pronunciation and natural speech"),(9300020,"jihoon.kim","Korean sentence patterns and formal communication"),(9300021,"mei.lin","Mandarin tones and confident conversation"),(9300022,"chen.wei","Mandarin characters and practical expression"),(9300023,"beatriz.costa","European portuguese pronunciation and everyday fluency"),(9300024,"rafael.oliveira","Portuguese conversations and advanced comprehension"))

# Demo accounts cannot log in; no existing student identity is impersonated.
DEMO_STUDENT_PREFIX = "lunafish_catalog_demo_student_"
SCORES = (5, 4, 5, 4)
DEMO_COMMENTS = (
    "DEMO REVIEW — Sample learning goals for {topic} are focused and clear.",
    "DEMO REVIEW — The suggested practice activities for {topic} are easy to follow.",
    "DEMO REVIEW — The example lesson plan breaks {topic} into manageable steps.",
    "DEMO REVIEW — The sample feedback approach for {topic} looks constructive.",
)


class Command(BaseCommand):
    help = "Seed four explicitly labeled DEMO reviews for each imported catalog teacher (dry-run by default)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually write demo users and demo reviews (default: preview only).",
        )

    def handle(self, *args, **options):
        teachers = []
        for pk, username, topic in CATALOG_TEACHERS:
            teacher = User.objects.filter(pk=pk, role="teacher").first()
            if teacher is None or teacher.username != username:
                raise CommandError(
                    f"Expected catalog teacher {pk} ({username}) was not found. "
                    "Load the provided catalog first. No demo reviews were added."
                )
            teachers.append((teacher, topic))

        existing = TeacherRating.objects.filter(
            teacher_id__in=[teacher.pk for teacher, _ in teachers],
            rater__username__startswith=DEMO_STUDENT_PREFIX,
        ).count()
        self.stdout.write(
            f"Catalog teachers: {len(teachers)}; planned demo reviews: "
            f"{len(teachers) * len(SCORES)}; existing demo reviews: {existing}."
        )
        if not options["apply"]:
            self.stdout.write(
                self.style.WARNING("Preview only. Use --apply to insert visibly labeled DEMO reviews.")
            )
            return

        created_count = 0
        skipped_count = 0
        with transaction.atomic():
            raters = []
            for index in range(len(SCORES)):
                username = f"{DEMO_STUDENT_PREFIX}{index + 1:02d}"
                rater, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "name": f"Demo Student {index + 1:02d}",
                        "role": "user",
                        "is_active": False,
                    },
                )
                if not created and (
                    rater.role != "user"
                    or rater.is_active
                    or rater.has_usable_password()
                    or not (rater.name or "").startswith("Demo Student ")
                ):
                    raise CommandError(
                        f"Username '{username}' is already used by a non-demo account. "
                        "Transaction cancelled."
                    )
                if created:
                    rater.set_unusable_password()
                    rater.save(update_fields=["password"])
                raters.append(rater)

            for teacher, topic in teachers:
                for index, (rater, score, pattern) in enumerate(
                    zip(raters, SCORES, DEMO_COMMENTS)
                ):
                    comment = pattern.format(topic=topic.lower())
                    rating, created = TeacherRating.objects.get_or_create(
                        teacher=teacher,
                        rater=rater,
                        defaults={
                            "rater_type": "student",
                            "stars": score,
                            "comment": comment,
                            "is_anonymous": False,
                            "is_verified": True,
                        },
                    )
                    if created:
                        created_count += 1
                    else:
                        # Never overwrite genuine or previously changed feedback.
                        skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} labeled demo reviews; skipped {skipped_count} existing. "
                "Each review begins with 'DEMO REVIEW' and has a 'Demo Student' author."
            )
        )
