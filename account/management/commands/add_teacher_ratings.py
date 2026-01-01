"""
Management command to add teacher ratings from students
دستور مدیریت برای اضافه کردن امتیاز معلمان از دانش‌آموزان
"""
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from account.models import User, TeacherRating
import random


class Command(BaseCommand):
    help = 'Add teacher ratings from existing students. اضافه کردن امتیاز معلمان از دانش‌آموزان موجود'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of ratings to create (default: 100)'
        )
        parser.add_argument(
            '--min-rating',
            type=int,
            default=1,
            help='Minimum rating value (default: 1)'
        )
        parser.add_argument(
            '--max-rating',
            type=int,
            default=5,
            help='Maximum rating value (default: 5)'
        )
        parser.add_argument(
            '--with-comments',
            action='store_true',
            help='Add random comments to ratings'
        )

    def handle(self, *args, **options):
        count = options['count']
        min_rating = options['min_rating']
        max_rating = options['max_rating']
        with_comments = options['with_comments']

        # Get all students
        students = User.objects.filter(role='user')
        teachers = User.objects.filter(role='teacher', is_teacher_verified=True)

        if not students.exists():
            self.stdout.write(
                self.style.ERROR('هیچ دانش‌آموزی در دیتابیس وجود ندارد')
            )
            return

        if not teachers.exists():
            self.stdout.write(
                self.style.ERROR('هیچ معلم تایید‌شده‌ای در دیتابیس وجود ندارد')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'شروع اضافه کردن {count} امتیاز...\n'
                f'تعداد دانش‌آموزان: {students.count()}\n'
                f'تعداد معلمان: {teachers.count()}'
            )
        )

        sample_comments = [
            'معلم بسیار خوب و توضیح‌دهنده است',
            'کلاس خیلی جالب و آموزنده بود',
            'معلم صبور و مهربان است',
            'روش تدریس بسیار مؤثر است',
            'توصیه می‌کنم برای دیگران',
            'کلاس خیلی سازمان‌یافته بود',
            'معلم خیلی متخصص است',
            'کلاس برای سطح من مناسب بود',
            'معلم به سؤالات من پاسخ داد',
            'بهتر می‌تواند باشد',
            'کلاس مفید بود',
            'معلم خیلی حرفه‌ای است',
            'من از این کلاس راضی هستم',
            'توصیه این معلم را می‌کنم',
            'کلاس ارزشمند بود',
        ]

        created_count = 0
        skipped_count = 0

        for i in range(count):
            try:
                # Random student and teacher
                student = random.choice(students)
                teacher = random.choice(teachers)

                # Generate random rating
                stars = random.randint(min_rating, max_rating)

                # Comment
                comment = ''
                if with_comments:
                    comment = random.choice(sample_comments)

                # Random rater type (student or parent)
                rater_type = random.choice(['student', 'parent'])

                # Try to create rating (unique constraint: teacher + rater)
                rating, created = TeacherRating.objects.get_or_create(
                    teacher=teacher,
                    rater=student,
                    defaults={
                        'stars': stars,
                        'comment': comment,
                        'rater_type': rater_type,
                        'is_anonymous': False,
                        'is_verified': True,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        f'[{i+1}/{count}] ✓ دانش‌آموز {student.name} → معلم {teacher.name}: {stars}⭐'
                        f'{f" ({comment[:30]}...)" if comment else ""}'
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        f'[{i+1}/{count}] ⊘ رتبه قبلاً موجود: {student.name} → {teacher.name}'
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'[{i+1}/{count}] خطا: {str(e)}')
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ تکمیل شد!\n'
                f'ایجاد شده: {created_count}\n'
                f'رد شده: {skipped_count}'
            )
        )
