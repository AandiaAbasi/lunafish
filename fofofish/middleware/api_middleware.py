"""
API Middleware - Authentication and request processing for API endpoints
"""
import json
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


class APIAuthenticationMiddleware:
    """
    Middleware for API authentication via Bearer token
    Supports token-based authentication for mobile/app API requests
    """
    
    # Public API endpoints (no authentication required)
    PUBLIC_ENDPOINTS = [
        '/api/home/',
        '/api/send-otp/',
        '/api/verify-otp/',
        '/api/complete-registration/',
        '/api/check-username/',
        '/api/login-password/',
        '/api/teacher/login-password/',
        '/api/teacher/send-otp/',
        '/api/teacher/verify-otp/',
        '/api/teacher/complete-registration/',
        '/api/user/send-email-otp/',
        '/api/user/verify-email-otp/',
        '/api/teacher/send-email-otp/',
        '/api/teacher/verify-email-otp/',
        # Content endpoints (public)
        '/api/articles/',
        '/api/faqs/',
        '/api/about/',
        '/api/terms/',
        '/api/privacy/',
        '/api/contact/',
        '/api/contact/phone/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only process API requests
        if request.path.startswith('/api/'):
            self._process_api_auth(request)
        
        return self.get_response(request)
    
    def _process_api_auth(self, request):
        """
        Process authentication for API requests
        """
        # Check if endpoint is public
        if self._is_public_endpoint(request.path):
            return
        
        # Get token from header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            # No token provided for protected endpoint
            request.user = AnonymousUser()
            return
        
        try:
            # Expected format: "Bearer <token>"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token_key = parts[1]
                token = Token.objects.select_related('user').get(key=token_key)
                request.user = token.user
                return
        except Token.DoesNotExist:
            pass
        
        # Invalid token
        request.user = AnonymousUser()
    
    def _is_public_endpoint(self, path):
        """
        Check if endpoint is public
        """
        for endpoint in self.PUBLIC_ENDPOINTS:
            if path.startswith(endpoint):
                return True
        return False


class APIErrorHandlingMiddleware:
    """
    Middleware for handling API errors and formatting responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': str(_('Invalid JSON format')),
                'data': None
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(_('An unexpected error occurred')),
                'error': str(e) if settings.DEBUG else None
            }, status=500)


class APICORSMiddleware:
    """
    Simple CORS middleware for API requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
