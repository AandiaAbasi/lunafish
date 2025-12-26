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
]
