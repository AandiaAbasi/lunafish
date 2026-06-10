import logging

import requests

from . import conf


logger = logging.getLogger(__name__)


def _publish(channel: str, data: dict) -> bool:
    if not conf.CENTRIFUGO_API_URL or not conf.CENTRIFUGO_API_KEY:
        logger.info('[Centrifugo] skipped publish to %s because it is not configured', channel)
        return False

    try:
        response = requests.post(
            conf.CENTRIFUGO_API_URL,
            json={'method': 'publish', 'params': {'channel': channel, 'data': data}},
            headers={'Authorization': f'apikey {conf.CENTRIFUGO_API_KEY}', 'Content-Type': 'application/json'},
            timeout=3,
        )
    except Exception as exc:
        logger.warning('[Centrifugo] publish error: %s', exc)
        return False

    if response.status_code == 200:
        return True
    logger.warning('[Centrifugo] publish failed: %s %s', response.status_code, response.text[:200])
    return False


def publish_to_class(class_id: str, event: str, data: dict) -> bool:
    return _publish(f'class:{class_id}', {'event': event, 'data': data})


def publish_to_user(user_id: str, event: str, data: dict) -> bool:
    return _publish(f'user:{user_id}', {'event': event, 'data': data})


def publish_to_class_control(class_id: str, event: str, data: dict) -> bool:
    return _publish(f'class:{class_id}:control', {'event': event, 'data': data})

