"""
Custom DRF Permissions for API access control
"""
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class StudentUsagePermission(permissions.BasePermission):
    """
    Permission to block student API access based on parental control limits
    
    Blocks when:
    - Student is outside allowed time window
    - Student has exceeded daily usage limit
    """
    
    def has_permission(self, request, view):
        # Only applies to students (role='user')
        if not request.user.is_authenticated:
            return True  # Let authentication handle this
        
        if request.user.role != 'user':
            return True  # Not a student, no restrictions
        
        # Check parental controls
        from account.models import ParentProfile, ParentAppUsageLog
        
        try:
            # Get active parent profile for student
            parent = ParentProfile.objects.filter(
                student=request.user,
                is_active=True
            ).first()
            
            if not parent:
                return True  # No parental controls set
            
            # Get server time
            server_now = timezone.localtime(timezone.now())
            current_time = server_now.time()
            today = server_now.date()
            
            # Check time window restriction
            if not parent.is_within_allowed_window(current_time):
                self.message = {
                    'success': False,
                    'error': 'USAGE_BLOCKED',
                    'error_code': 'OUT_OF_ALLOWED_WINDOW',
                    'message': _('Access is not allowed at this time. Please check with your parent.'),
                    'block_reason': 'OUT_OF_ALLOWED_WINDOW',
                    'allowed_start_time': str(parent.allowed_start_time) if parent.allowed_start_time else None,
                    'allowed_end_time': str(parent.allowed_end_time) if parent.allowed_end_time else None,
                    'server_time': str(current_time)
                }
                return False
            
            # Check daily usage limit
            if parent.daily_usage_limit_minutes:
                usage_log = ParentAppUsageLog.objects.filter(
                    parent=parent,
                    date=today
                ).first()
                
                if usage_log:
                    used_seconds = usage_log.total_seconds
                    limit_seconds = parent.daily_usage_limit_minutes * 60
                    remaining_seconds = limit_seconds - used_seconds
                    
                    if remaining_seconds <= 0:
                        self.message = {
                            'success': False,
                            'error': 'USAGE_BLOCKED',
                            'error_code': 'DAILY_LIMIT_REACHED',
                            'message': _('You have reached your daily usage limit. Please try again tomorrow.'),
                            'block_reason': 'DAILY_LIMIT_REACHED',
                            'used_today_seconds': used_seconds,
                            'remaining_seconds': 0,
                            'daily_limit_minutes': parent.daily_usage_limit_minutes
                        }
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking student usage permission: {e}")
            return True  # Fail open to avoid blocking legitimate access
