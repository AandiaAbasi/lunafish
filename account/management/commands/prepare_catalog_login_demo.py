"""Prepare ONLY the 24 imported catalog teachers and one Portuguese student.

Preview:
  python manage.py prepare_catalog_login_demo

Apply on a presentation database (password supplied securely via environment):
  LUNAFISH_PRESENTATION_PASSWORD=<secret> python manage.py prepare_catalog_login_demo --apply --confirm-presentation

This never creates a classes.OnlineClass or any virtual meeting room.
The +1 202-555-01xx phone numbers are reserved fictional US numbers. They
cannot receive OTPs; use the existing username/password login endpoints.
"""
import os
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from account.models import User
from classroom.models import (
    ClassBooking, Course, CourseEnrollment, TeacherAvailability, TeachingSubject,
)
from exercise.models import CategoryField, Field, FieldDetail, Order, OrderDetail


CATALOG_TEACHERS = (
    "olivia.hartley", "daniel.whitmore", "maya.bennett", "lucas.reed",
    "camille.laurent", "julien.moreau", "elise.fournier", "giulia.romano",
    "matteo.ricci", "sofia.bellini", "lucia.navarro", "mateo.alvarez",
    "isabel.ortega", "lena.fischer", "tobias.weber", "clara.hoffmann",
    "yuki.tanaka", "haruto.sato", "minseo.park", "jihoon.kim",
    "mei.lin", "chen.wei", "beatriz.costa", "rafael.oliveira",
)
STUDENT_USERNAME = "sofia.martins.lf"
STUDENT_PHONE = "+12025550124"
RAFAEL_ID = 9300024
DEMO_REF = "LUNAFISH_PRESENTATION_NO_CHARGE"

# Subject ID, course ID, existing availability ID. No online class is created.
RESERVATIONS = (
    (9400070, 9500139, 9600553),
    (9400070, 9500139, 9600555),
    (9400071, 9500141, 9600554),
    (9400071, 9500141, 9600556),
)
# Question title, type, options (correct option first); input answers use one option.
EXERCISES = {
    9400070: (
        ("How do you say 'Good morning' in Portuguese?", "radioButton",
         ("Bom dia", "Boa noite", "Até logo", "Obrigado")),
        ("Write 'thank you' as a male speaker in Portuguese.", "input",
         ("Obrigado",)),
        ("Which sentence means 'I would like some water, please'?", "radioButton",
         ("Eu gostaria de água, por favor.", "Eu moro perto da escola.",
          "Eu já terminei a viagem.", "Eu não gosto de água.")),
    ),
    9400071: (
        ("Choose the correct sentence about yesterday.", "radioButton",
         ("Ontem fui ao mercado.", "Ontem vou ao mercado.",
          "Ontem irei ao mercado.", "Ontem ir ao mercado.")),
        ("Complete: 'Se eu ___ tempo, viajaria mais.'", "input",
         ("tivesse",)),
        ("How would you politely ask for directions to the station?", "radioButton",
         ("Pode dizer-me como chegar à estação?", "Quero a estação agora.",
          "És a estação de comboios?", "Vou estar a estação ontem.")),
    ),
}


