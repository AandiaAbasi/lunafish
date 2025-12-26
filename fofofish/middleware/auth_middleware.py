import re
import json
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import get_language, gettext_lazy as _
from django.urls import resolve, Resolver404
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token


class LoginRequiredMiddleware:
    PUBLIC_PATHS = [
        # language-independent public paths
        r'^/set-language/?$',
        r'^/?$',
        r'^/index/?$',
        r'^/articles/?$',
        r'^/article/[-\w]+/?$',
        r'^/about/?$',
        r'^/terms/?$',
        r'^/privacy/?$',
        r'^/contact/?$',
        r'^/faqs/?$',
        # admin
        r'^/admin/?$',
        # media/static
        r'^/media/.*$',
        r'^/static/.*$',
        r'^/staticfiles/.*$',
        # API public endpoints
        r'^/api/home/?$',
    ]

    # Customer-only paths
    CUSTOMER_PATHS = [
        r'^/api/send-otp/?$',
        r'^/api/verify-otp/?$',
        r'^/api/complete-registration/?$',
        r'^/api/check-username/?$',
        r'^/api/login-password/?$',
        r'^/api/user/send-email-otp/?$',
        r'^/api/user/verify-email-otp/?$',
        r'^/api/fetch-user/?$',
        r'^/api/profile/?$',
        r'^/api/change-password/?$',
        r'^/api/logout/?$',
        r'^/api/articles/.*$',
        r'^/api/faqs/?$',
        r'^/api/about/?$',
        r'^/api/terms/?$',
        r'^/api/privacy/?$',
        r'^/api/contact/?$',
        r'^/api/contact/phone/?$',
    ]

    # Teacher-only paths
    TEACHER_PATHS = [
        r'^/api/teacher/login-password/?$',
        r'^/api/teacher/send-otp/?$',
        r'^/api/teacher/verify-otp/?$',
        r'^/api/teacher/send-email-otp/?$',
        r'^/api/teacher/verify-email-otp/?$',
        r'^/api/promote-to-teacher/?$',
        r'^/api/teacher-profile/?$',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Remove language prefix for path matching
        path_without_prefix = path
        for lang_code in ['fa', 'en']:
            lang_prefix = f'/{lang_code}/'
            if path.startswith(lang_prefix):
                path_without_prefix = path[len(lang_prefix)-1:]
                break

        try:
            resolve(path_without_prefix)
        except Resolver404:
            return self.get_response(request)

        # Allow public paths
        if path_without_prefix.startswith('/admin/') or self._matches(path_without_prefix, self.PUBLIC_PATHS):
            return self.get_response(request)

        # Authentication check
        user = request.user
        if not user.is_authenticated:
            # Unauthenticated trying to access protected paths
            if self._matches(path_without_prefix, self.CUSTOMER_PATHS + self.TEACHER_PATHS):
                messages.error(request, _("You must log in to access this section."))
                return redirect(f'/{get_language()}/admin/')  # یا صفحه‌ی لاگین دلخواه
            return self.get_response(request)

        # Staff/Admin restrictions
        if user.is_superuser or user.is_staff:
            if self._matches(path_without_prefix, self.CUSTOMER_PATHS + self.TEACHER_PATHS):
                messages.error(request, _("You don't have permission to access this section as an admin."))
                return redirect(f'/{get_language()}/admin/')
            return self.get_response(request)

        # Role-based access
        if hasattr(user, 'role'):
            if user.role == 'teacher' and self._matches(path_without_prefix, self.CUSTOMER_PATHS):
                messages.error(request, _("Teachers cannot access customer endpoints."))
            if user.role == 'user' and self._matches(path_without_prefix, self.TEACHER_PATHS):
                messages.error(request, _("Customers cannot access teacher endpoints."))

        return self.get_response(request)

    def _matches(self, path, patterns):
        return any(re.match(p, path) for p in patterns)


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
            from django.conf import settings
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
