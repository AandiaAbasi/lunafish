import time
import uuid

import jwt
from django.conf import settings


GUEST_CLASS_ACCESS_SCOPE = 'guest_class_access'


def _signing_secret():
    return getattr(settings, 'GUEST_CLASS_SIGNING_SECRET', settings.SECRET_KEY)


def get_guest_class_access_ttl_seconds():
    return int(getattr(settings, 'GUEST_CLASS_ACCESS_TTL_SECONDS', 8 * 60 * 60))


def generate_guest_class_access_code(*, class_id, room_id, role, title=''):
    """
    Create a self-contained access code for a stateless guest classroom.

    This token is NOT a user authentication token. It only proves which
    stateless room may be joined and whether the holder is a teacher/student.
    No database row is created or looked up when issuing or validating it.
    """
    if role not in {'teacher', 'student'}:
        raise ValueError('Invalid guest classroom role.')

    now = int(time.time())
    ttl = get_guest_class_access_ttl_seconds()

    return jwt.encode(
        {
            'scope': GUEST_CLASS_ACCESS_SCOPE,
            'jti': str(uuid.uuid4()),
            'class_id': str(class_id),
            'room_id': str(room_id),
            'role': role,
            'title': str(title or ''),
            'iat': now,
            'exp': now + ttl,
        },
        _signing_secret(),
        algorithm='HS256',
    )


def decode_guest_class_access_code(code):
    claims = jwt.decode(
        code,
        _signing_secret(),
        algorithms=['HS256'],
        options={'require': ['scope', 'class_id', 'room_id', 'role', 'iat', 'exp']},
    )

    if claims.get('scope') != GUEST_CLASS_ACCESS_SCOPE:
        raise jwt.InvalidTokenError('Invalid guest classroom access scope.')

    if claims.get('role') not in {'teacher', 'student'}:
        raise jwt.InvalidTokenError('Invalid guest classroom role.')

    # Validate UUID formatting without touching any model/database.
    uuid.UUID(str(claims['class_id']))
    uuid.UUID(str(claims['room_id']))

    return claims
