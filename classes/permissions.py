from rest_framework import permissions

from .models import ClassEnrollment
from .utils import is_student, is_teacher


def is_teacher_user(user):
    return is_teacher(user)


def is_student_user(user):
    return is_student(user)


class IsClassParticipant(permissions.BasePermission):
    message = 'You must be a class participant.'

    def has_object_permission(self, request, view, obj):
        if obj.teacher_id == request.user.id:
            return True
        return ClassEnrollment.objects.filter(class_session=obj, student=request.user, left_at__isnull=True).exists()


class IsClassTeacher(permissions.BasePermission):
    message = 'Only the class teacher can perform this action.'

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'teacher_id'):
            return obj.teacher_id == request.user.id
        if hasattr(obj, 'class_session'):
            return obj.class_session.teacher_id == request.user.id
        return False



class IsTeacher(permissions.BasePermission):
    message = 'Only teachers can perform this action.'

    def has_permission(self, request, view):
        return is_teacher_user(request.user)


class IsStudent(permissions.BasePermission):
    message = 'Only students can perform this action.'

    def has_permission(self, request, view):
        return is_student_user(request.user)


class IsTeacherOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return is_teacher_user(request.user)


class IsEnrolledStudent(permissions.BasePermission):
    message = 'You must be enrolled in this class.'

    def has_object_permission(self, request, view, obj):
        class_session = obj if hasattr(obj, 'enrollments') else getattr(obj, 'class_session', None)
        if not class_session:
            return False
        return ClassEnrollment.objects.filter(class_session=class_session, student=request.user, left_at__isnull=True).exists()


class IsMessageSenderOrClassTeacher(permissions.BasePermission):
    message = 'Only the message sender or class teacher can delete this message.'

    def has_object_permission(self, request, view, obj):
        return obj.sender_id == request.user.id or obj.class_session.teacher_id == request.user.id
