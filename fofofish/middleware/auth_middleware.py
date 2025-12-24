import re
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import get_language, gettext_lazy as _
from django.urls import resolve, Resolver404


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
