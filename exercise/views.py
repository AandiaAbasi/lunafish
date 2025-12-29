"""
API Views for Exercise and Exam Management
تمرین‌ها و سوالات برای دروس
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    Exercise, Question, QuestionOption,
    StudentExerciseAttempt, StudentQuestionAnswer,
    ExerciseChoice, StudentExerciseChoice
)
from .serializers import (
    ExerciseListSerializer, ExerciseDetailSerializer,
    QuestionSerializer, QuestionDetailSerializer,
    QuestionOptionSerializer, StudentExerciseAttemptSerializer,
    StudentQuestionAnswerSerializer,
    ExerciseChoiceSerializer, StudentExerciseChoiceSerializer
)
from classroom.models import TeachingSubject


# ========== Exercise APIs ==========

class ExerciseListCreateAPIView(APIView):
    """
    List and Create Exercises
    دریافت لیست تمرین‌ها و ایجاد تمرین جدید
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Exercise'],
        summary='List Exercises',
        description='دریافت لیست تمرین‌ها',
        parameters=[
            OpenApiParameter('subject', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by subject ID'),
            OpenApiParameter('teacher', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by teacher ID'),
            OpenApiParameter('difficulty', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by difficulty'),
            OpenApiParameter('is_published', OpenApiTypes.BOOL, required=False, location=OpenApiParameter.QUERY, description='Filter by published status'),
        ],
        responses={200: OpenApiResponse(description="List of exercises")}
    )
    def get(self, request):
        queryset = Exercise.objects.all()
        
        # فیلتر برای معلم - تنها تمرین‌های خود را ببیند
        if request.user.role == 'teacher':
            queryset = queryset.filter(teacher=request.user)
        
        # فیلتر برای دانش‌آموز - تنها تمرین‌های منتشر شده را ببیند
        if request.user.role == 'student':
            queryset = queryset.filter(is_published=True)
        
        # اضافی فیلترها
        subject_id = request.query_params.get('subject')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        teacher_id = request.query_params.get('teacher')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        difficulty = request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        is_published = request.query_params.get('is_published')
        if is_published is not None:
            is_published = is_published.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_published=is_published)
        
        serializer = ExerciseListSerializer(queryset, many=True)
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Exercise'],
        summary='Create Exercise',
        description='ایجاد تمرین جدید (فقط معلمان)',
        request=None,
        responses={
            201: OpenApiResponse(description="Exercise created"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    def post(self, request):
        if request.user.role != 'teacher':
            return Response(
                {'error': _('تنها معلمان می‌توانند تمرین ایجاد کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data.copy()
        data['teacher'] = request.user.id
        
        serializer = ExerciseDetailSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseRetrieveAPIView(APIView):
    """
    Retrieve Exercise Details
    دریافت جزئیات تمرین
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise'],
        summary='Get Exercise Details',
        description='دریافت جزئیات کامل تمرین',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Exercise ID')
        ],
        responses={200: OpenApiResponse(description="Exercise details")}
    )
    def get(self, request, id):
        try:
            exercise = Exercise.objects.get(id=id)
        except Exercise.DoesNotExist:
            return Response(
                {'error': _('تمرین یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی دسترسی
        if request.user.role == 'student' and not exercise.is_published:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ExerciseDetailSerializer(exercise)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExerciseUpdateAPIView(APIView):
    """
    Update Exercise
    ویرایش تمرین
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Exercise'],
        summary='Update Exercise',
        description='ویرایش تمرین',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Exercise ID')
        ],
        request=None,
        responses={200: OpenApiResponse(description="Exercise updated")}
    )
    def post(self, request, id):
        try:
            exercise = Exercise.objects.get(id=id)
        except Exercise.DoesNotExist:
            return Response(
                {'error': _('تمرین یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی دسترسی
        if request.user.role == 'teacher' and exercise.teacher_id != request.user.id:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ExerciseDetailSerializer(exercise, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseDeleteAPIView(APIView):
    """
    Delete Exercise
    حذف تمرین
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise'],
        summary='Delete Exercise',
        description='حذف تمرین',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Exercise ID')
        ],
        responses={204: OpenApiResponse(description="Exercise deleted")}
    )
    def post(self, request, id):
        try:
            exercise = Exercise.objects.get(id=id)
        except Exercise.DoesNotExist:
            return Response(
                {'error': _('تمرین یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # بررسی دسترسی
        if request.user.role == 'teacher' and exercise.teacher_id != request.user.id:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        exercise.delete()
        return Response(
            {'message': _('تمرین با موفقیت حذف شد')},
            status=status.HTTP_204_NO_CONTENT
        )


# ========== Question APIs ==========

class QuestionListCreateAPIView(APIView):
    """
    List and Create Questions
    دریافت لیست سوالات و ایجاد سوال جدید
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Question'],
        summary='List Questions',
        description='دریافت لیست سوالات',
        parameters=[
            OpenApiParameter('exercise', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by exercise ID'),
            OpenApiParameter('question_type', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by question type'),
        ],
        responses={200: OpenApiResponse(description="List of questions")}
    )
    def get(self, request):
        queryset = Question.objects.all()
        
        exercise_id = request.query_params.get('exercise')
        if exercise_id:
            queryset = queryset.filter(exercise_id=exercise_id)
        
        question_type = request.query_params.get('question_type')
        if question_type:
            queryset = queryset.filter(question_type=question_type)
        
        serializer = QuestionSerializer(queryset, many=True)
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Question'],
        summary='Create Question',
        description='ایجاد سوال جدید',
        request=None,
        responses={201: OpenApiResponse(description="Question created")}
    )
    def post(self, request):
        if request.user.role != 'teacher':
            return Response(
                {'error': _('تنها معلمان می‌توانند سوال ایجاد کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = QuestionDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionRetrieveAPIView(APIView):
    """Retrieve Question Details"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Question'],
        summary='Get Question Details',
        description='دریافت جزئیات سوال',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Question ID')
        ],
        responses={200: OpenApiResponse(description="Question details")}
    )
    def get(self, request, id):
        try:
            question = Question.objects.get(id=id)
        except Question.DoesNotExist:
            return Response(
                {'error': _('سوال یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = QuestionDetailSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuestionUpdateAPIView(APIView):
    """Update Question"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Question'],
        summary='Update Question',
        description='ویرایش سوال',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Question ID')
        ],
        request=None,
        responses={200: OpenApiResponse(description="Question updated")}
    )
    def post(self, request, id):
        try:
            question = Question.objects.get(id=id)
        except Question.DoesNotExist:
            return Response(
                {'error': _('سوال یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = QuestionDetailSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionDeleteAPIView(APIView):
    """Delete Question"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Question'],
        summary='Delete Question',
        description='حذف سوال',
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, required=True, location=OpenApiParameter.PATH, description='Question ID')
        ],
        responses={204: OpenApiResponse(description="Question deleted")}
    )
    def post(self, request, id):
        try:
            question = Question.objects.get(id=id)
        except Question.DoesNotExist:
            return Response(
                {'error': _('سوال یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        question.delete()
        return Response(
            {'message': _('سوال با موفقیت حذف شد')},
            status=status.HTTP_204_NO_CONTENT
        )


# ========== Question Option APIs ==========

class QuestionOptionListCreateAPIView(APIView):
    """
    List and Create Question Options
    دریافت گزینه‌ها و ایجاد گزینه جدید
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Question Option'],
        summary='Create Question Option',
        description='ایجاد گزینه جدید برای سوال',
        request=None,
        responses={201: OpenApiResponse(description="Option created")}
    )
    def post(self, request):
        if request.user.role != 'teacher':
            return Response(
                {'error': _('تنها معلمان می‌توانند گزینه اضافه کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = QuestionOptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionOptionUpdateAPIView(APIView):
    """Update Question Option"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def post(self, request, id):
        try:
            option = QuestionOption.objects.get(id=id)
        except QuestionOption.DoesNotExist:
            return Response(
                {'error': _('گزینه یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = QuestionOptionSerializer(option, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionOptionDeleteAPIView(APIView):
    """Delete Question Option"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, id):
        try:
            option = QuestionOption.objects.get(id=id)
        except QuestionOption.DoesNotExist:
            return Response(
                {'error': _('گزینه یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        option.delete()
        return Response(
            {'message': _('گزینه با موفقیت حذف شد')},
            status=status.HTTP_204_NO_CONTENT
        )


# ========== Student Exercise Attempt APIs ==========

class StudentExerciseAttemptListAPIView(APIView):
    """List Student Attempts"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Student Exercise'],
        summary='List Exercise Attempts',
        description='دریافت لیست تلاش‌های تمرین',
        parameters=[
            OpenApiParameter('exercise', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by exercise ID'),
            OpenApiParameter('status', OpenApiTypes.STR, required=False, location=OpenApiParameter.QUERY, description='Filter by status'),
        ],
        responses={200: OpenApiResponse(description="List of attempts")}
    )
    def get(self, request):
        if request.user.role == 'student':
            queryset = StudentExerciseAttempt.objects.filter(student=request.user)
        elif request.user.role == 'teacher':
            queryset = StudentExerciseAttempt.objects.filter(exercise__teacher=request.user)
        else:
            queryset = StudentExerciseAttempt.objects.all()
        
        exercise_id = request.query_params.get('exercise')
        if exercise_id:
            queryset = queryset.filter(exercise_id=exercise_id)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        serializer = StudentExerciseAttemptSerializer(queryset, many=True)
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)


class StudentExerciseAttemptRetrieveAPIView(APIView):
    """Retrieve Student Attempt"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        try:
            attempt = StudentExerciseAttempt.objects.get(id=id)
        except StudentExerciseAttempt.DoesNotExist:
            return Response(
                {'error': _('تلاش یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StudentExerciseAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentExerciseAttemptSubmitAPIView(APIView):
    """Submit Exercise Attempt"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, id):
        try:
            attempt = StudentExerciseAttempt.objects.get(id=id)
        except StudentExerciseAttempt.DoesNotExist:
            return Response(
                {'error': _('تلاش یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if attempt.student_id != request.user.id:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        attempt.status = 'submitted'
        attempt.submitted_at = timezone.now()
        attempt.save()
        
        serializer = StudentExerciseAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentExerciseAttemptGradeAPIView(APIView):
    """Grade Exercise Attempt"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, id):
        try:
            attempt = StudentExerciseAttempt.objects.get(id=id)
        except StudentExerciseAttempt.DoesNotExist:
            return Response(
                {'error': _('تلاش یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if attempt.exercise.teacher_id != request.user.id:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        score = request.data.get('score')
        percentage = request.data.get('percentage')
        teacher_notes = request.data.get('teacher_notes', '')
        
        if score is not None:
            attempt.score = int(score)
        
        if percentage is not None:
            attempt.percentage = float(percentage)
        
        if teacher_notes:
            attempt.teacher_notes = teacher_notes
        
        attempt.status = 'graded'
        attempt.graded_at = timezone.now()
        attempt.save()
        
        serializer = StudentExerciseAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ========== Student Question Answer APIs ==========

class StudentQuestionAnswerListCreateAPIView(APIView):
    """Create Student Answer"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def post(self, request):
        serializer = StudentQuestionAnswerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentQuestionAnswerUpdateAPIView(APIView):
    """Update Student Answer"""
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def post(self, request, id):
        try:
            answer = StudentQuestionAnswer.objects.get(id=id)
        except StudentQuestionAnswer.DoesNotExist:
            return Response(
                {'error': _('جواب یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if answer.attempt.student_id != request.user.id:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = StudentQuestionAnswerSerializer(answer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== Exercise Choice APIs ==========

class ExerciseChoiceListCreateAPIView(APIView):
    """
    List and Create Exercise Choices
    دریافت لیست دسته‌های تمرین‌های اختیاری و ایجاد دسته جدید
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Exercise Choice'],
        summary='List Exercise Choices',
        description='دریافت لیست دسته‌های تمرین‌های اختیاری',
        parameters=[
            OpenApiParameter('subject', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by subject ID'),
            OpenApiParameter('teacher', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by teacher ID'),
            OpenApiParameter('is_published', OpenApiTypes.BOOL, required=False, location=OpenApiParameter.QUERY, description='Filter by published status'),
        ],
        responses={200: OpenApiResponse(description="List of exercise choices")}
    )
    def get(self, request):
        queryset = ExerciseChoice.objects.all()
        
        # Filter by subject if provided
        subject_id = request.query_params.get('subject')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        
        # Filter by teacher if provided
        teacher_id = request.query_params.get('teacher')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by published status
        is_published = request.query_params.get('is_published')
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')
        
        serializer = ExerciseChoiceSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Exercise Choice'],
        summary='Create Exercise Choice Group',
        description='ایجاد دسته جدید تمرین‌های اختیاری',
        request=ExerciseChoiceSerializer,
        responses={201: OpenApiResponse(description="Exercise choice created successfully")}
    )
    def post(self, request):
        # Only teachers can create exercise choices
        if not hasattr(request.user, 'role') or request.user.role != 'teacher':
            return Response(
                {'error': _('فقط معلمان می‌توانند دسته تمرین‌ها را ایجاد کنند')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data.copy()
        data['teacher'] = request.user.id
        
        serializer = ExerciseChoiceSerializer(data=data)
        if serializer.is_valid():
            serializer.save(teacher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseChoiceRetrieveAPIView(APIView):
    """
    Retrieve Exercise Choice Details
    دریافت جزئیات دسته تمرین‌های اختیاری
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise Choice'],
        summary='Retrieve Exercise Choice',
        description='دریافت جزئیات دسته تمرین‌های اختیاری',
        responses={200: OpenApiResponse(description="Exercise choice details")}
    )
    def get(self, request, id):
        try:
            exercise_choice = ExerciseChoice.objects.get(id=id)
        except ExerciseChoice.DoesNotExist:
            return Response(
                {'error': _('دسته تمرین یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ExerciseChoiceSerializer(exercise_choice)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExerciseChoiceUpdateAPIView(APIView):
    """
    Update Exercise Choice
    بروزرسانی دسته تمرین‌های اختیاری
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Exercise Choice'],
        summary='Update Exercise Choice',
        description='بروزرسانی دسته تمرین‌های اختیاری',
        request=ExerciseChoiceSerializer,
        responses={200: OpenApiResponse(description="Exercise choice updated successfully")}
    )
    def post(self, request, id):
        try:
            exercise_choice = ExerciseChoice.objects.get(id=id)
        except ExerciseChoice.DoesNotExist:
            return Response(
                {'error': _('دسته تمرین یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission: only teacher who created it can update
        if exercise_choice.teacher_id != request.user.id:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ExerciseChoiceSerializer(exercise_choice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseChoiceDeleteAPIView(APIView):
    """
    Delete Exercise Choice
    حذف دسته تمرین‌های اختیاری
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Exercise Choice'],
        summary='Delete Exercise Choice',
        description='حذف دسته تمرین‌های اختیاری',
        responses={204: OpenApiResponse(description="Exercise choice deleted successfully")}
    )
    def post(self, request, id):
        try:
            exercise_choice = ExerciseChoice.objects.get(id=id)
        except ExerciseChoice.DoesNotExist:
            return Response(
                {'error': _('دسته تمرین یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission: only teacher who created it can delete
        if exercise_choice.teacher_id != request.user.id:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        exercise_choice.delete()
        return Response(
            {'message': _('دسته تمرین حذف شد')},
            status=status.HTTP_204_NO_CONTENT
        )


# ========== Student Exercise Choice APIs ==========

class StudentExerciseChoiceListCreateAPIView(APIView):
    """
    List and Create Student Exercise Choices
    دریافت انتخاب‌های تمرین دانش‌آموز و ایجاد انتخاب جدید
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Student Exercise Choice'],
        summary='List Student Exercise Choices',
        description='دریافت انتخاب‌های تمرین دانش‌آموز',
        parameters=[
            OpenApiParameter('student', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by student ID'),
            OpenApiParameter('exercise_choice_group', OpenApiTypes.INT, required=False, location=OpenApiParameter.QUERY, description='Filter by exercise choice group'),
        ],
        responses={200: OpenApiResponse(description="List of student exercise choices")}
    )
    def get(self, request):
        # Students can only see their own choices, teachers see all
        if hasattr(request.user, 'role') and request.user.role == 'teacher':
            queryset = StudentExerciseChoice.objects.all()
        else:
            queryset = StudentExerciseChoice.objects.filter(student=request.user)
        
        # Filter by student if provided and user has permission
        student_id = request.query_params.get('student')
        if student_id and (hasattr(request.user, 'role') and request.user.role == 'teacher'):
            queryset = queryset.filter(student_id=student_id)
        
        # Filter by exercise choice group
        choice_group_id = request.query_params.get('exercise_choice_group')
        if choice_group_id:
            queryset = queryset.filter(exercise_choice_group_id=choice_group_id)
        
        serializer = StudentExerciseChoiceSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Student Exercise Choice'],
        summary='Create Student Exercise Choice',
        description='ایجاد انتخاب تمرین برای دانش‌آموز',
        request=StudentExerciseChoiceSerializer,
        responses={201: OpenApiResponse(description="Student exercise choice created successfully")}
    )
    def post(self, request):
        data = request.data.copy()
        data['student'] = request.user.id
        
        # Check if student already has a choice for this group
        choice_group_id = data.get('exercise_choice_group')
        if StudentExerciseChoice.objects.filter(
            student=request.user,
            exercise_choice_group_id=choice_group_id
        ).exists():
            return Response(
                {'error': _('شما قبلاً برای این گروه انتخاب کرده‌اید')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = StudentExerciseChoiceSerializer(data=data)
        if serializer.is_valid():
            serializer.save(student=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentExerciseChoiceRetrieveAPIView(APIView):
    """
    Retrieve Student Exercise Choice Details
    دریافت جزئیات انتخاب تمرین دانش‌آموز
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Student Exercise Choice'],
        summary='Retrieve Student Exercise Choice',
        description='دریافت جزئیات انتخاب تمرین دانش‌آموز',
        responses={200: OpenApiResponse(description="Student exercise choice details")}
    )
    def get(self, request, id):
        try:
            student_choice = StudentExerciseChoice.objects.get(id=id)
        except StudentExerciseChoice.DoesNotExist:
            return Response(
                {'error': _('انتخاب یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission: student can see only their own choice, teachers can see all
        if (not hasattr(request.user, 'role') or request.user.role != 'teacher') and student_choice.student_id != request.user.id:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = StudentExerciseChoiceSerializer(student_choice)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentExerciseChoiceUpdateAPIView(APIView):
    """
    Update Student Exercise Choice
    بروزرسانی انتخاب تمرین دانش‌آموز
    """
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    @extend_schema(
        tags=['Student Exercise Choice'],
        summary='Update Student Exercise Choice',
        description='بروزرسانی انتخاب تمرین دانش‌آموز',
        request=StudentExerciseChoiceSerializer,
        responses={200: OpenApiResponse(description="Student exercise choice updated successfully")}
    )
    def post(self, request, id):
        try:
            student_choice = StudentExerciseChoice.objects.get(id=id)
        except StudentExerciseChoice.DoesNotExist:
            return Response(
                {'error': _('انتخاب یافت نشد')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission: student can update only their own choice
        if student_choice.student_id != request.user.id:
            return Response(
                {'error': _('دسترسی محدود است')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = StudentExerciseChoiceSerializer(student_choice, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
