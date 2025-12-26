"""
Custom authentication for DRF to work with Bearer tokens
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token


class BearerTokenAuthentication(TokenAuthentication):
    """
    Custom Token Authentication that accepts Bearer tokens
    """
    keyword = 'Bearer'
    
    def get_model(self):
        return Token
