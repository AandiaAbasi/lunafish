"""Location hints from the mobile apps; fail closed if missing or invalid.

These client signals are not independently verified residency information.
"""
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def is_international_request(request):
    region = (request.headers.get('X-Client-Region') or '').strip().upper()
    timezone = (request.headers.get('X-Client-Timezone') or '').strip()
    if region in ('IR', 'IRAN') or timezone == 'Asia/Tehran':
        return False
    if not re.fullmatch(r'[A-Z]{2}', region) or not timezone:
        return False
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, KeyError, ValueError):
        return False
    return True
