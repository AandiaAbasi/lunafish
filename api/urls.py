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
    path('user/', views.FetchUserAPIView.as_view(), name='user'),
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
    path('teacher/availability/<int:id>/', views.TeacherAvailabilityDetailAPIView.as_view(), name='availability_detail'),
    path('teacher/availability/<int:id>/update/', views.UpdateTeacherAvailabilityAPIView.as_view(), name='availability_update'),
    path('teacher/availability/<int:id>/delete/', views.DeleteTeacherAvailabilityAPIView.as_view(), name='availability_delete'),
    
    # ========== Class Booking (خرید کلاس) ==========
    path('class-booking/create/', views.CreateClassBookingAPIView.as_view(), name='class_booking_create'),
    path('my-bookings/', views.StudentBookingsListAPIView.as_view(), name='student_bookings_list'),
    path('teacher/bookings/', views.TeacherBookingsListAPIView.as_view(), name='teacher_bookings_list'),
    path('class-booking/<int:id>/status/', views.UpdateBookingStatusAPIView.as_view(), name='booking_status_update'),
    path('class-booking/<int:id>/cancel/', views.CancelBookingAPIView.as_view(), name='booking_cancel'),
    
    # ========== Payment APIs ==========
    path('class-booking/<int:booking_id>/initiate-payment/', views.InitiatePaymentAPIView.as_view(), name='initiate_payment'),
    path('payment/callback/', views.PaymentCallbackAPIView.as_view(), name='payment_callback'),
    path('payment/redirect/', views.PaymentRedirectAPIView.as_view(), name='payment_redirect'),
    path('class-booking/<int:booking_id>/payment-status/', views.PaymentStatusAPIView.as_view(), name='payment_status'),
    
    # ========== Teaching Subjects (کلاس‌ها) ==========
    path('teaching-subjects/', views.TeachingSubjectListAPIView.as_view(), name='teaching_subject_list'),
    path('teaching-subjects/create/', views.TeachingSubjectCreateAPIView.as_view(), name='teaching_subject_create'),
    path('teaching-subjects/<int:id>/', views.TeachingSubjectRetrieveAPIView.as_view(), name='teaching_subject_retrieve'),
    path('teaching-subjects/<int:id>/update/', views.TeachingSubjectUpdateAPIView.as_view(), name='teaching_subject_update'),
    path('teaching-subjects/<int:id>/delete/', views.TeachingSubjectDeleteAPIView.as_view(), name='teaching_subject_delete'),
    
    # ========== Teacher Discovery APIs ==========
    path('teachers/', views.TeacherListAPIView.as_view(), name='teacher_list'),
    path('teachers/<int:id>/', views.TeacherDetailAPIView.as_view(), name='teacher_detail'),
    
    # ========== Teacher's Students & Classes APIs ==========
    path('teacher/dashboard/', views.TeacherDashboardAPIView.as_view(), name='teacher_dashboard'),
    path('teacher/students/', views.TeacherStudentsListAPIView.as_view(), name='teacher_students_list'),
    path('teacher/student/<int:student_id>/profile/', views.StudentProfileDetailAPIView.as_view(), name='student_profile_detail'),
    path('teacher/student/<int:student_id>/paid-classes/', views.StudentPaidClassesListAPIView.as_view(), name='student_paid_classes'),
    path('teacher/student/<int:student_id>/exercises/', views.StudentExercisesListAPIView.as_view(), name='student_exercises'),
    
    # ========== Parent Portal APIs ==========
    path('parent/login/', views.ParentLoginAPIView.as_view(), name='parent_login'),
    path('parent/dashboard/', views.ParentDashboardAPIView.as_view(), name='parent_dashboard'),
    path('parent/child-class-history/', views.ChildClassHistoryAPIView.as_view(), name='child_class_history'),
    path('parent/child-payment-history/', views.ChildPaymentHistoryAPIView.as_view(), name='child_payment_history'),
    path('parent/payment-summary/', views.ChildPaymentSummaryAPIView.as_view(), name='payment_summary'),
    path('parent/update-usage-time/', views.ParentUpdateUsageTimeAPIView.as_view(), name='update_usage_time'),
    path('parent/profile/', views.ParentProfileAPIView.as_view(), name='parent_profile'),
    path('parent/change-password/', views.ParentChangePasswordAPIView.as_view(), name='parent_change_password'),
    
    # ========== Parental Control - Usage Tracking APIs ==========
    path('parental/limits/', views.ParentalLimitsAPIView.as_view(), name='parental_limits'),
    path('parental/usage/report/', views.ParentalUsageReportAPIView.as_view(), name='parental_usage_report'),
    
    # ========== Attendance APIs ==========
    path('attendance/<int:booking_id>/', views.AttendanceAPIView.as_view(), name='attendance'),
    path('attendance/<int:booking_id>/list/', views.AttendanceListAPIView.as_view(), name='attendance_list'),
    path('attendance/list/', views.AttendanceGeneralListAPIView.as_view(), name='attendance_general_list'),
    
    # ========== Financial System APIs ==========
    # Wallet endpoints
    path('wallet/', views.TeacherWalletDetailAPIView.as_view(), name='teacher_wallet'),
    path('wallet/update-bank-info/', views.UpdateBankInformationAPIView.as_view(), name='update_bank_info'),
    
    # Withdrawal request endpoints
    path('withdrawal-requests/', views.WithdrawalRequestListAPIView.as_view(), name='withdrawal_requests_list'),
    path('withdrawal-requests/create/', views.WithdrawalRequestCreateAPIView.as_view(), name='withdrawal_request_create'),
    path('withdrawal-requests/<int:request_id>/approve/', views.WithdrawalApproveAPIView.as_view(), name='withdrawal_request_approve'),
    
    # Transaction endpoints
    path('transactions/', views.WalletTransactionListAPIView.as_view(), name='wallet_transactions'),
    path('student-transactions/', views.StudentTransactionListAPIView.as_view(), name='student_transactions'),
    
    # Financial summary endpoint
    path('financial-summary/', views.FinancialSummaryAPIView.as_view(), name='financial_summary'),
    
    # ========== Exercise APIs (آزمون‌ها) ==========
    # TWO-STEP Field Creation
    path('exercise/field/create/', views.CreateFieldAPIView.as_view(), name='field_create_step1'),  # Step 1: Create Field (multipart)
    path('exercise/field/<int:field_id>/details/', views.CreateFieldDetailsAPIView.as_view(), name='field_create_details_step2'),  # Step 2: Add Details (JSON)
    path('exercise/field/<int:field_id>/', views.GetFieldDetailAPIView.as_view(), name='field_detail'),  # Get Field with Details
    path('exercise/field/<int:field_id>/update/', views.UpdateFieldAPIView.as_view(), name='field_update'),  # Update Field
    path('exercise/field/<int:field_id>/delete/', views.DeleteFieldAPIView.as_view(), name='field_delete'),  # Delete Field
    path('exercise/field/detail/<int:detail_id>/update/', views.UpdateFieldDetailAPIView.as_view(), name='field_detail_update'),  # Update Field Detail
    
    # Other Exercise APIs
    path('exercise/fields/teacher/', views.TeacherFieldListAPIView.as_view(), name='teacher_fields_list'),
    path('exercise/exam/create/', views.CreateExamAPIView.as_view(), name='exam_create'),
    path('exercise/exam/<int:subject_id>/', views.GetExamAPIView.as_view(), name='exam_get'),
    path('exercise/exam/<int:subject_id>/steps/', views.GetExamByStepsAPIView.as_view(), name='exam_get_by_steps'),
    path('exercise/exam/<int:subject_id>/step/<int:step>/delete/', views.DeleteExamStepAPIView.as_view(), name='exam_step_delete'),
    path('exercise/exam/question/<int:question_id>/delete/', views.DeleteExamQuestionAPIView.as_view(), name='exam_question_delete'),
    path('exercise/exam/<int:subject_id>/submit/', views.SubmitExamAPIView.as_view(), name='exam_submit'),
    
    # Student Exercise APIs
    path('student/exercises/', views.StudentSubjectsWithExercisesAPIView.as_view(), name='student_subjects_with_exercises'),
    path('student/exercises/<int:subject_id>/steps/', views.StudentExamByStepsAPIView.as_view(), name='student_exam_by_steps'),
    path('student/exercises/<int:subject_id>/save-answer/', views.StudentSaveAnswerAPIView.as_view(), name='student_save_answer'),
    
    path('exercise/results/', views.GetExamResultsAPIView.as_view(), name='exam_results_list'),
    path('exercise/results/<int:attempt_id>/', views.GetExamAttemptDetailAPIView.as_view(), name='exam_results_detail'),
    
    # ========== Student Rating & Medal APIs ==========
    path('rating/student/', views.GiveStudentRatingAPIView.as_view(), name='give_student_rating'),
    path('rating/student/<int:rating_id>/', views.UpdateStudentRatingAPIView.as_view(), name='update_student_rating'),
    path('medal/student/', views.GiveStudentMedalAPIView.as_view(), name='give_student_medal'),
    path('medal/student/<int:medal_id>/', views.DeleteStudentMedalAPIView.as_view(), name='delete_student_medal'),
    path('student/<int:student_id>/rating-profile/', views.StudentProfileRatingAPIView.as_view(), name='student_rating_profile'),
    path('exercise/<int:exercise_id>/rating/', views.ExerciseRatingDetailAPIView.as_view(), name='exercise_rating_detail'),
    
    # ========== Teacher Rating APIs ==========
    path('rating/teacher/', views.GiveTeacherRatingAPIView.as_view(), name='give_teacher_rating'),
    path('teacher/<int:teacher_id>/rating-profile/', views.TeacherProfileRatingAPIView.as_view(), name='teacher_rating_profile'),
    path('teacher/<int:teacher_id>/ratings/', views.TeacherRatingsListAPIView.as_view(), name='teacher_ratings_list'),
    path('my-rating/teacher/<int:teacher_id>/', views.MyTeacherRatingAPIView.as_view(), name='my_teacher_rating'),
    
    # ========== Support Message APIs (پیام‌های پشتیبانی) ==========
    path('support-messages/', views.SupportMessageAPIView.as_view(), name='support_messages'),
    path('support-messages/<int:message_id>/', views.SupportMessageDetailAPIView.as_view(), name='support_message_detail'),
    path('teacher-conversations/', views.TeacherConversationsAPIView.as_view(), name='teacher_conversations'),
    path('teacher-conversations/<int:teacher_id>/', views.TeacherConversationDetailAPIView.as_view(), name='teacher_conversation_detail'),
    
    # ========== Package & Installment Payment APIs (فصل ۲۹) ==========
    path('packages/', views.PackageListAPIView.as_view(), name='package_list'),
    path('student/enrollments/', views.StudentEnrollmentListAPIView.as_view(), name='student_enrollments'),
    path('packages/check-session-access/', views.CheckSessionAccessAPIView.as_view(), name='check_session_access'),
    path('packages/process-payment/', views.ProcessPackagePaymentAPIView.as_view(), name='process_package_payment'),
    path('packages/verify-payment/', views.VerifyPackagePaymentAPIView.as_view(), name='verify_package_payment'),
    
    # ========== Teacher Package Management APIs ==========
    path('teacher/packages/', views.TeacherPackageListCreateAPIView.as_view(), name='teacher_package_list_create'),
    path('teacher/packages/<int:package_id>/', views.TeacherPackageDetailAPIView.as_view(), name='teacher_package_detail'),
    path('teacher/packages/<int:package_id>/installments/', views.TeacherPackageInstallmentListCreateAPIView.as_view(), name='teacher_installment_list_create'),
    path('teacher/packages/<int:package_id>/installments/<int:installment_id>/', views.TeacherPackageInstallmentDetailAPIView.as_view(), name='teacher_installment_detail'),
    
    path('teacher/courses/', views.TeacherCourseListCreateView.as_view()),
    path('teacher/courses/<int:pk>/', views.TeacherCourseDetailView.as_view()),
    
    path('courses/', views.CourseListView.as_view()),
    path('courses/<int:pk>/', views.CourseDetailView.as_view()),
    path('courses/<int:course_id>/enroll/', views.EnrollCourseView.as_view()),
    path('courses/payment/callback/', views.CoursePaymentCallbackAPIView.as_view(), name='course_payment_callback'),
    path('courses/payment/redirect/', views.CoursePaymentRedirectView.as_view(), name='course_payment_redirect'),
    path('enrollments/<int:enrollment_id>/confirm/', views.ConfirmEnrollmentPaymentView.as_view()),
    path('enrollments/', views.StudentEnrollmentListView.as_view()),
    path('enrollments/<int:pk>/', views.StudentEnrollmentDetailView.as_view(), name='student-enrollment-detail'),
    path('courses/teacher/', views.TeacherEnrollmentListView.as_view(), name='teacher-course-list'),
    path('courses/teacher/<int:pk>/', views.TeacherEnrollmentDetailView.as_view(), name='teacher-course-detail'),
    path('teacher/assign-time/', views.AssignTimeToEnrollmentView.as_view(), name='assign-time-to-enrollment'),
    
    # ========== Internal RTC Events Endpoint ==========
    path('internal/rtc-events/', views.InternalRTCEventAPIView.as_view(), name='internal_rtc_events'),
]
