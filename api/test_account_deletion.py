"""Account deletion guards and anonymization behavior."""
from django.test import TestCase
from rest_framework.test import APIClient

from account.models import ParentProfile, User


class DeleteAccountApiTests(TestCase):
    url = '/api/account/delete/'

    def setUp(self):
        self.user = User.objects.create_user(
            username='delete-test-student',
            password='Correct-password-123',
            role='user',
            name='Example Student',
            phone='+12025550199',
            email='student-delete@example.test',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_password_and_explicit_confirmation_required(self):
        r = self.client.post(self.url, {'password': 'bad', 'confirmation': 'DELETE'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        r = self.client.post(self.url, {'password': 'Correct-password-123', 'confirmation': 'YES'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_student_account_anonymized_and_deactivated(self):
        r = self.client.post(self.url, {'password': 'Correct-password-123', 'confirmation': 'DELETE'}, format='json')
        self.assertEqual(r.status_code, 200, getattr(r, 'data', None))
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.has_usable_password())
        self.assertIsNone(self.user.phone)
        self.assertIsNone(self.user.email)
        self.assertIsNone(self.user.name)
        self.assertTrue(self.user.username.startswith('deleted_'))

    def test_parent_session_cannot_delete_child(self):
        self.client.force_authenticate(user=self.user, token={'is_parent_session': True})
        r = self.client.post(self.url, {'password': 'Correct-password-123', 'confirmation': 'DELETE'}, format='json')
        self.assertEqual(r.status_code, 403)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_related_parent_credential_revoked(self):
        parent = ParentProfile.objects.create(
            student=self.user,
            parent_name='Parent Example',
            parent_password_hash='test-parent-secret-hash',
            is_active=True,
        )
        r = self.client.post(self.url, {'password': 'Correct-password-123', 'confirmation': 'DELETE'}, format='json')
        self.assertEqual(r.status_code, 200)
        parent.refresh_from_db()
        self.assertFalse(parent.is_active)
        self.assertEqual(parent.parent_name, 'Deleted parent')
        self.assertNotEqual(parent.parent_password_hash, 'test-parent-secret-hash')

    def test_teacher_account_disables_subjects_and_courses(self):
        from classroom.models import Course, TeacherAvailability, TeachingSubject
        self.user.role = 'teacher'
        self.user.is_teacher_verified = True
        self.user.save(update_fields=['role', 'is_teacher_verified'])

        subject = TeachingSubject.objects.create(
            teacher=self.user, title='Delete account course',
            description='Demo description', level='beginner', is_active=True,
        )
        course = Course.objects.create(
            subject=subject, title='Demo course', description='Demo',
            price=0, session_count=3, is_active=True,
        )
        slot = TeacherAvailability.objects.create(
            teacher=self.user,
            date='2035-01-01', start_time='10:00', end_time='11:00', price=0,
            is_available=True,
        )
        response = self.client.post(
            self.url, {'password': 'Correct-password-123', 'confirmation': 'DELETE'}, format='json',
        )
        self.assertEqual(response.status_code, 200, response.data)
        subject.refresh_from_db()
        course.refresh_from_db()
        slot.refresh_from_db()
        self.assertFalse(subject.is_active)
        self.assertFalse(course.is_active)
        self.assertFalse(slot.is_available)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_teacher_verified)

    def test_admin_accounts_cannot_be_removed_here(self):
        self.user.role = 'admin'
        self.user.save(update_fields=['role'])
        r = self.client.post(self.url, {'password': 'Correct-password-123', 'confirmation': 'DELETE'}, format='json')
        self.assertEqual(r.status_code, 403)
