"""
API URLs - All mobile/app API endpoints
"""
from django.urls import path, re_path
from . import views

app_name = 'api'

urlpatterns = [
    # ========== Home Page ==========
    path('home/', views.HomePageAPIView.as_view(), name='home'),

    # ========== Authentication ==========
    path('send-otp/', views.SendOTPAPIView.as_view(), name='send_otp'),
    path('verify-otp/', views.VerifyOTPAPIView.as_view(), name='verify_otp'),
    path('complete-registration/', views.CompleteRegistrationAPIView.as_view(), name='complete_registration'),
    path('check-username/', views.CheckUsernameAPIView.as_view(), name='check_username'),
    path('login-password/', views.UserLoginPasswordAPIView.as_view(), name='user_login_password'),
    
    # ========== Teacher Authentication ==========
    path('teacher/login-password/', views.TeacherLoginPasswordAPIView.as_view(), name='teacher_login_password'),
    path('teacher/send-otp/', views.TeacherSendOTPAPIView.as_view(), name='teacher_send_otp'),
    path('teacher/verify-otp/', views.TeacherVerifyOTPAPIView.as_view(), name='teacher_verify_otp'),
    path('teacher/complete-registration/', views.TeacherCompleteRegistrationAPIView.as_view(), name='teacher_complete_registration'),
    
    # ========== Email-Based Authentication ==========
    path('user/send-email-otp/', views.UserSendEmailOTPAPIView.as_view(), name='user_send_email_otp'),
    path('user/verify-email-otp/', views.UserVerifyEmailOTPAPIView.as_view(), name='user_verify_email_otp'),
    path('teacher/send-email-otp/', views.TeacherSendEmailOTPAPIView.as_view(), name='teacher_send_email_otp'),
    path('teacher/verify-email-otp/', views.TeacherVerifyEmailOTPAPIView.as_view(), name='teacher_verify_email_otp'),
    
    # ========== Profile Management ==========
    path('fetch-user/', views.FetchUserAPIView.as_view(), name='fetch_user'),
    path('profile/', views.UserProfileAPIView.as_view(), name='profile'),
    # Legacy endpoint for backward compatibility
    path('teacher-profile/', views.UserProfileAPIView.as_view(), name='teacher_profile'),
    
    # ========== Complete Profile ==========
    path('complete-student-profile/', views.CompleteStudentProfileAPIView.as_view(), name='complete_student_profile'),
    path('complete-teacher-profile/', views.CompleteTeacherProfileAPIView.as_view(), name='complete_teacher_profile'),
    
    path('promote-to-teacher/', views.PromoteToTeacherAPIView.as_view(), name='promote_to_teacher'),
    
    # ========== Avatar Templates ==========
    path('avatars/', views.AvatarTemplateListAPIView.as_view(), name='avatar_list'),
    path('select-avatar/', views.SelectAvatarAPIView.as_view(), name='select_avatar'),
    
    # ========== Settings & Security ==========
    path('change-password/', views.ChangePasswordAPIView.as_view(), name='change_password'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),
    
    # ========== Core Content ==========
    path('articles/', views.ArticleListAPIView.as_view(), name='article_list'),
    path('articles/<int:pk>/', views.ArticleDetailAPIView.as_view(), name='article_detail'),
    path('faqs/', views.FAQListAPIView.as_view(), name='faq_list'),
    path('about/', views.AboutAPIView.as_view(), name='about'),
    path('terms/', views.TermListAPIView.as_view(), name='terms'),
    path('privacy/', views.PrivacyListAPIView.as_view(), name='privacy'),
    path('contact/', views.ContactListAPIView.as_view(), name='contact'),
    path('contact/phone/', views.ContactPhoneAPIView.as_view(), name='contact_phone'),
    
    # ========== Teacher Time Slots ==========
    path('teacher/availability/', views.TeacherAvailabilityListAPIView.as_view(), name='availability_list'),
    path('teacher/availability/create/', views.CreateTeacherAvailabilityAPIView.as_view(), name='availability_create'),
    path('teacher/availability/bulk-create/', views.BulkCreateTeacherAvailabilityAPIView.as_view(), name='availability_bulk_create'),
    path('teacher/availability/<int:id>/update/', views.UpdateTeacherAvailabilityAPIView.as_view(), name='availability_update'),
    path('teacher/availability/<int:id>/delete/', views.DeleteTeacherAvailabilityAPIView.as_view(), name='availability_delete'),
    
    # ========== Teaching Subjects (کلاس‌ها) ==========
    path('teaching-subjects/', views.TeachingSubjectListAPIView.as_view(), name='teaching_subject_list'),
    path('teaching-subjects/create/', views.TeachingSubjectCreateAPIView.as_view(), name='teaching_subject_create'),
    path('teaching-subjects/<int:id>/', views.TeachingSubjectRetrieveAPIView.as_view(), name='teaching_subject_retrieve'),
    path('teaching-subjects/<int:id>/update/', views.TeachingSubjectUpdateAPIView.as_view(), name='teaching_subject_update'),
    path('teaching-subjects/<int:id>/delete/', views.TeachingSubjectDeleteAPIView.as_view(), name='teaching_subject_delete'),
    
    # ========== Exercise APIs (آزمون‌ها) ==========
    path('exercise/field/create/', views.CreateFieldAPIView.as_view(), name='field_create'),
    path('exercise/exam/create/', views.CreateExamAPIView.as_view(), name='exam_create'),
    path('exercise/exam/<int:subject_id>/', views.GetExamAPIView.as_view(), name='exam_get'),
    path('exercise/exam/<int:subject_id>/submit/', views.SubmitExamAPIView.as_view(), name='exam_submit'),
    path('exercise/results/', views.GetExamResultsAPIView.as_view(), name='exam_results_list'),
    path('exercise/results/<int:attempt_id>/', views.GetExamAttemptDetailAPIView.as_view(), name='exam_results_detail'),
    
    # ========== Chat APIs ==========
    path('chat/<int:chat_room_id>/', views.GetChatHistoryAPIView.as_view(), name='chat_history'),
    path('chat/<int:chat_room_id>/send/', views.SendMessageAPIView.as_view(), name='send_message'),
    path('chat/message/<int:message_id>/react/', views.AddReactionAPIView.as_view(), name='add_reaction'),
    path('chat/<int:chat_room_id>/participants/', views.ListParticipantsAPIView.as_view(), name='list_participants'),
]
