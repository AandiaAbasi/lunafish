from rest_framework.permissions import BasePermission


class IsTeacherOrStaff(BasePermission):
    """Allow teachers and Django staff/superusers to read student placement history."""

    message = "شما اجازه مشاهده تاریخچه تعیین سطح دانش‌آموزان را ندارید."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return bool(
            getattr(user, "is_superuser", False)
            or getattr(user, "is_staff", False)
            or getattr(user, "role", None) == "teacher"
        )
