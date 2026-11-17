"""Self-service account removal for authenticated students and teachers.

Removing an account immediately disables login, clears personal profile data,
and hides teacher offerings. Financial/class histories remain as non-public
records for accounting, disputes and existing student bookings.
"""
import uuid

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import OTP, ParentProfile, User
from api.throttles import PasswordLoginThrottle
from classroom.models import Course, TeacherAvailability, TeachingSubject


class DeleteAccountRequestSerializer(serializers.Serializer):
    password = serializers.CharField(trim_whitespace=False, write_only=True)
    confirmation = serializers.CharField()


class DeleteAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PasswordLoginThrottle]

    def post(self, request):
        serializer = DeleteAccountRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # A parent uses a student identity via an extended JWT: this must
        # never allow the parent to delete the child's account.
        token = request.auth
        if token is not None and token.get('is_parent_session', False):
            return Response(
                {'success': False, 'message': 'Parent sessions cannot delete a student account.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if serializer.validated_data['confirmation'] != 'DELETE':
            return Response(
                {'success': False, 'message': 'Account deletion confirmation is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if not user.is_active or user.role not in ('user', 'teacher'):
                return Response(
                    {'success': False, 'message': 'This account cannot be deleted.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not user.check_password(serializer.validated_data['password']):
                return Response(
                    {'success': False, 'message': 'Incorrect password.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Disable public teacher profiles and stop creating new bookings
            # without deleting students' existing paid booking records.
            if user.role == 'teacher':
                TeacherAvailability.objects.filter(teacher=user).update(is_available=False)
                TeachingSubject.objects.filter(teacher=user).update(is_active=False)
                Course.objects.filter(teacher=user).update(is_active=False)

            # Revoke every parent credential linked to the student.
            ParentProfile.objects.filter(student=user).update(
                is_active=False,
                parent_name='Deleted parent',
                phone=None,
                email=None,
                parent_password_hash=make_password(None),
            )
            OTP.objects.filter(user=user).delete()

            # Unique anonymous username prevents reuse of old credentials and
            # preserves referential integrity for payments/class records.
            user.username = f'deleted_{user.pk}_{uuid.uuid4().hex[:12]}'
            for field in (
                'name', 'first_name', 'last_name', 'phone', 'email', 'bio',
                'birth_date', 'qualifications', 'languages_taught',
                'specialization', 'resume_summary', 'available_times',
                'push_token',
            ):
                setattr(user, field, None if field not in ('first_name', 'last_name') else '')
            user.profile_photo_path = None
            user.introduction_video = None
            user.selected_avatar = None
            user.is_active = False
            user.is_online = False
            user.is_teacher_verified = False
            user.phone_verified_at = None
            user.email_verified_at = None
            user.last_login = None
            user.set_unusable_password()
            user.save()

        return Response(
            {
                'success': True,
                'message': 'Your account has been deleted. Financial and class records may be retained where required.',
            },
            status=status.HTTP_200_OK,
        )
