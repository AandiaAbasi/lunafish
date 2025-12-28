from django.test import TestCase
from django.utils import timezone
from account.models import User
from .models import (
    ClassLevel, Language, Course, Lesson, LessonEnrollment,
    Quiz, StudentQuizAttempt, Attendance, StudentProgress
)


class CourseTestCase(TestCase):
    def setUp(self):
        self.level = ClassLevel.objects.create(name='Beginner', order=1)
        self.language = Language.objects.create(name='English', code='en')
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@example.com',
            password='pass123',
            role='teacher'
        )
        self.course = Course.objects.create(
            title='English 101',
            teacher=self.teacher,
            language=self.language,
            level=self.level,
            hourly_rate=50.00
        )
    
    def test_course_creation(self):
        self.assertEqual(self.course.title, 'English 101')
        self.assertEqual(self.course.teacher, self.teacher)
        self.assertTrue(self.course.is_active)


class LessonTestCase(TestCase):
    def setUp(self):
        self.level = ClassLevel.objects.create(name='Beginner', order=1)
        self.language = Language.objects.create(name='English', code='en')
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@example.com',
            password='pass123',
            role='teacher'
        )
        self.course = Course.objects.create(
            title='English 101',
            teacher=self.teacher,
            language=self.language,
            level=self.level,
            hourly_rate=50.00
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title='Lesson 1: Greeting',
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            agora_channel_name='lesson-1',
            agora_channel_id='ch-1001'
        )
    
    def test_lesson_creation(self):
        self.assertEqual(self.lesson.title, 'Lesson 1: Greeting')
        self.assertEqual(self.lesson.status, 'scheduled')
        self.assertTrue(self.lesson.is_upcoming())


class EnrollmentTestCase(TestCase):
    def setUp(self):
        self.level = ClassLevel.objects.create(name='Beginner', order=1)
        self.language = Language.objects.create(name='English', code='en')
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@example.com',
            password='pass123',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username='student1',
            email='student@example.com',
            password='pass123',
            role='user'
        )
        self.course = Course.objects.create(
            title='English 101',
            teacher=self.teacher,
            language=self.language,
            level=self.level,
            hourly_rate=50.00
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title='Lesson 1',
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            agora_channel_name='lesson-1',
            agora_channel_id='ch-1001'
        )
    
    def test_enrollment(self):
        enrollment = LessonEnrollment.objects.create(
            lesson=self.lesson,
            student=self.student,
            role='student'
        )
        self.assertEqual(enrollment.status, 'registered')
