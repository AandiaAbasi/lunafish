from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    Course, Lesson, LessonEnrollment, Quiz, StudentQuizAttempt,
    Attendance, StudentProgress, AgoraToken, ClassLevel, Language
)
from .serializers import (
    CourseListSerializer, CourseDetailSerializer,
    LessonListSerializer, LessonDetailSerializer,
    LessonEnrollmentSerializer, QuizListSerializer,
    QuizDetailSerializer, StudentQuizAttemptListSerializer,
    StudentQuizAttemptDetailSerializer,
    AttendanceSerializer, StudentProgressSerializer,
    AgoraTokenSerializer, ClassLevelSerializer, LanguageSerializer
)


class ClassLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """Class level management - Read only"""
    queryset = ClassLevel.objects.all()
    serializer_class = ClassLevelSerializer
    permission_classes = [permissions.IsAuthenticated]


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    """Language management - Read only"""
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [permissions.IsAuthenticated]


class CourseViewSet(viewsets.ModelViewSet):
    """Course CRUD operations"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'teacher__username']
    ordering_fields = ['created_at', 'title', 'hourly_rate']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return self.request.user.courses.all()
        return Course.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseListSerializer
    
    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)


class LessonViewSet(viewsets.ModelViewSet):
    """Lesson CRUD operations"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'course__title']
    ordering_fields = ['scheduled_at', 'created_at', 'status']
    ordering = ['-scheduled_at']
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return Lesson.objects.filter(course__teacher=self.request.user)
        return Lesson.objects.filter(enrollments__student=self.request.user).distinct()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LessonDetailSerializer
        return LessonListSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def start_lesson(self, request, pk=None):
        """Start a lesson"""
        lesson = self.get_object()
        
        # Only teacher can start
        if lesson.course.teacher != request.user:
            return Response({'error': 'Only teacher can start lesson'}, status=status.HTTP_403_FORBIDDEN)
        
        lesson.status = 'in_progress'
        lesson.started_at = timezone.now()
        lesson.save()
        
        return Response({
            'status': 'started',
            'lesson_id': lesson.id,
            'agora_channel_id': lesson.agora_channel_id,
            'agora_channel_name': lesson.agora_channel_name
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def end_lesson(self, request, pk=None):
        """End a lesson"""
        lesson = self.get_object()
        
        # Only teacher can end
        if lesson.course.teacher != request.user:
            return Response({'error': 'Only teacher can end lesson'}, status=status.HTTP_403_FORBIDDEN)
        
        lesson.status = 'completed'
        lesson.ended_at = timezone.now()
        lesson.save()
        
        return Response({
            'status': 'completed',
            'duration_minutes': lesson.get_duration_minutes()
        })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def participants(self, request, pk=None):
        """Get lesson participants"""
        lesson = self.get_object()
        enrollments = lesson.enrollments.all()
        serializer = LessonEnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)


class LessonEnrollmentViewSet(viewsets.ModelViewSet):
    """Lesson enrollment management"""
    serializer_class = LessonEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            return LessonEnrollment.objects.filter(lesson_id=lesson_id)
        return LessonEnrollment.objects.filter(student=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request):
        """Student enrolls to a lesson"""
        lesson_id = request.data.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        enrollment, created = LessonEnrollment.objects.get_or_create(
            lesson=lesson,
            student=request.user,
            defaults={'role': 'student'}
        )
        
        serializer = self.get_serializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """Quiz management - Read only"""
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'lesson__title']
    ordering_fields = ['created_at', 'difficulty']
    ordering = ['-created_at']
    
    def get_queryset(self):
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            return Quiz.objects.filter(lesson_id=lesson_id, is_active=True)
        return Quiz.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuizDetailSerializer
        return QuizListSerializer


class StudentQuizAttemptViewSet(viewsets.ModelViewSet):
    """Student quiz attempts"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return StudentQuizAttempt.objects.filter(student=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StudentQuizAttemptDetailSerializer
        return StudentQuizAttemptListSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def start_attempt(self, request):
        """Start a new quiz attempt"""
        from django.utils import timezone
        from django.db.models import Count
        
        quiz_id = request.data.get('quiz_id')
        quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
        
        # Check if student is enrolled in the lesson
        if request.user.role == 'user':
            enrollment = get_object_or_404(
                LessonEnrollment,
                lesson=quiz.lesson,
                student=request.user
            )
        
        # Check max attempts
        previous_attempts = StudentQuizAttempt.objects.filter(
            quiz=quiz,
            student=request.user
        ).count()
        
        if previous_attempts >= quiz.max_attempts:
            return Response(
                {'error': f'Maximum {quiz.max_attempts} attempts allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new attempt
        attempt = StudentQuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            attempt_number=previous_attempts + 1,
            submission_status='in_progress'
        )
        
        serializer = self.get_serializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail='pk', methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def submit(self, request, pk=None):
        """Submit quiz attempt and calculate score"""
        from django.utils import timezone
        from decimal import Decimal
        
        attempt = self.get_object()
        
        # Verify ownership
        if attempt.student != request.user:
            return Response(
                {'error': 'You can only submit your own attempts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already submitted
        if attempt.is_submitted:
            return Response(
                {'error': 'This attempt has already been submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate score
        responses = attempt.responses.all()
        total_points = 0
        earned_points = 0
        
        for response in responses:
            question_points = response.question.points
            total_points += question_points
            
            if response.is_correct:
                earned_points += question_points
        
        # Calculate percentage
        if total_points > 0:
            score = int((earned_points / total_points) * 100)
        else:
            score = 0
        
        # Update attempt
        attempt.submitted_at = timezone.now()
        attempt.is_submitted = True
        attempt.submission_status = 'submitted'
        attempt.submission_method = request.data.get('method', 'manual')
        attempt.score = score
        attempt.total_points = total_points
        attempt.earned_points = earned_points
        attempt.passed = score >= attempt.quiz.passing_score
        
        # Calculate time taken
        if attempt.started_at and attempt.submitted_at:
            time_delta = attempt.submitted_at - attempt.started_at
            attempt.time_taken_minutes = Decimal(time_delta.total_seconds()) / Decimal(60)
        
        attempt.save()
        
        serializer = self.get_serializer(attempt)
        return Response(serializer.data)


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """Attendance records"""
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-expected_at']
    
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return Attendance.objects.filter(lesson__course__teacher=self.request.user)
        return Attendance.objects.filter(student=self.request.user)


class StudentProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """Student progress tracking"""
    serializer_class = StudentProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return StudentProgress.objects.filter(student=self.request.user)


class AgoraTokenViewSet(viewsets.ModelViewSet):
    """Agora token management"""
    serializer_class = AgoraTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AgoraToken.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def generate_token(self, request):
        """Generate a new Agora token"""
        from .services import AgoraService
        
        lesson_id = request.data.get('lesson_id')
        privilege = request.data.get('privilege', 'publisher')
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Check if student is enrolled
        if request.user.role == 'user':
            enrollment = get_object_or_404(LessonEnrollment, lesson=lesson, student=request.user)
        
        # Generate token
        agora_service = AgoraService()
        token = agora_service.generate_token(
            channel=lesson.agora_channel_name,
            uid=request.user.id,
            privilege=privilege
        )
        
        agora_token = AgoraToken.objects.create(
            lesson=lesson,
            user=request.user,
            token=token,
            privilege=privilege,
            expires_at=timezone.now() + timezone.timedelta(hours=1)
        )
        
        serializer = self.get_serializer(agora_token)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
