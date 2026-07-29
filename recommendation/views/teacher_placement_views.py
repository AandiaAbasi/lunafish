import logging

from django.contrib.auth import get_user_model
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from recommendation.models import EnglishPlacementAssessment
from recommendation.permissions import IsTeacherOrStaff
from recommendation.services.placement_history_service import (
    build_assessment_details,
    build_assessment_list_item,
    serialize_student,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def _positive_int(value, default, maximum=None):
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default

    result = max(result, 1)
    if maximum is not None:
        result = min(result, maximum)
    return result


@api_view(["GET"])
@permission_classes([IsTeacherOrStaff])
def student_placement_history_api(request, student_id):
    """
    Return the immutable English placement history of one student.

    Query parameters:
    - page: default 1
    - page_size: default 10, maximum 50
    - status: pending | confirmed | overridden
    - source: test | admin | teacher
    - test_id: filter by placement test
    - search: search in test title or evaluator note
    """
    try:
        try:
            student = User.objects.get(pk=student_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "دانش‌آموز مورد نظر یافت نشد.",
            }, status=status.HTTP_404_NOT_FOUND)

        if getattr(student, "role", None) == "teacher":
            return Response({
                "success": False,
                "message": "شناسه ارسال‌شده متعلق به دانش‌آموز نیست.",
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = (
            EnglishPlacementAssessment.objects
            .filter(student=student)
            .select_related(
                "student",
                "test",
                "response__test",
                "assessed_by",
                "online_class__teacher",
            )
            .order_by("-created_at")
        )

        status_filter = request.GET.get("status", "").strip()
        if status_filter:
            valid_statuses = {
                choice[0] for choice in EnglishPlacementAssessment.Status.choices
            }
            if status_filter not in valid_statuses:
                return Response({
                    "success": False,
                    "message": "مقدار status معتبر نیست.",
                }, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(status=status_filter)

        source_filter = request.GET.get("source", "").strip()
        if source_filter:
            valid_sources = {
                choice[0] for choice in EnglishPlacementAssessment.Source.choices
            }
            if source_filter not in valid_sources:
                return Response({
                    "success": False,
                    "message": "مقدار source معتبر نیست.",
                }, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(source=source_filter)

        test_id = request.GET.get("test_id")
        if test_id:
            try:
                test_id = int(test_id)
            except (TypeError, ValueError):
                return Response({
                    "success": False,
                    "message": "test_id باید عدد باشد.",
                }, status=status.HTTP_400_BAD_REQUEST)

            queryset = queryset.filter(
                Q(test_id=test_id) | Q(response__test_id=test_id)
            )

        search = request.GET.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(test__title__icontains=search)
                | Q(response__test__title__icontains=search)
                | Q(note__icontains=search)
            )

        page = _positive_int(request.GET.get("page"), 1)
        page_size = _positive_int(request.GET.get("page_size"), 10, maximum=50)

        paginator = Paginator(queryset, page_size)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages or 1)
            page = page_obj.number

        results = [
            build_assessment_list_item(item)
            for item in page_obj.object_list
        ]

        all_student_assessments = EnglishPlacementAssessment.objects.filter(
            student=student
        )
        latest = (
            all_student_assessments
            .select_related(
                "test",
                "response__test",
                "assessed_by",
                "online_class__teacher",
            )
            .order_by("-created_at")
            .first()
        )

        current_placement = None
        if latest:
            current_placement = build_assessment_list_item(latest)["placement"]

        stats = {
            "total": all_student_assessments.count(),
            "pending": all_student_assessments.filter(
                status=EnglishPlacementAssessment.Status.PENDING
            ).count(),
            "confirmed": all_student_assessments.filter(
                status=EnglishPlacementAssessment.Status.CONFIRMED
            ).count(),
            "overridden": all_student_assessments.filter(
                status=EnglishPlacementAssessment.Status.OVERRIDDEN
            ).count(),
            "test": all_student_assessments.filter(
                source=EnglishPlacementAssessment.Source.TEST
            ).count(),
            "manual": all_student_assessments.exclude(
                source=EnglishPlacementAssessment.Source.TEST
            ).count(),
        }

        return Response({
            "success": True,
            "message": "تاریخچه تعیین سطح دانش‌آموز با موفقیت دریافت شد.",
            "data": {
                "student": serialize_student(student),
                "current_placement": current_placement,
                "results": results,
                "stats": stats,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_pages": paginator.num_pages,
                    "total_count": paginator.count,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                },
            },
        }, status=status.HTTP_200_OK)

    except Exception as exc:
        logger.error(
            "Error loading student placement history: %s",
            str(exc),
            exc_info=True,
        )
        return Response({
            "success": False,
            "message": "خطا در دریافت تاریخچه تعیین سطح دانش‌آموز.",
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsTeacherOrStaff])
def placement_assessment_detail_api(request, assessment_id):
    """Return full score, level and skill details for one history item."""
    try:
        try:
            assessment = (
                EnglishPlacementAssessment.objects
                .select_related(
                "student",
                "test",
                "response__test",
                "assessed_by",
                "online_class__teacher",
            )
                .get(pk=assessment_id)
            )
        except EnglishPlacementAssessment.DoesNotExist:
            return Response({
                "success": False,
                "message": "نتیجه تعیین سطح مورد نظر یافت نشد.",
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": True,
            "message": "جزئیات نتیجه تعیین سطح با موفقیت دریافت شد.",
            "data": {
                "student": serialize_student(assessment.student),
                **build_assessment_details(assessment),
            },
        }, status=status.HTTP_200_OK)

    except Exception as exc:
        logger.error(
            "Error loading placement assessment detail: %s",
            str(exc),
            exc_info=True,
        )
        return Response({
            "success": False,
            "message": "خطا در دریافت جزئیات نتیجه تعیین سطح.",
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
