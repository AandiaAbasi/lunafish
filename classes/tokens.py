import time

import jwt

from . import conf


def generate_centrifugo_connection_token(user_id, ttl=None):
    now = int(time.time())
    ttl = ttl or conf.CENTRIFUGO_TOKEN_TTL_SECONDS
    return jwt.encode({'sub': str(user_id), 'exp': now + ttl, 'iat': now}, conf.CENTRIFUGO_TOKEN_SECRET, algorithm='HS256')


def generate_whiteboard_subscription_token(user_id, class_id, can_publish=False, ttl=None):
    now = int(time.time())
    ttl = ttl or conf.CENTRIFUGO_TOKEN_TTL_SECONDS
    payload = {
        'sub': str(user_id),
        'channel': f'whiteboard:class:{class_id}',
        'exp': now + ttl,
        'iat': now,
    }
    if can_publish:
        payload['allow'] = {'publish': True}
    return jwt.encode(payload, conf.CENTRIFUGO_TOKEN_SECRET, algorithm='HS256')


def generate_rtc_token(user_id, room_id, permissions, ttl=None, call_id=None, session_id=None, call_type='classroom'):
    now = int(time.time())
    ttl = ttl or conf.RTC_TOKEN_TTL_SECONDS
    call_id = call_id or room_id
    session_id = session_id or f'{room_id}:{user_id}'
    return jwt.encode(
        {
            'sub': str(user_id),
            'room': str(room_id),
            'call_id': str(call_id),
            'room_id': str(room_id),
            'user_id': str(user_id),
            'session_id': str(session_id),
            'call_type': str(call_type),
            'permissions': permissions,
            'exp': now + ttl,
            'iat': now,
        },
        conf.RTC_JWT_SECRET,
        algorithm='HS256',
    )

