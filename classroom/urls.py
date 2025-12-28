from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassLevelViewSet, LanguageViewSet, CourseViewSet,
    LessonViewSet, LessonEnrollmentViewSet, QuizViewSet,
    StudentQuizAttemptViewSet, AttendanceViewSet,
    StudentProgressViewSet, AgoraTokenViewSet
)

router = DefaultRouter()
router.register(r'levels', ClassLevelViewSet, basename='class-level')
router.register(r'languages', LanguageViewSet, basename='language')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'enrollments', LessonEnrollmentViewSet, basename='enrollment')
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'quiz-attempts', StudentQuizAttemptViewSet, basename='quiz-attempt')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'progress', StudentProgressViewSet, basename='progress')
router.register(r'agora-tokens', AgoraTokenViewSet, basename='agora-token')

app_name = 'classroom'

urlpatterns = [
    path('', include(router.urls)),
]
