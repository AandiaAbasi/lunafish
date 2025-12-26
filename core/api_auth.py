"""
API Key Authentication for Skyroom Integration
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


class APIKeyAuthentication(TokenAuthentication):
    """
    Simple API Key Authentication
    
    Clients must authenticate by passing a valid api key in the 
    "X-API-Key" HTTP header.
    """
    
    keyword = 'X-API-Key'
    
    def authenticate(self, request):
        """
        Returns a two-tuple of `User` and token if a valid signature has been
        supplied using HTTP X-API-Key header.  Otherwise returns `None`.
        """
        auth = request.META.get('HTTP_X_API_KEY', '').strip()
        
        if not auth:
            return None
        
        return self.authenticate_credentials(auth)
    
    def authenticate_credentials(self, key):
        """
        Authenticate the API key
        """
        # Get valid API keys from settings
        valid_keys = getattr(settings, 'VALID_API_KEYS', {})
        
        if not valid_keys:
            raise AuthenticationFailed('No API keys configured')
        
        if key not in valid_keys:
            raise AuthenticationFailed('Invalid API key')
        
        # Return a tuple (user, token) - we use None for user since API key auth
        # doesn't require a Django user
        return (None, key)
    
    def authenticate_header(self, request):
        return self.keyword


class APIKeyTokenUser:
    """
    A fake user object for API key authentication
    """
    def __init__(self, key_name):
        self.is_authenticated = True
        self.username = f"api_key_{key_name}"
        self.is_staff = True
        self.is_superuser = True
