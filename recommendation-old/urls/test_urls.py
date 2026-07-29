from django.urls import path
from recommendation.views import (
    scale_views,
    student_test_views,
    teacher_placement_views,
    test_views,
)

app_name = "recommendation"

urlpatterns = [

    path(
        "tests/",
        test_views.test_list_view,
        name="test_list"
    ),

    path(
        "tests/create/",
        test_views.test_create_view,
        name="test_create"
    ),

    path(
        "tests/<int:test_id>/",
        test_views.test_detail_view,
        name="test_detail"
    ),

    path(
        "tests/<int:test_id>/edit/",
        test_views.test_edit_view,
        name="test_edit"
    ),

    path(
        "tests/<int:test_id>/delete/",
        test_views.test_delete_view,
        name="test_delete"
    ),

    path(
        "tests/<int:test_id>/weights/",
        test_views.test_weights_view,
        name="test_weights"
    ),

    path(
        "tests/<int:test_id>/scales/<int:scale_id>/interpretations/",
        scale_views.scale_interpretations_manage_view,
        name="scale_interpretations",
    ),
    
    path('psychological-tests/', student_test_views.psychological_tests_list_api, name='psychological_tests_list'),
    path('get-register-psychological-tests/', student_test_views.last_test_register, name='register_psychological_tests_list'),
    path('psychological-tests/<int:test_id>/', student_test_views.psychological_test_detail_api, name='psychological_test_detail'),
    path('psychological-tests/<int:test_id>/submit/', student_test_views.psychological_test_submit_api, name='psychological_test_submit'),
    path('psychological-tests/<int:test_id>/view-answers/', student_test_views.psychological_test_view_answers_api, name='psychological_test_view_answers'),
    path('psychological-tests/<int:test_id>/result/', student_test_views.psychological_test_result_api, name='psychological_test_result'),

    path(
        'teacher/students/<int:student_id>/placement-history/',
        teacher_placement_views.student_placement_history_api,
        name='teacher_student_placement_history',
    ),
    path(
        'teacher/placement-history/<int:assessment_id>/',
        teacher_placement_views.placement_assessment_detail_api,
        name='teacher_placement_assessment_detail',
    ),
    

]
