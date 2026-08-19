import logging

from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger(__name__)


class FailOpenIPRateThrottle(SimpleRateThrottle):
    """IP throttle that still applies when a request already carries a valid JWT."""
    scope = 'auth'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as exc:
            # Redis/cache outages must not turn authentication into HTTP 500.
            logger.warning("Authentication throttle cache unavailable: %s", exc)
            return True


class OTPRequestThrottle(FailOpenIPRateThrottle):
    scope = 'auth_otp_request'
    rate = '5/min'


class OTPVerifyThrottle(FailOpenIPRateThrottle):
    scope = 'auth_otp_verify'
    rate = '20/min'


class PasswordLoginThrottle(FailOpenIPRateThrottle):
    scope = 'auth_password_login'
    rate = '10/min'
