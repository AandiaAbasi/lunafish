from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics, parsers
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.db import models, transaction
from django.http import StreamingHttpResponse, HttpResponse
import re
from django.core.paginator import Paginator
from recommendation.selectors import get_last_test_register
from recommendation.serializers import PsychologicalTestSerializer
import jdatetime
import logging
logger = logging.getLogger(__name__)


def _assessment_online_class(assessment):
    if not assessment:
        return None

    try:
        return assessment.online_class
    except (ObjectDoesNotExist, AttributeError):
        return None


def _select_online_class_assessment(assessments):
    """
    Select the most useful class for the student test list:
    active first, then scheduled, then the latest ended/cancelled class.
    Assessments are expected to be ordered newest first.
    """
    scheduled_assessment = None
    fallback_assessment = None

    for assessment in assessments:
        online_class = _assessment_online_class(assessment)
        if not online_class:
            continue

        if fallback_assessment is None:
            fallback_assessment = assessment

        if (
            online_class.status == online_class.STATUS_ACTIVE
            and online_class.actual_start
            and not online_class.actual_end
        ):
            return assessment

        if (
            scheduled_assessment is None
            and online_class.status == online_class.STATUS_SCHEDULED
        ):
            scheduled_assessment = assessment

    return scheduled_assessment or fallback_assessment

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def psychological_tests_list_api(request):
    """
    List tests together with the current user's response and the most relevant
    online class created from that test's placement history.

    Online class selection priority:
    1. active and joinable class
    2. scheduled class
    3. latest ended/cancelled class

    The nested ``online_class`` object contains complete class information.
    Compatibility aliases such as ``online_class_id`` and
    ``online_actual_start`` are also returned so the current booking join flow
    can be reused without a second classroom implementation.
    """
    try:
        from django.db.models import Count, Prefetch, Q
        from recommendation.models import (
            EnglishPlacementAssessment,
            PsychologicalTest,
            StudentTestResponse,
        )
        from recommendation.services.placement_history_service import (
            serialize_online_class,
        )

        search_query = request.GET.get('search', '').strip()

        tests_qs = PsychologicalTest.objects.all()
        if search_query:
            tests_qs = tests_qs.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        tests_qs = tests_qs.annotate(
            questions_total=Count('questions', distinct=True)
        ).order_by('id')

        placement_assessments_qs = (
            EnglishPlacementAssessment.objects
            .select_related(
                'test',
                'assessed_by',
                'online_class__teacher',
            )
            .annotate(
                online_class_enrolled_count=Count(
                    'online_class__enrollments',
                    filter=Q(online_class__enrollments__left_at__isnull=True),
                    distinct=True,
                )
            )
            .order_by('-created_at')
        )

        user_responses = (
            StudentTestResponse.objects
            .filter(user=request.user, test__in=tests_qs)
            .select_related('test')
            .prefetch_related(
                Prefetch(
                    'placement_assessments',
                    queryset=placement_assessments_qs,
                    to_attr='placement_history_cache',
                )
            )
        )

        responses_map = {
            response.test_id: response
            for response in user_responses
        }

        tests_data = []
        stats = {
            'not_started': 0,
            'in_progress': 0,
            'completed': 0,
            'total': 0,
        }

        for test in tests_qs:
            response = responses_map.get(test.id)

            if response:
                test_status = response.status
                started_at = response.started_at
                completed_at = response.completed_at
                is_completed = test_status == 'completed'
                assessments = getattr(
                    response,
                    'placement_history_cache',
                    [],
                )
            else:
                test_status = 'not_started'
                started_at = None
                completed_at = None
                is_completed = False
                assessments = []

            latest_assessment = assessments[0] if assessments else None
            class_assessment = _select_online_class_assessment(assessments)
            online_class = (
                serialize_online_class(class_assessment)
                if class_assessment
                else None
            )

            completed_at_jalali = ''
            started_at_jalali = ''

            if completed_at:
                completed_at_jalali = jdatetime.datetime.fromgregorian(
                    datetime=timezone.localtime(completed_at)
                ).strftime('%Y/%m/%d - %H:%M')

            if started_at:
                started_at_jalali = jdatetime.datetime.fromgregorian(
                    datetime=timezone.localtime(started_at)
                ).strftime('%Y/%m/%d - %H:%M')

            online_class_id = online_class['id'] if online_class else None
            online_actual_start = (
                online_class['actual_start']['iso']
                if online_class
                else None
            )
            online_actual_end = (
                online_class['actual_end']['iso']
                if online_class
                else None
            )

            test_item = {
                'id': test.id,
                'title': test.title,
                'description': test.description,
                'test_type': getattr(test, 'test_type', None),
                'question_count': test.questions_total,

                'assigned_at': None,
                'assigned_at_jalali': '',
                'deadline': None,
                'deadline_jalali': '',
                'deadline_passed': False,

                'status': test_status,
                'status_display': {
                    'not_started': 'شروع نشده',
                    'in_progress': 'در حال پاسخ',
                    'completed': 'تکمیل شده',
                }.get(test_status, 'شروع نشده'),

                'is_completed': is_completed,
                'is_expired': False,
                'can_take': True,

                'response_id': response.id if response else None,
                'completed_at': (
                    completed_at.isoformat()
                    if completed_at
                    else None
                ),
                'completed_at_jalali': completed_at_jalali,
                'started_at': (
                    started_at.isoformat()
                    if started_at
                    else None
                ),
                'started_at_jalali': started_at_jalali,

                'latest_placement_assessment_id': (
                    latest_assessment.id
                    if latest_assessment
                    else None
                ),
                'class_placement_assessment_id': (
                    class_assessment.id
                    if class_assessment
                    else None
                ),

                # Full nested payload.
                'online_class': online_class,
                'has_online_class': bool(online_class),
                'can_join_online_class': bool(
                    online_class and online_class['can_join']
                ),

                # Compatibility fields matching the booking list.
                'online_class_id': online_class_id,
                'online_class_status': (
                    online_class['status']
                    if online_class
                    else None
                ),
                'online_scheduled_start': (
                    online_class['scheduled_start']['iso']
                    if online_class
                    else None
                ),
                'online_scheduled_end': (
                    online_class['scheduled_end']['iso']
                    if online_class
                    else None
                ),
                'online_actual_start': online_actual_start,
                'online_actual_end': online_actual_end,
            }

            tests_data.append(test_item)

            if test_status in stats:
                stats[test_status] += 1
            else:
                stats['not_started'] += 1
            stats['total'] += 1

        filter_status = request.GET.get(
            'filter_status',
            'all',
        ).strip().lower()

        if filter_status != 'all':
            if filter_status == 'open':
                tests_data = [
                    item for item in tests_data
                    if item['status'] in ['not_started', 'in_progress']
                ]
            elif filter_status == 'closed':
                tests_data = [
                    item for item in tests_data
                    if item['status'] == 'completed' or item['is_expired']
                ]
            elif filter_status in [
                'not_started',
                'in_progress',
                'completed',
            ]:
                tests_data = [
                    item for item in tests_data
                    if item['status'] == filter_status
                ]

        try:
            page = max(int(request.GET.get('page', 1)), 1)
        except (TypeError, ValueError):
            page = 1

        try:
            page_size = max(int(request.GET.get('page_size', 10)), 1)
        except (TypeError, ValueError):
            page_size = 10

        page_size = min(page_size, 50)
        paginator = Paginator(tests_data, page_size)

        try:
            tests_page = paginator.page(page)
        except Exception:
            tests_page = paginator.page(1)
            page = 1

        return Response({
            'success': True,
            'message': 'لیست تست‌ها با موفقیت دریافت شد',
            'data': {
                'tests': list(tests_page),
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': tests_page.has_next(),
                    'has_previous': tests_page.has_previous(),
                },
                'stats': stats,
            },
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            'Error in psychological_tests_list_api: %s',
            str(e),
            exc_info=True,
        )
        return Response({
            'success': False,
            'message': f'خطا در دریافت لیست تست‌ها: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])

@permission_classes([AllowAny])
def psychological_test_detail_api(request, test_id):
    """
    Get detailed information about a psychological test.
    Returns test questions and options if test is not yet taken or in progress.
    
    Response:
    {
        "success": true,
        "message": "جزئیات تست با موفقیت دریافت شد",
        "data": {
            "test": {...},
            "assignment": {...},
            "response": {...} or null,
            "questions": [...]
        }
    }
    """
    try:
        from recommendation.models import PsychologicalTest, StudentTestResponse
        from django.utils import timezone
        
         
        
        # Get test
        try:
            test = PsychologicalTest.objects.get(
                id=test_id,
                is_active=True
            )
        except PsychologicalTest.DoesNotExist:
            return Response({
                'success': False,
                'message': 'تست مورد نظر یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if test is assigned to user's class
        
        
        
        response = None
        has_started = False
        is_completed = False
        
        # Check if deadline has passed
        deadline_passed = False
        
        
        # Get questions with options
        questions = test.questions.prefetch_related('options').order_by('order')
        questions_data = []
        
        for question in questions:
            options_data = []
            if question.question_type == 'multiple_choice':
                for option in question.options.all().order_by('order'):
                    options_data.append({
                        'id': option.id,
                        'text': option.option_text,
                        'order': option.order,
                        'icon': option.icon
                    })
            
            questions_data.append({
                'id': question.id,
                'icon': question.icon,
                'text': question.question_text,
                'question_type': question.question_type,
                'question_type_display': {
                    'multiple_choice': 'چند گزینه‌ای',
                    'text_input': 'ورودی متنی کوتاه',
                    'textarea': 'متن بلند'
                }.get(question.question_type, ''),
                'order': question.order,
                'is_required': question.is_required,
                'options': options_data
            })
        
        # Prepare response data
        response_data = None
        if response:
            started_at_jalali = ''
            if response.started_at:
                j_date = jdatetime.datetime.fromgregorian(datetime=response.started_at)
                started_at_jalali = j_date.strftime('%Y/%m/%d - %H:%M')
            
            completed_at_jalali = ''
            if response.completed_at:
                j_date = jdatetime.datetime.fromgregorian(datetime=response.completed_at)
                completed_at_jalali = j_date.strftime('%Y/%m/%d - %H:%M')
            
            response_data = {
                'id': response.id,
                'status': response.status,
                'status_display': {
                    'not_started': 'شروع نشده',
                    'in_progress': 'در حال پاسخ',
                    'completed': 'تکمیل شده'
                }.get(response.status, ''),
                'started_at': response.started_at.isoformat() if response.started_at else None,
                'started_at_jalali': started_at_jalali,
                'completed_at': response.completed_at.isoformat() if response.completed_at else None,
                'completed_at_jalali': completed_at_jalali
            }
        
        test_data = {
            'id': test.id,
            'title': test.title,
            'description': test.description,
            'question_count': len(questions_data),
            'is_active': test.is_active
        }
         
        
        return Response({
            'success': True,
            'message': 'جزئیات تست با موفقیت دریافت شد',
            'data': {
                'test': test_data,
                'response': response_data,
                'questions': questions_data,
                'has_started': has_started,
                'is_completed': is_completed,
                'can_take': True
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in psychological_test_detail_api: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': f'خطا در دریافت جزئیات تست: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])

@permission_classes([IsAuthenticated])
@transaction.atomic
def psychological_test_submit_api(request, test_id):
    """
    Submit answers to a psychological test.
    
    Request Body:
    {
        "answers": {
            "question_id": "selected_option_id" (for multiple_choice),
            "question_id": "text answer" (for text_input/textarea)
        }
    }
    
    Response:
    {
        "success": true,
        "message": "تست با موفقیت ثبت شد",
        "data": {
            "response_id": 123,
            "completed_at": "...",
            "has_result": true/false
        }
    }
    """
    try:
        from recommendation.models import (
            PsychologicalTest, StudentTestResponse,
            TestQuestion, StudentAnswer, QuestionOption
        )
        from django.utils import timezone
        
        # Get user from JWT token
        user = request.user
        if not user:
            return Response({
                'success': False,
                'message': 'دانش‌آموز یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
         
        # Get test
        try:
            test = PsychologicalTest.objects.get(id=test_id, is_active=True)
        except PsychologicalTest.DoesNotExist:
            return Response({
                'success': False,
                'message': 'تست مورد نظر یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
         
       
        # Get or create user response
        response, created = StudentTestResponse.objects.get_or_create(
            test=test,
            user=user,
            defaults={
                'status': 'in_progress',
                'started_at': timezone.now()
            }
        )
        
        # If not newly created and status is not_started, update to in_progress
        if not created and response.status == 'not_started':
            response.status = 'in_progress'
            response.started_at = timezone.now()
            response.save()
        
        # Check if already completed
       
        # Get answers from request
        answers_dict = request.data.get('answers', {})
        if not answers_dict:
            return Response({
                'success': False,
                'message': 'لطفاً به سوالات پاسخ دهید'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process answers
        questions = test.questions.all()
        errors = []
        
        for question in questions:
            answer_value = answers_dict.get(str(question.id))
            
            if question.question_type == 'multiple_choice':
                # Expecting option ID
                if answer_value:
                    try:
                        option = QuestionOption.objects.get(
                            id=int(answer_value),
                            question=question
                        )
                        # Create or update answer
                        StudentAnswer.objects.update_or_create(
                            response=response,
                            question=question,
                            defaults={
                                'selected_option': option,
                                'text_answer': ''
                            }
                        )
                    except (QuestionOption.DoesNotExist, ValueError):
                        if question.is_required:
                            errors.append(f'گزینه انتخابی برای سوال {question.order} نامعتبر است')
                elif question.is_required:
                    errors.append(f'لطفاً به سوال {question.order} پاسخ دهید')
            
            else:  # text_input or textarea
                if answer_value and str(answer_value).strip():
                    # Create or update answer
                    StudentAnswer.objects.update_or_create(
                        response=response,
                        question=question,
                        defaults={
                            'selected_option': None,
                            'text_answer': str(answer_value).strip()
                        }
                    )
                elif question.is_required:
                    errors.append(f'لطفاً به سوال {question.order} پاسخ دهید')
        
        if errors:
            return Response({
                'success': False,
                'message': 'خطاهای زیر رخ داد',
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as completed. The existing row is intentionally updated so the
        # current one-response-per-user-per-test behaviour remains unchanged.
        response.status = 'completed'
        response.completed_at = timezone.now()
        response.save(update_fields=['status', 'completed_at', 'updated_at'])

        # Calculate immediately and save an immutable placement snapshot.
        from recommendation.utils import calculate_test_result
        from recommendation.services.placement_service import (
            create_placement_history_from_result,
        )

        result = calculate_test_result(response)
        create_placement_history_from_result(response, result)
        has_result = result is not None
        
        completed_at_jalali = ''
        if response.completed_at:
            j_date = jdatetime.datetime.fromgregorian(datetime=response.completed_at)
            completed_at_jalali = j_date.strftime('%Y/%m/%d - %H:%M')
        
        return Response({
            'success': True,
            'message': 'تست با موفقیت ثبت شد. از صبر و دقت شما متشکریم',
            'data': {
                'response_id': response.id,
                'completed_at': response.completed_at.isoformat(),
                'completed_at_jalali': completed_at_jalali,
                'has_result': has_result
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in psychological_test_submit_api: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': f'خطا در ثبت تست: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])

@permission_classes([IsAuthenticated])
def psychological_test_view_answers_api(request, test_id):
    """
    View submitted answers to a completed test - read-only.
    
    Response:
    {
        "success": true,
        "message": "پاسخ‌های تست با موفقیت دریافت شد",
        "data": {
            "test": {...},
            "response": {...},
            "questions_with_answers": [...]
        }
    }
    """
    try:
        from recommendation.models import PsychologicalTest, StudentTestResponse, StudentAnswer
        
        # Get user from JWT token
        user = request.user
        if not user:
            return Response({
                'success': False,
                'message': 'دانش‌آموز یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get test
        try:
            test = PsychologicalTest.objects.get(
                id=test_id,
                is_active=True
            )
        except PsychologicalTest.DoesNotExist:
            return Response({
                'success': False,
                'message': 'تست مورد نظر یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get user's response
        try:
            response = StudentTestResponse.objects.get(test=test, user=user)
        except StudentTestResponse.DoesNotExist:
            return Response({
                'success': False,
                'message': 'شما هنوز این تست را شروع نکرده‌اید'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if test is completed
        if response.status != 'completed':
            return Response({
                'success': False,
                'message': 'شما هنوز این تست را تکمیل نکرده‌اید'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all questions with answers
        questions = test.questions.prefetch_related('options').order_by('order')
        answers = StudentAnswer.objects.filter(
            response=response
        ).select_related('question', 'selected_option')
        
        # Create answers dict
        answers_dict = {answer.question_id: answer for answer in answers}
        
        # Combine questions with answers
        questions_with_answers = []
        for question in questions:
            answer = answers_dict.get(question.id)
            
            # Prepare options
            options_data = []
            if question.question_type == 'multiple_choice':
                for option in question.options.all().order_by('order'):
                    options_data.append({
                        'id': option.id,
                        'text': option.option_text,
                        'order': option.order,
                        'is_selected': answer and answer.selected_option_id == option.id
                    })
            
            # Prepare answer data
            answer_data = None
            if answer:
                if question.question_type == 'multiple_choice':
                    answer_data = {
                        'type': 'option',
                        'selected_option_id': answer.selected_option_id,
                        'selected_option_text': answer.selected_option.option_text if answer.selected_option else ''
                    }
                else:
                    answer_data = {
                        'type': 'text',
                        'text': answer.text_answer
                    }
            
            questions_with_answers.append({
                'question': {
                    'id': question.id,
                    'text': question.question_text,
                    'question_type': question.question_type,
                    'question_type_display': {
                        'multiple_choice': 'چند گزینه‌ای',
                        'text_input': 'ورودی متنی کوتاه',
                        'textarea': 'متن بلند'
                    }.get(question.question_type, ''),
                    'order': question.order,
                    'options': options_data
                },
                'answer': answer_data
            })
        
        # Convert dates to Jalali
        completed_at_jalali = ''
        if response.completed_at:
            j_date = jdatetime.datetime.fromgregorian(datetime=response.completed_at)
            completed_at_jalali = j_date.strftime('%Y/%m/%d - %H:%M')
        
        test_data = {
            'id': test.id,
            'title': test.title,
            'description': test.description,
        }
        
        response_data = {
            'id': response.id,
            'status': response.status,
            'completed_at': response.completed_at.isoformat(),
            'completed_at_jalali': completed_at_jalali
        }
        
        return Response({
            'success': True,
            'message': 'پاسخ‌های تست با موفقیت دریافت شد',
            'data': {
                'test': test_data,
                'response': response_data,
                'questions_with_answers': questions_with_answers
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in psychological_test_view_answers_api: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': f'خطا در دریافت پاسخ‌های تست: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def psychological_test_result_api(request, test_id):
    """
    Return an English placement result prepared for direct UI rendering.

    Level and skill metadata are entirely database-driven:
    - TestScale.scale_type determines the group.
    - TestScale.rank determines level order.
    - TestScale.pass_score determines pass/fail.
    - TestScale title/description and ScaleInterpretation provide display copy.

    ``scale_results`` remains in the response temporarily for backward
    compatibility with older application versions.
    """
    try:
        from recommendation.models import (
            EnglishPlacementAssessment,
            PsychologicalTest,
            StudentTestResponse,
            TestScale,
        )

        user = request.user
        if not user:
            return Response({
                'success': False,
                'message': 'دانش‌آموز یافت نشد',
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            test = PsychologicalTest.objects.get(id=test_id, is_active=True)
        except PsychologicalTest.DoesNotExist:
            return Response({
                'success': False,
                'message': 'تست مورد نظر یافت نشد',
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            response = StudentTestResponse.objects.get(test=test, user=user)
        except StudentTestResponse.DoesNotExist:
            return Response({
                'success': False,
                'message': 'شما هنوز این تست را شروع نکرده‌اید',
            }, status=status.HTTP_404_NOT_FOUND)

        if response.status != 'completed':
            return Response({
                'success': False,
                'message': 'شما هنوز این تست را تکمیل نکرده‌اید',
            }, status=status.HTTP_400_BAD_REQUEST)

        if not test.scales.exists():
            return Response({
                'success': False,
                'message': 'این تست فاقد سیستم امتیازدهی است',
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from recommendation.utils import calculate_test_result
            result = calculate_test_result(response)
        except Exception as calc_error:
            logger.error(
                'Error calculating placement result: %s',
                str(calc_error),
                exc_info=True,
            )
            return Response({
                'success': False,
                'message': 'خطا در محاسبه نتیجه تست. لطفاً با مشاور تماس بگیرید',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        scales = list(
            TestScale.objects
            .filter(test=test)
            .prefetch_related('interpretations')
        )
        raw_scores = result.raw_scores or {}
        summary = result.summary or {}

        scale_details_map = {
            str(item.get('code')): item
            for item in summary.get('scale_details', [])
            if isinstance(item, dict) and item.get('code') is not None
        }

        def numeric_score(value, default=0.0):
            try:
                return float(value)
            except (TypeError, ValueError):
                return float(default)

        def serialize_interpretation(scale, score):
            matched = None
            for item in scale.interpretations.all():
                if item.min_score <= score <= item.max_score:
                    matched = item
                    break

            if not matched:
                return None

            return {
                'id': matched.id,
                'level': matched.title,
                'title': matched.title,
                'description': matched.description,
                'min_score': numeric_score(matched.min_score),
                'max_score': numeric_score(matched.max_score),
                'order': matched.order,
            }

        def serialize_scale_result(scale):
            raw_score = numeric_score(raw_scores.get(scale.code, 0))
            detail = scale_details_map.get(str(scale.code), {})
            percentage = numeric_score(detail.get('percentage', raw_score))
            percentage = max(0.0, min(100.0, percentage))
            pass_score = numeric_score(scale.pass_score)

            item = {
                'id': scale.id,
                'code': scale.code,
                'name': scale.title,
                'title': scale.title,
                'description': scale.description,
                'scale_type': scale.scale_type,
                'rank': scale.rank,
                'raw_score': raw_score,
                'percentage': round(percentage, 2),
                'pass_score': pass_score,
                'interpretation': serialize_interpretation(scale, raw_score),
            }

            if scale.scale_type == TestScale.ScaleType.LEVEL:
                item['passed'] = raw_score >= pass_score

            return item

        scale_results = [serialize_scale_result(scale) for scale in scales]

        level_results = sorted(
            [
                item for item in scale_results
                if item['scale_type'] == TestScale.ScaleType.LEVEL
            ],
            key=lambda item: (
                item['rank'] is None,
                item['rank'] if item['rank'] is not None else 0,
                item['id'],
            ),
        )

        skill_results = sorted(
            [
                item for item in scale_results
                if item['scale_type'] == TestScale.ScaleType.SKILL
            ],
            key=lambda item: (
                item['rank'] is None,
                item['rank'] if item['rank'] is not None else 0,
                item['id'],
            ),
        )

        other_results = [
            item for item in scale_results
            if item['scale_type'] not in {
                TestScale.ScaleType.LEVEL,
                TestScale.ScaleType.SKILL,
            }
        ]

        def normalize_level_value(value):
            if value is None:
                return ''
            return str(value).strip().lower().replace('-', '_')

        level_scale_map = {
            normalize_level_value(item['code']): item
            for item in level_results
        }

        def serialize_level(value):
            normalized = normalize_level_value(value)
            if not normalized:
                return None

            configured = level_scale_map.get(normalized)
            if configured:
                return {
                    'id': configured['id'],
                    'code': configured['code'],
                    'title': configured['title'],
                    'description': configured['description'],
                    'rank': configured['rank'],
                }

            # This is only a defensive fallback for an old stored result whose
            # scale no longer exists. New results always resolve from TestScale.
            return {
                'id': None,
                'code': str(value).replace('_', '-').upper(),
                'title': '',
                'description': '',
                'rank': None,
            }

        latest_assessment = (
            EnglishPlacementAssessment.objects
            .filter(response=response)
            .order_by('-created_at')
            .first()
        )

        suggested_level_value = summary.get('suggested_level')
        final_level_value = (
            latest_assessment.final_level
            if latest_assessment and latest_assessment.final_level
            else None
        )

        suggested_level = serialize_level(suggested_level_value)
        final_level = serialize_level(final_level_value)
        display_level = final_level or suggested_level

        placement = {
            'suggested_level': suggested_level,
            'final_level': final_level,
            'display_level': display_level,
            'is_final': bool(final_level),
            'status': (
                latest_assessment.status
                if latest_assessment
                else EnglishPlacementAssessment.Status.PENDING
            ),
            'source': latest_assessment.source if latest_assessment else None,
            'assessed_at': (
                latest_assessment.assessed_at.isoformat()
                if latest_assessment and latest_assessment.assessed_at
                else None
            ),
        }

        completed_at_jalali = ''
        if response.completed_at:
            j_date = jdatetime.datetime.fromgregorian(datetime=response.completed_at)
            completed_at_jalali = j_date.strftime('%Y/%m/%d - %H:%M')

        test_data = {
            'id': test.id,
            'title': test.title,
            'description': test.description,
            'test_type': test.test_type,
        }

        response_data = {
            'id': response.id,
            'status': response.status,
            'completed_at': response.completed_at.isoformat(),
            'completed_at_jalali': completed_at_jalali,
        }

        result_data = {
            'id': result.id,
            'raw_scores': raw_scores,
            'summary': summary,
            'suggested_level': suggested_level,
            'result_type': summary.get('result_type'),
        }

        return Response({
            'success': True,
            'message': 'نتیجه تست با موفقیت دریافت شد',
            'data': {
                'test': test_data,
                'response': response_data,
                'result': result_data,
                'placement': placement,
                'level_results': level_results,
                'skill_results': skill_results,
                'other_results': other_results,
                'scale_results': scale_results,
            },
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            'Error in psychological_test_result_api: %s',
            str(e),
            exc_info=True,
        )
        return Response({
            'success': False,
            'message': f'خطا در دریافت نتیجه تست: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def last_test_register(request):
    test = get_last_test_register()

    if not test:
        return Response(None, status=status.HTTP_200_OK)

    serializer = PsychologicalTestSerializer(test)
    return Response(serializer.data, status=status.HTTP_200_OK)