class Command(BaseCommand):
    help = "Preview or activate imported catalog teacher logins and seed Rafael's presentation learner"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Write to database")
        parser.add_argument(
            "--confirm-presentation", action="store_true",
            help="Confirm that this is a presentation environment with fictional users",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        if apply and not options["confirm_presentation"]:
            raise CommandError("Use --apply --confirm-presentation only on a demo database.")

        password = os.environ.get("LUNAFISH_PRESENTATION_PASSWORD", "")
        if apply and (len(password) < 16 or password.isspace()):
            raise CommandError("Set LUNAFISH_PRESENTATION_PASSWORD to a strong 16+ character password.")

        # Validate the original import identities. Never update arbitrary users
        # or synthetic review accounts.
        teachers = []
        for offset, username in enumerate(CATALOG_TEACHERS):
            pk = 9300001 + offset
            user = User.objects.filter(pk=pk, username=username, role="teacher").first()
            if user is None:
                raise CommandError(f"Missing catalog teacher pk={pk} username={username}")
            expected_phone = f"+120255501{offset:02d}"  # reserved example numbers
            if user.phone not in (None, "", expected_phone):
                raise CommandError(f"Teacher {username} already has a different phone; not overwriting.")
            if apply and user.has_usable_password() and not user.check_password(password):
                raise CommandError(f"Teacher {username} has a different usable password; refusing reset.")
            teachers.append((user, expected_phone))

        teacher = teachers[-1][0]
        if teacher.pk != RAFAEL_ID or teacher.username != "rafael.oliveira":
            raise CommandError("Rafael identity mismatch")

        for subject_id, course_id, slot_id in RESERVATIONS:
            subject = TeachingSubject.objects.filter(
                pk=subject_id, teacher_id=RAFAEL_ID, status="approved", is_active=True,
            ).first()
            if not subject:
                raise CommandError(f"Rafael's active approved subject {subject_id} is missing")
            if not Course.objects.filter(
                pk=course_id, subject_id=subject_id, status="approved", is_active=True,
            ).exists():
                raise CommandError(f"Rafael's active approved course {course_id} is missing")
            if not TeacherAvailability.objects.filter(pk=slot_id, teacher_id=RAFAEL_ID).exists():
                raise CommandError(f"Rafael's time slot {slot_id} is missing")

        student = User.objects.filter(username=STUDENT_USERNAME).first()
        if student and (
            student.role != "user"
            or student.name != "Sofia Martins"
            or student.phone not in (None, "", STUDENT_PHONE)
        ):
            raise CommandError("Student username belongs to another account; refusing changes")
        if apply and student and student.has_usable_password() and not student.check_password(password):
            raise CommandError("Demo student has another usable password; refusing reset")

        reserved_phones = [number for _, number in teachers] + [STUDENT_PHONE]
        permitted_ids = [user.pk for user, _ in teachers] + ([student.pk] if student else [])
        conflicting = User.objects.filter(phone__in=reserved_phones).exclude(pk__in=permitted_ids).first()
        if conflicting:
            raise CommandError(f"One reserved demo phone is already assigned to user {conflicting.pk}")

        self.stdout.write(
            f"Validated {len(teachers)} catalog teachers, Rafael's subjects/courses/slots, "
            f"and student {STUDENT_USERNAME}."
        )
        if not apply:
            self.stdout.write(
                "PREVIEW ONLY. Apply with --apply --confirm-presentation and "
                "LUNAFISH_PRESENTATION_PASSWORD set. No online class will be created."
            )
            return

        with transaction.atomic():
            for user, expected_phone in teachers:
                changes = []
                if not user.phone:
                    user.phone = expected_phone
                    changes.append("phone")
                if not user.check_password(password):
                    user.set_password(password)
                    changes.append("password")
                if changes:
                    user.save(update_fields=changes)

            if not student:
                student = User(
                    username=STUDENT_USERNAME,
                    name="Sofia Martins",
                    first_name="Sofia",
                    last_name="Martins",
                    role="user",
                    gender="female",
                    is_active=True,
                    phone=STUDENT_PHONE,
                )
                student.set_password(password)
                student.save()
            else:
                changes = []
                if not student.phone:
                    student.phone = STUDENT_PHONE
                    changes.append("phone")
                if not student.check_password(password):
                    student.set_password(password)
                    changes.append("password")
                if changes:
                    student.save(update_fields=changes)

            enrollments = {}
            for course_id in (9500139, 9500141):
                enrollment, created = CourseEnrollment.objects.get_or_create(
                    course_id=course_id, student=student,
                    defaults={
                        "paid_amount": Decimal("0.00"), "payment_status": "paid",
                        "payment_ref": DEMO_REF, "paid_at": timezone.now(),
                    },
                )
                if not created and enrollment.payment_ref != DEMO_REF:
                    raise CommandError(f"Course {course_id} has a non-demo enrollment; not touching it")
                enrollments[course_id] = enrollment

            for subject_id, course_id, slot_id in RESERVATIONS:
                slot = TeacherAvailability.objects.select_for_update().get(pk=slot_id)
                booking = ClassBooking.objects.filter(availability=slot).first()
                if booking:
                    if (booking.student_id != student.id
                        or booking.teacher_id != RAFAEL_ID
                        or booking.subject_id != subject_id
                        or booking.enrollment_id != enrollments[course_id].id):
                        raise CommandError(f"Time slot {slot_id} is already booked by another user")
                    continue
                if slot.is_booked or not slot.is_available or slot.is_expired or slot.is_past():
                    raise CommandError(f"Time slot {slot_id} is unavailable; no partial changes committed")
                ClassBooking.objects.create(
                    availability=slot, teacher=teacher, student=student,
                    subject_id=subject_id, enrollment=enrollments[course_id],
                    status="reserved", price=Decimal("0.00"),
                    discount_amount=Decimal("0.00"), final_price=Decimal("0.00"),
                    paid_amount=Decimal("0.00"), payment_status="paid",
                    payment_ref=DEMO_REF, paid_at=timezone.now(),
                )
                slot.is_booked = True
                slot.is_available = False
                slot.save(update_fields=["is_booked", "is_available"])

            for subject_id, questions in EXERCISES.items():
                subject = TeachingSubject.objects.get(pk=subject_id, teacher=teacher)
                fields = []
                for index, (title, question_type, options_list) in enumerate(questions):
                    field, _ = Field.objects.get_or_create(
                        teacher=teacher, title=title,
                        defaults={
                            "sort": index + 1, "type": question_type, "is_required": 1,
                            "guide": "Choose the best answer." if question_type != "input"
                                     else "Type the correct Portuguese word.",
                            "des": "Portuguese language practice.",
                        },
                    )
                    if field.type != question_type:
                        raise CommandError(f"Unexpected question type for '{title}'")
                    for i, answer in enumerate(options_list):
                        FieldDetail.objects.get_or_create(
                            field=field, title=answer,
                            defaults={
                                "sort": i + 1,
                                "is_correct": 1 if i == 0 else 0,
                                "correct_answer": answer if question_type == "input" else None,
                            },
                        )
                    CategoryField.objects.get_or_create(
                        teachingsubject=subject, field=field,
                        defaults={
                            "step": 1 if index < 2 else 2,
                            "sort": index + 1, "type": question_type,
                            "is_conditional": False,
                        },
                    )
                    fields.append(field)

                # An incomplete attempt makes student exercise progress visible,
                # leaving remaining questions unanswered for an actual app demo.
                order = Order.objects.filter(user=student, teachingsubject=subject).first()
                if not order:
                    order = Order.objects.create(
                        user=student, teachingsubject=subject,
                        score=0, correct=0, incorrect=0,
                    )
                for field in fields[:2 if subject_id == 9400070 else 1]:
                    if not OrderDetail.objects.filter(order=order, field=field).exists():
                        correct_option = FieldDetail.objects.get(field=field, sort=1)
                        OrderDetail.objects.create(
                            order=order, field=field,
                            field_detail=correct_option if field.type != "input" else None,
                            value=correct_option.correct_answer if field.type == "input" else None,
                            score=1,
                        )
                order.correct = OrderDetail.objects.filter(
                    order=order, score__gt=0,
                ).values("field_id").distinct().count()
                order.score = order.correct
                order.incorrect = 0
                order.save(update_fields=["correct", "score", "incorrect"])

        self.stdout.write(self.style.SUCCESS(
            "Prepared 24 teacher logins and one student login; "
            "2 course enrollments, 4 reserved class slots, 6 questions in 2 exercises. "
            "No online class created."
        ))
