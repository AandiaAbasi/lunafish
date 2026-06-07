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


def generate_rtc_token(user_id, room_id, permissions, ttl=None):
    now = int(time.time())
    ttl = ttl or conf.RTC_TOKEN_TTL_SECONDS
    return jwt.encode(
        {
            'sub': str(user_id),
            'room': str(room_id),
            'permissions': permissions,
            'exp': now + ttl,
            'iat': now,
        },
        conf.RTC_JWT_SECRET,
        algorithm='HS256',
    )

