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


def sync_user_english_level(assessment, assessor):
    """
    Copy the final approved level to User when the project User model contains
    the documented English-level fields. Kept defensive because the account app
    was not included in the supplied archive.
    """
    if not assessment.final_level:
        return False

    user = assessment.student
    field_names = {field.name for field in user._meta.get_fields()}
    required = {
        'english_level',
        'english_level_source',
        'english_level_updated_at',
        'english_level_assessed_by',
    }
    if not required.issubset(field_names):
        return False

    if assessment.source == EnglishPlacementAssessment.Source.TEACHER:
        source = 'teacher'
    elif assessment.response_id:
        source = 'placement_test'
    else:
        source = 'admin'

    user.english_level = assessment.final_level
    user.english_level_source = source
    user.english_level_updated_at = assessment.assessed_at or timezone.now()
    user.english_level_assessed_by = assessor
    user.save(update_fields=[
        'english_level',
        'english_level_source',
        'english_level_updated_at',
        'english_level_assessed_by',
    ])
    return True
