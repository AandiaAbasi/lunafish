from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string

from . import conf


def get_user_role(user):
    if user is None or not user.is_authenticated:
        return None

    if conf.USER_ROLE_RESOLVER:
        resolver = import_string(conf.USER_ROLE_RESOLVER)
        return resolver(user)

    if conf.USER_ROLE_FIELD:
        role_value = getattr(user, conf.USER_ROLE_FIELD, None)
        if role_value == conf.TEACHER_ROLE_VALUE:
            return 'teacher'
        if role_value == conf.STUDENT_ROLE_VALUE:
            return 'student'

    if conf.IS_TEACHER_METHOD and hasattr(user, conf.IS_TEACHER_METHOD):
        method = getattr(user, conf.IS_TEACHER_METHOD)
        if callable(method) and method():
            return 'teacher'

    if conf.IS_STUDENT_METHOD and hasattr(user, conf.IS_STUDENT_METHOD):
        method = getattr(user, conf.IS_STUDENT_METHOD)
        if callable(method) and method():
            return 'student'

    if conf.TEACHER_MODEL:
        Teacher = apps.get_model(conf.TEACHER_MODEL)
        if Teacher.objects.filter(**{conf.TEACHER_USER_FIELD: user}).exists():
            return 'teacher'

    if conf.STUDENT_MODEL:
        Student = apps.get_model(conf.STUDENT_MODEL)
        if Student.objects.filter(**{conf.STUDENT_USER_FIELD: user}).exists():
            return 'student'

    return None


def is_teacher(user):
    return get_user_role(user) == 'teacher'


def is_student(user):
    return get_user_role(user) == 'student'


def get_teacher_queryset():
    User = get_user_model()
    if conf.USER_ROLE_FIELD:
        return User.objects.filter(**{conf.USER_ROLE_FIELD: conf.TEACHER_ROLE_VALUE})
    if conf.TEACHER_MODEL:
        Teacher = apps.get_model(conf.TEACHER_MODEL)
        teacher_user_ids = Teacher.objects.values_list(f'{conf.TEACHER_USER_FIELD}__id', flat=True)
        return User.objects.filter(id__in=teacher_user_ids)
    return User.objects.none()


def get_student_queryset():
    User = get_user_model()
    if conf.USER_ROLE_FIELD:
        return User.objects.filter(**{conf.USER_ROLE_FIELD: conf.STUDENT_ROLE_VALUE})
    if conf.STUDENT_MODEL:
        Student = apps.get_model(conf.STUDENT_MODEL)
        student_user_ids = Student.objects.values_list(f'{conf.STUDENT_USER_FIELD}__id', flat=True)
        return User.objects.filter(id__in=student_user_ids)
    return User.objects.none()
