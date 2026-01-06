"""
مثال‌های استفاده از API‌های قسط‌بندی و دسترسی به جلسات

این فایل شامل:
1. نمایش استفاده از API endpoint‌ها
2. مثال‌های عملی برای توابع service
3. تست‌های دستی
"""

# ============================================
# 1. ایجاد پکیج با قسط‌بندی
# ============================================

"""
POST /api/packages/
Content-Type: application/json

{
    "title": "انگلیسی مبتدی - 30 جلسه",
    "description": "دوره جامع یادگیری انگلیسی برای مبتدیان",
    "total_sessions": 30,
    "total_price": 600000,
    "subjects": [1]  # ID موضوع
}

Response:
{
    "id": 1,
    "title": "انگلیسی مبتدی - 30 جلسه",
    "total_sessions": 30,
    "total_price": "600000.00",
    "has_installment": false,
    "installments": []
}
"""


# ============================================
# 2. اضافه کردن اقساط به پکیج
# ============================================

"""
POST /api/packages/1/installments/
Content-Type: application/json

[
    {
        "installment_number": 1,
        "amount": 200000,
        "session_number": 1,
        "description": "قسط اول - قبل از جلسه اول"
    },
    {
        "installment_number": 2,
        "amount": 200000,
        "session_number": 10,
        "description": "قسط دوم - قبل از جلسه دهم"
    },
    {
        "installment_number": 3,
        "amount": 200000,
        "session_number": 20,
        "description": "قسط سوم - قبل از جلسه بیستم"
    }
]
"""


# ============================================
# 3. بررسی صحت مجموع اقساط
# ============================================

"""
POST /api/packages/1/validate_installments/

Response:
{
    "is_valid": true,
    "message": "مجموع اقساط صحیح است",
    "total_price": "600000.00",
    "total_installments": 600000
}
"""


# ============================================
# 4. ثبت‌نام دانش‌آموز به پکیج
# ============================================

"""
POST /api/enrollments/
Content-Type: application/json

{
    "package": 1  # ID پکیج
}

Response:
{
    "id": 1,
    "student_name": "علی رضائی",
    "package": {...},
    "enrollment_date": "2026-01-06T10:30:00Z",
    "status": "active",
    "completed_sessions_count": 0,
    "payment_summary": {
        "total_amount": "600000.00",
        "paid_amount": "0.00",
        "remaining_amount": "600000.00",
        "total_installments": 3,
        "paid_installments": 0,
        "pending_installments": 3,
        "completion_percentage": 0
    },
    "next_due_installment": {
        "installment_number": 1,
        "amount": "200000.00",
        "session_number": 1,
        "remaining_amount": "200000.00"
    },
    "installment_payments": [
        {
            "id": 1,
            "installment": {
                "id": 1,
                "installment_number": 1,
                "amount": "200000.00",
                "session_number": 1
            },
            "amount_due": "200000.00",
            "amount_paid": "0.00",
            "payment_status": "pending",
            "remaining_amount": "200000.00",
            "is_fully_paid": false
        },
        ...
    ]
}
"""


# ============================================
# 5. پردازش پرداخت قسط
# ============================================

"""
POST /api/enrollments/1/process-payment/
Content-Type: application/json

{
    "installment_id": 1,
    "amount_paid": 200000,
    "payment_ref": "ref_gatewayy_123456"
}

Response:
{
    "success": true,
    "message": "پرداخت با موفقیت ثبت شد",
    "payment": {
        "id": 1,
        "installment": {...},
        "amount_due": "200000.00",
        "amount_paid": "200000.00",
        "payment_status": "paid",
        "payment_ref": "ref_gateway_123456",
        "first_payment_date": "2026-01-06T11:00:00Z",
        "last_payment_date": "2026-01-06T11:00:00Z",
        "completed_date": "2026-01-06T11:00:00Z",
        "is_fully_paid": true
    }
}
"""


# ============================================
# 6. بررسی دسترسی به جلسه
# ============================================

"""
POST /api/enrollments/1/check-session-access/
Content-Type: application/json

{
    "session_number": 5
}

Response (موفق):
{
    "can_access": true,
    "message": "دسترسی مجاز است",
    "session_number": 5
}

Response (ناموفق):
{
    "can_access": false,
    "message": "قسط 1 برای جلسه 1 پرداخت نشده است",
    "session_number": 5
}
"""


