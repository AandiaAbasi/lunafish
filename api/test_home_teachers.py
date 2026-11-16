"""Regression tests for the home teacher-ranking fallback.

Unrated teachers must be discoverable, but never receive fabricated scores.
"""
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from account.models import TeacherRating, User
from api.views import HomePageAPIView


class HomeTeacherRankingTests(TestCase):
    def setUp(self):
        self.rated_teacher = User.objects.create_user(
            username='rated_teacher_home_test',
            password='test-password',
            role='teacher',
            is_teacher_verified=True,
            is_active=True,
        )
        self.unrated_teacher = User.objects.create_user(
            username='unrated_teacher_home_test',
            password='test-password',
            role='teacher',
            is_teacher_verified=True,
            is_active=True,
        )
        self.student = User.objects.create_user(
            username='student_home_test',
            password='test-password',
            role='user',
        )

    def home_teachers(self):
        response = HomePageAPIView.as_view()(
            APIRequestFactory().get('/api/home/')
        )
        self.assertEqual(response.status_code, 200)
        sections = {section['type']: section['data'] for section in response.data['data']}
        return sections['teachers']

    def test_unrated_verified_teachers_are_shown_without_fake_stars(self):
        teachers = self.home_teachers()
        records = {teacher['id']: teacher for teacher in teachers}
        self.assertIn(self.rated_teacher.id, records)
        self.assertIn(self.unrated_teacher.id, records)
        self.assertEqual(records[self.unrated_teacher.id]['total_ratings'], 0)
        self.assertEqual(records[self.unrated_teacher.id]['average_rating'], 0)

    def test_only_verified_ratings_count_and_rank_ahead_of_unrated(self):
        TeacherRating.objects.create(
            teacher=self.rated_teacher,
            rater=self.student,
            stars=5,
            comment='Helpful lessons',
            is_verified=True,
        )
        teachers = self.home_teachers()
        self.assertEqual(teachers[0]['id'], self.rated_teacher.id)
        self.assertEqual(teachers[0]['average_rating'], 5)
        self.assertEqual(teachers[0]['total_ratings'], 1)

    def test_pending_review_does_not_inflate_rank(self):
        TeacherRating.objects.create(
            teacher=self.rated_teacher,
            rater=self.student,
            stars=5,
            comment='Pending review',
            is_verified=False,
        )
        teachers = self.home_teachers()
        record = next(item for item in teachers if item['id'] == self.rated_teacher.id)
        self.assertEqual(record['total_ratings'], 0)
        self.assertEqual(record['average_rating'], 0)
