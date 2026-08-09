import uuid
from datetime import datetime, timezone as dt_timezone

import jwt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import conf
from .guest_serializers import GuestClassCreateSerializer, GuestClassJoinSerializer
from .guest_tokens import (
    decode_guest_class_access_code,
    generate_guest_class_access_code,
    get_guest_class_access_ttl_seconds,
)
from .tokens import (
    generate_centrifugo_connection_token,
    generate_rtc_token,
    generate_whiteboard_subscription_token,
)


TEACHER_PERMISSIONS = {
    'consume': True,
    'produceAudio': True,
    'produceVideo': True,
    'produceScreen': True,
    'manageRecording': True,
}

STUDENT_PERMISSIONS = {
    'consume': True,
    'produceAudio': True,
    'produceVideo': True,
    'produceScreen': False,
    'manageRecording': False,
}


def _guest_user_payload(participant_id, name, role):
    return {
        'id': str(participant_id),
        'username': name,
        'name': name,
        'email': None,
        'phone': None,
        'role': 'teacher' if role == 'teacher' else 'user',
        'firstName': name,
        'lastName': '',
        'profile_photo': None,
        'isGuest': True,
    }


def _guest_class_payload(*, class_id, room_id, title, expires_at):
    return {
        'id': str(class_id),
        'title': title,
        'description': '',
        'status': 'active',
        'sourceType': 'guest',
        'roomId': str(room_id),
        'isGuest': True,
        'isStateless': True,
        'requiresUserAuth': False,
        'expiresAt': datetime.fromtimestamp(expires_at, tz=dt_timezone.utc).isoformat(),
        'settings': {
            'allowStudentChat': True,
            'allowStudentReactions': True,
            'allowStudentVideo': True,
            'enableRecording': False,
            'requireApprovalToJoin': False,
        },
    }


def _build_guest_join_payload(*, claims, participant_id, name):
    class_id = str(claims['class_id'])
    room_id = str(claims['room_id'])
    role = claims['role']
    title = claims.get('title') or 'Guest Online Class'
    permissions = TEACHER_PERMISSIONS if role == 'teacher' else STUDENT_PERMISSIONS
    can_draw = role == 'teacher'

    user = _guest_user_payload(participant_id, name, role)

    return {
        'class': _guest_class_payload(
            class_id=class_id,
            room_id=room_id,
            title=title,
            expires_at=claims['exp'],
        ),
        'rtc': {
            'token': generate_rtc_token(
                participant_id,
                room_id,
                permissions,
                call_id=class_id,
                session_id=f'{class_id}:{participant_id}',
                call_type='guest_classroom',
            ),
            'wsUrl': conf.RTC_WS_URL,
            'roomId': room_id,
            'iceServers': conf.RTC_ICE_SERVERS,
            'permissions': permissions,
        },
        'realtime': {
            'token': generate_centrifugo_connection_token(participant_id),
            'wsUrl': conf.CENTRIFUGO_WS_URL,
            'channels': [
                f'class:{class_id}',
                f'user:{participant_id}',
                *([f'class:{class_id}:control'] if role == 'teacher' else []),
            ],
        },
        'whiteboard': {
            'subscriptionToken': generate_whiteboard_subscription_token(
                participant_id,
                class_id,
                can_draw,
            ),
            'channel': f'whiteboard:class:{class_id}',
            'canDraw': can_draw,
        },
        'user': user,
        'participant': {
            'id': str(participant_id),
            'user': user,
            'role': role,
            'isGuest': True,
            'canUnmute': permissions['produceAudio'],
            'canShareVideo': permissions['produceVideo'],
            'canShareScreen': permissions['produceScreen'],
            'canDrawOnWhiteboard': can_draw,
        },
        # There is intentionally no DB-backed participant list here. The RTC
        # joinRoom response already returns currently connected room peers.
        'participants': [],
    }


class GuestClassCreateAPIView(APIView):
    """
    Create a completely stateless online classroom.

    No Authorization header is required and this endpoint never reads/writes
    OnlineClass, ClassEnrollment, User, Booking, or any other model.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GuestClassCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        class_id = uuid.uuid4()
        room_id = uuid.uuid4()
        participant_id = uuid.uuid4()
        title = serializer.validated_data.get('title') or 'Guest Online Class'
        name = serializer.validated_data.get('name') or 'Teacher'

        host_code = generate_guest_class_access_code(
            class_id=class_id,
            room_id=room_id,
            role='teacher',
            title=title,
        )
        join_code = generate_guest_class_access_code(
            class_id=class_id,
            room_id=room_id,
            role='student',
            title=title,
        )
        host_claims = decode_guest_class_access_code(host_code)

        payload = _build_guest_join_payload(
            claims=host_claims,
            participant_id=participant_id,
            name=name,
        )
        payload.update({
            'joinCode': join_code,
            'hostCode': host_code,
            'accessTtlSeconds': get_guest_class_access_ttl_seconds(),
        })

        return Response(payload, status=status.HTTP_201_CREATED)


class GuestClassJoinAPIView(APIView):
    """
    Join a stateless online classroom with its invitation code.

    The invitation code is room-scoped and is not a user/login JWT. Each join
    receives a fresh random guest identity and fresh RTC/realtime credentials.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GuestClassJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        name = serializer.validated_data.get('name') or 'Guest'

        try:
            claims = decode_guest_class_access_code(code)
        except jwt.ExpiredSignatureError:
            return Response(
                {'error': 'Guest class access code has expired.'},
                status=status.HTTP_410_GONE,
            )
        except (jwt.InvalidTokenError, ValueError, TypeError):
            return Response(
                {'error': 'Invalid guest class access code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            _build_guest_join_payload(
                claims=claims,
                participant_id=uuid.uuid4(),
                name=name,
            )
        )