# ============================================
# 7. دریافت خلاصه پرداخت‌ها
# ============================================

"""
GET /api/enrollments/1/payment-summary/

Response:
{
    "total_amount": "600000.00",
    "paid_amount": "200000.00",
    "remaining_amount": "400000.00",
    "total_installments": 3,
    "paid_installments": 1,
    "pending_installments": 2,
    "completion_percentage": 33.33
}
"""


# ============================================
# 8. دریافت اقساط پرداخت‌نشده
# ============================================

"""
GET /api/enrollments/1/unpaid_installments/

Response:
[
    {
        "installment": {
            "id": 2,
            "installment_number": 2,
            "amount": "200000.00",
            "session_number": 10
        },
        "payment": {
            "id": 2,
            "installment": {...},
            "amount_due": "200000.00",
            "amount_paid": "0.00",
            "payment_status": "pending",
            "remaining_amount": "200000.00"
        }
    },
    {
        "installment": {
            "id": 3,
            "installment_number": 3,
            "amount": "200000.00",
            "session_number": 20
        },
        "payment": {
            "id": 3,
            "installment": {...},
            "amount_due": "200000.00",
            "amount_paid": "0.00",
            "payment_status": "pending",
            "remaining_amount": "200000.00"
        }
    }
]
"""


# ============================================
# 9. استفاده از Service در کد Python
# ============================================

from classroom.models import StudentPackageEnrollment
from classroom.services import PackageInstallmentService
from decimal import Decimal

# دریافت ثبت‌نام
enrollment = StudentPackageEnrollment.objects.get(id=1)

# بررسی دسترسی به جلسه
can_access, message = PackageInstallmentService.can_student_attend_session(
    enrollment, 
    session_number=5
)
print(f"دسترسی: {can_access}, پیام: {message}")

# دریافت قسط بعدی
result = PackageInstallmentService.get_next_due_installment(enrollment)
if result:
    installment, payment = result
    print(f"قسط بعدی: {installment.installment_number}, مبلغ: {payment.amount_due}")

# دریافت خلاصه پرداخت
summary = PackageInstallmentService.get_enrollment_payment_summary(enrollment)
print(f"کل: {summary['total_amount']}, پرداخت‌شده: {summary['paid_amount']}")

# پردازش پرداخت
success, msg, payment = PackageInstallmentService.process_installment_payment(
    enrollment,
    installment_id=1,
    amount_paid=Decimal('200000'),
    payment_ref='ref_123'
)
print(f"موفقیت: {success}, پیام: {msg}")


# ============================================
# 10. سناریو کامل
# ============================================

"""
سناریو:
1. معلم یک پکیج 30 جلسه‌ای با 3 قسط می‌سازد
2. دانش‌آموز برای پکیج ثبت‌نام می‌کند
3. قسط اول (برای جلسه 1) پرداخت می‌کند
4. سیستم برای جلسات 1-9 دسترسی می‌دهد
5. سایر جلسات محدود هستند

مثال کد:

from django.contrib.auth import get_user_model
from classroom.models import Package, PackageInstallment
from classroom.services import PackageInstallmentService, PackageService

User = get_user_model()

# 1. معلم پکیج می‌سازد
teacher = User.objects.get(username='teacher_ali')
installments = [
    {'installment_number': 1, 'amount': 200000, 'session_number': 1},
    {'installment_number': 2, 'amount': 200000, 'session_number': 10},
    {'installment_number': 3, 'amount': 200000, 'session_number': 20},
]
success, msg, package = PackageService.create_package_with_installments(
    teacher, 'انگلیسی', 30, 600000, installments
)

# 2. دانش‌آموز ثبت‌نام می‌کند
student = User.objects.get(username='student_sara')
enrollment = StudentPackageEnrollment.objects.create(
    student=student,
    package=package
)

# 3. قسط اول پرداخت می‌شود
success, msg, payment = PackageInstallmentService.process_installment_payment(
    enrollment, 1, 200000, 'ref_123'
)

# 4. بررسی دسترسی
can_access, msg = PackageInstallmentService.can_student_attend_session(enrollment, 5)
print(f"جلسه 5: {can_access}")  # True

# 5. بررسی دسترسی به جلسات بعدی
can_access, msg = PackageInstallmentService.can_student_attend_session(enrollment, 15)
print(f"جلسه 15: {can_access}")  # False (نیازمند قسط دوم)
"""
