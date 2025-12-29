from django.urls import path
from . import views

app_name = 'exercise'

urlpatterns = [
    # ========== Exercise Management ==========
    # Teacher can create, update, delete exercises
    path('exercises/', views.ExerciseListCreateAPIView.as_view(), name='exercise_list_create'),
    path('exercises/<int:id>/', views.ExerciseRetrieveAPIView.as_view(), name='exercise_retrieve'),
    path('exercises/<int:id>/update/', views.ExerciseUpdateAPIView.as_view(), name='exercise_update'),
    path('exercises/<int:id>/delete/', views.ExerciseDeleteAPIView.as_view(), name='exercise_delete'),
    
    # ========== Question Management ==========
    path('questions/', views.QuestionListCreateAPIView.as_view(), name='question_list_create'),
    path('questions/<int:id>/', views.QuestionRetrieveAPIView.as_view(), name='question_retrieve'),
    path('questions/<int:id>/update/', views.QuestionUpdateAPIView.as_view(), name='question_update'),
    path('questions/<int:id>/delete/', views.QuestionDeleteAPIView.as_view(), name='question_delete'),
    
    # ========== Question Options Management ==========
    path('options/', views.QuestionOptionListCreateAPIView.as_view(), name='option_list_create'),
    path('options/<int:id>/update/', views.QuestionOptionUpdateAPIView.as_view(), name='option_update'),
    path('options/<int:id>/delete/', views.QuestionOptionDeleteAPIView.as_view(), name='option_delete'),
    
    # ========== Student Exercise Attempts ==========
    path('attempts/', views.StudentExerciseAttemptListAPIView.as_view(), name='attempt_list'),
    path('attempts/<int:id>/', views.StudentExerciseAttemptRetrieveAPIView.as_view(), name='attempt_retrieve'),
    path('attempts/<int:id>/submit/', views.StudentExerciseAttemptSubmitAPIView.as_view(), name='attempt_submit'),
    path('attempts/<int:id>/grade/', views.StudentExerciseAttemptGradeAPIView.as_view(), name='attempt_grade'),
    
    # ========== Student Answers ==========
    path('answers/', views.StudentQuestionAnswerListCreateAPIView.as_view(), name='answer_list_create'),
    path('answers/<int:id>/update/', views.StudentQuestionAnswerUpdateAPIView.as_view(), name='answer_update'),
    
    # ========== Exercise Choice Groups ==========
    path('choices/', views.ExerciseChoiceListCreateAPIView.as_view(), name='choice_list_create'),
    path('choices/<int:id>/', views.ExerciseChoiceRetrieveAPIView.as_view(), name='choice_retrieve'),
    path('choices/<int:id>/update/', views.ExerciseChoiceUpdateAPIView.as_view(), name='choice_update'),
    path('choices/<int:id>/delete/', views.ExerciseChoiceDeleteAPIView.as_view(), name='choice_delete'),
    
    # ========== Student Exercise Choices ==========
    path('student-choices/', views.StudentExerciseChoiceListCreateAPIView.as_view(), name='student_choice_list_create'),
    path('student-choices/<int:id>/', views.StudentExerciseChoiceRetrieveAPIView.as_view(), name='student_choice_retrieve'),
    path('student-choices/<int:id>/update/', views.StudentExerciseChoiceUpdateAPIView.as_view(), name='student_choice_update'),
]
