from datetime import timedelta
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from api.parent_serializers import ParentLoginSerializer
from account.models import OTP, ParentProfile, User, VerificationToken
from account.serializers import SendOTPSerializer
from account.services import (
    OTPDeliveryError,
    _hash_code,
    complete_registration,
    complete_teacher_registration,
    generate_and_send_otp,
    validate_otp,
)


@override_settings(OTP_MAX_ATTEMPTS=5)
class AuthenticationHardeningTests(TestCase):
    def make_otp(self, phone, code='123456', purpose='login', user=None):
        return OTP.objects.create(
            user=user,
            phone=phone,
            code=_hash_code(code),
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=2),
        )

    def test_invalid_identifier_is_rejected_before_service(self):
        serializer = SendOTPSerializer(data={'identifier': 'abc', 'purpose': 'login'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('identifier', serializer.errors)

    def test_phone_is_normalized_and_register_alias_is_supported(self):
        serializer = SendOTPSerializer(data={'identifier': '۰۹۱۲۳۴۵۶۷۸۹', 'purpose': 'register'})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['identifier'], '+989123456789')
        self.assertEqual(serializer.validated_data['purpose'], 'registration')

    def test_wrong_role_endpoint_does_not_consume_valid_otp(self):
        teacher = User.objects.create_user(
            username='teacher-role-test',
            password='StrongPass123!',
            phone='+989111111111',
            role='teacher',
        )
        otp = self.make_otp(teacher.phone, user=teacher)

        ok, _ = validate_otp(teacher.phone, '123456', purpose='login', expected_role='user')
        self.assertFalse(ok)
        otp.refresh_from_db()
        self.assertFalse(otp.is_used)

        ok, result = validate_otp(teacher.phone, '123456', purpose='login', expected_role='teacher')
        self.assertTrue(ok)
        self.assertEqual(result.pk, teacher.pk)
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_inactive_user_cannot_login_with_otp(self):
        user = User.objects.create_user(
            username='inactive-user',
            password='StrongPass123!',
            phone='+989122222222',
            role='user',
            is_active=False,
        )
        otp = self.make_otp(user.phone, user=user)
        ok, _ = validate_otp(user.phone, '123456', purpose='login', expected_role='user')
        self.assertFalse(ok)
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_otp_is_locked_after_maximum_failed_attempts(self):
        user = User.objects.create_user(
            username='attempt-user',
            password='StrongPass123!',
            phone='+989133333333',
            role='user',
        )
        otp = self.make_otp(user.phone, user=user)
        for _ in range(5):
            ok, _ = validate_otp(user.phone, '000000', purpose='login', expected_role='user')
            self.assertFalse(ok)

        otp.refresh_from_db()
        self.assertEqual(otp.failed_attempts, 5)
        self.assertTrue(otp.is_used)

    def test_student_verification_token_cannot_create_teacher(self):
        otp = self.make_otp('+989144444444', purpose='registration')
        ok, result = validate_otp(
            otp.phone,
            '123456',
            purpose='registration',
            registration_role='user',
        )
        self.assertTrue(ok)
        token = VerificationToken.objects.get(token=result['verification_token'])
        self.assertEqual(token.target_role, 'user')

        ok, _ = complete_teacher_registration(
            verification_token=token.token,
            username='should-not-be-teacher',
            password='StrongPass123!',
        )
        self.assertFalse(ok)
        self.assertFalse(User.objects.filter(username='should-not-be-teacher').exists())

    @patch('account.services.send_sms', return_value={'status': 'error', 'message': 'provider down'})
    def test_failed_sms_does_not_leave_valid_otp(self, _send_sms):
        with self.assertRaises(OTPDeliveryError):
            generate_and_send_otp('+989155555555', purpose='login')
        self.assertFalse(OTP.objects.filter(phone='+989155555555', purpose='login').exists())

    def test_registration_can_auto_generate_optional_username(self):
        token = VerificationToken.objects.create(
            token='student-token',
            phone='+989166666666',
            expires_at=timezone.now() + timedelta(minutes=30),
            target_role='user',
        )
        ok, user = complete_registration(
            verification_token=token.token,
            username=None,
            password='StrongPass123!',
            name=None,
        )
        self.assertTrue(ok)
        self.assertTrue(user.username.startswith('user_'))

    def test_teacher_registration_creates_wallet_in_same_flow(self):
        token = VerificationToken.objects.create(
            token='teacher-token',
            phone='+989177777777',
            expires_at=timezone.now() + timedelta(minutes=30),
            target_role='teacher',
        )
        ok, teacher = complete_teacher_registration(
            verification_token=token.token,
            username=None,
            password='StrongPass123!',
            name='Teacher',
        )
        self.assertTrue(ok)
        self.assertTrue(hasattr(teacher, 'wallet'))

    def test_multiple_parents_login_matches_correct_parent(self):
        student = User.objects.create_user(
            username='student-with-two-parents',
            password='StrongPass123!',
            phone='+989188888888',
            role='user',
        )
        p1 = ParentProfile(student=student, parent_name='Parent One', parent_password_hash='')
        p1.set_password('first-parent-password')
        p1.save()
        p2 = ParentProfile(student=student, parent_name='Parent Two', parent_password_hash='')
        p2.set_password('second-parent-password')
        p2.save()

        serializer = ParentLoginSerializer(data={
            'username': student.username,
            'password': 'second-parent-password',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['parent'].pk, p2.pk)

    def test_nonblank_email_is_case_insensitively_unique(self):
        User.objects.create_user(username='email-one', email='Case@Test.com', password='StrongPass123!')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(username='email-two', email='case@test.com', password='StrongPass123!')
