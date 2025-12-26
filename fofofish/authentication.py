"""
Custom authentication for DRF to work with JWT Bearer tokens
"""
from rest_framework_simplejwt.authentication import JWTAuthentication


class BearerJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication with Bearer token support
    Handles authorization header in format: Bearer <token>
    """
    pass
