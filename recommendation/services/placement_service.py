from django.utils import timezone

from recommendation.models import EnglishPlacementAssessment


def create_placement_history_from_result(response, result):
    """
    Create one immutable history snapshot for the current submission.

    The response/result rows are still updated in place, preserving the existing
    one-response-per-user-per-test behaviour. Only this assessment history grows.
    """
    if response.test.test_type != 'english_placement':
        return None

    suggested_level = (result.summary or {}).get('suggested_level')

    return EnglishPlacementAssessment.objects.create(
        student=response.user,
        response=response,
        test=response.test,
        suggested_level=suggested_level,
        source=EnglishPlacementAssessment.Source.TEST,
        status=EnglishPlacementAssessment.Status.PENDING,
        response_completed_at=response.completed_at,
        raw_scores_snapshot=dict(result.raw_scores or {}),
        result_summary_snapshot=dict(result.summary or {}),
    )


def sync_user_english_level(assessment):
    """
    همگام‌سازی سطح نهایی تعیین‌شده با پروفایل دانش‌آموز.
    """

    student = assessment.student
    final_level = assessment.final_level

    if not student or not final_level:
        return

    level_code = getattr(final_level, 'code', final_level)

    if isinstance(level_code, str):
        level_code = level_code.lower()

    if assessment.source == EnglishPlacementAssessment.Source.ADMIN:
        user_level_source = 'admin'
    else:
        user_level_source = 'placement_test'

    student.english_level = level_code
    student.english_level_source = user_level_source
    student.english_level_updated_at = (
        assessment.assessed_at or timezone.now()
    )
    student.english_level_assessed_by = assessment.assessed_by

    student.save(
        update_fields=[
            'english_level',
            'english_level_source',
            'english_level_updated_at',
            'english_level_assessed_by',
        ]
    )
