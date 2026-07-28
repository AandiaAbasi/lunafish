from django.db.models import Count
from recommendation.models import PsychologicalTest


def list_tests(search_query=None, status_filter=None):

    queryset = PsychologicalTest.objects.annotate(
        question_count=Count('questions', distinct=True)
    ).order_by('-created_at')

    if search_query:
        queryset = queryset.filter(title__icontains=search_query)

    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)

    if status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)

    return queryset




def get_test_detail_queryset():
    return PsychologicalTest.objects.prefetch_related(
        "questions__options",
        "scales__interpretations",
    )

def get_last_test_register():
    return PsychologicalTest.objects.filter(test_type='register').order_by('-id').first()