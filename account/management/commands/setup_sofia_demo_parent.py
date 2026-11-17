"""Create or reset Sofia Martins's *separate* demo parent login.

Read-only preview (the default):
    python manage.py setup_sofia_demo_parent

Apply ONLY in a presentation database:
    LUNAFISH_DEMO_PARENT_PASSWORD=<secret> \
      python manage.py setup_sofia_demo_parent --apply --confirm-presentation

The parent logs in using student username "sofia.martins.lf" and this parent
password, not the student's ordinary password. No credentials are committed.
"""
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from account.models import ParentProfile, User


STUDENT_USERNAME = "sofia.martins.lf"
STUDENT_NAME = "Sofia Martins"
PARENT_NAME = "Mariana Martins"


class Command(BaseCommand):
    help = "Provision a separate password-protected parent login for demo student Sofia Martins"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write demo parent data")
        parser.add_argument("--confirm-presentation", action="store_true", help="Acknowledge demo-only use")
        parser.add_argument(
            "--reset-existing", action="store_true",
            help="Explicitly replace an existing demo parent's password",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        if apply and not options["confirm_presentation"]:
            raise CommandError("Use --apply --confirm-presentation on a demo environment only.")

        try:
            student = User.objects.get(username=STUDENT_USERNAME, role="user")
        except User.DoesNotExist as exc:
            raise CommandError(
                "Demo student sofia.martins.lf was not found. Run the catalog demo seed first."
            ) from exc

        if student.name != STUDENT_NAME or not student.is_active:
            raise CommandError("Unexpected or inactive student account; refusing to modify data.")

        parent = ParentProfile.objects.filter(student=student, parent_name=PARENT_NAME).first()
        if parent and not parent.is_active:
            raise CommandError("Existing parent is inactive; refusing to change its status.")
        if parent and apply and not options["reset_existing"]:
            raise CommandError(
                "Demo parent already exists. Use --reset-existing explicitly to change its password."
            )

        self.stdout.write(
            f"Student: {student.username} (id={student.pk}); "
            f"demo parent: {PARENT_NAME}; action: {'reset' if parent else 'create'}"
        )
        if not apply:
            self.stdout.write("PREVIEW ONLY. No password or parent record has been changed.")
            return

        password = os.environ.get("LUNAFISH_DEMO_PARENT_PASSWORD", "")
        if len(password) < 16 or not password.strip():
            raise CommandError(
                "Set LUNAFISH_DEMO_PARENT_PASSWORD to a private password of at least 16 characters."
            )

        with transaction.atomic():
            student = User.objects.select_for_update().get(pk=student.pk)
            parent = ParentProfile.objects.select_for_update().filter(
                student=student, parent_name=PARENT_NAME,
            ).first()
            if parent:
                if not options["reset_existing"]:
                    raise CommandError("Parent was created concurrently; refusing implicit reset.")
                if not parent.is_active:
                    raise CommandError("Parent was deactivated; refusing implicit reactivation.")
            else:
                parent = ParentProfile(
                    student=student,
                    parent_name=PARENT_NAME,
                    is_active=True,
                    can_view_class_history=True,
                    can_view_payments=True,
                    can_select_teacher=False,
                    can_set_usage_time=True,
                )
            parent.set_password(password)
            if parent.pk:
                parent.save(update_fields=["parent_password_hash", "updated_at"])
            else:
                parent.save()

            if not parent.verify_password(password):
                raise CommandError("Parent password verification failed; transaction rolled back.")

        self.stdout.write(self.style.SUCCESS(
            f"Parent login ready: student username={STUDENT_USERNAME}, "
            f"parent profile={PARENT_NAME} (id={parent.pk})."
        ))
