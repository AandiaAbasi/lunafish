"""
Parent Portal - Sample Implementation & Testing
والدین می‌توانند با student_id یا شماره تماس یا ایمیل + parent_password وارد شوند
"""

# ===== Example 1: Create Parent Profile =====
# python manage.py shell

from account.models import ParentProfile, User
from django.utils import timezone

# دانش‌آموز را پیدا کنید
student = User.objects.get(id=5, role='user')

# والد را ایجاد کنید
parent = ParentProfile.objects.create(
    student=student,
    parent_name="محمد علی احمدی",
    phone="09123456789",
    email="parent@example.com",
    can_view_class_history=True,
    can_view_payments=True,
    can_select_teacher=False,
    can_set_usage_time=True,
    daily_usage_limit_minutes=120,  # 2 ساعت روزانه
    allowed_start_time="08:00",      # از 8 صبح
    allowed_end_time="22:00",        # تا 10 شب
    is_active=True
)

# رمز والد را تنظیم کنید
parent.set_password("SecurePassword123!")
parent.save()

print(f"Parent created: {parent.parent_name}")
print(f"Student: {parent.student.name or parent.student.username}")
print(f"Parent ID: {parent.id}")


# ===== Example 2: Verify Parent Password =====

# والد را پیدا کنید
parent = ParentProfile.objects.get(id=3)

# رمز را بررسی کنید
if parent.verify_password("SecurePassword123!"):
    print("Password is correct!")
else:
    print("Password is incorrect!")


# ===== Example 3: Update Parent Permissions =====

parent = ParentProfile.objects.get(id=3)

# مجوزها را به‌روزرسانی کنید
parent.can_select_teacher = True
parent.can_view_payments = True
parent.save()

print(f"Permissions updated for {parent.parent_name}")


# ===== Example 4: Update Usage Time =====

parent = ParentProfile.objects.get(id=3)

from datetime import time

# محدودیت‌های زمانی را تعیین کنید
parent.daily_usage_limit_minutes = 90  # 1.5 ساعت
parent.allowed_start_time = time(14, 0)  # 2 بعدازظهر
parent.allowed_end_time = time(21, 0)    # 9 شب
parent.save()

print(f"Usage time updated:")
print(f"  Daily limit: {parent.daily_usage_limit_minutes} minutes")
print(f"  Allowed time: {parent.allowed_start_time} - {parent.allowed_end_time}")


# ===== Example 5: Get All Parents of a Student =====

student = User.objects.get(id=5)
parents = student.parents.filter(is_active=True)

print(f"Student {student.name} has {parents.count()} active parents:")
for parent in parents:
    print(f"  - {parent.parent_name} ({parent.phone})")


# ===== Example 6: Track Parent Login =====

parent = ParentProfile.objects.get(id=3)
parent.last_login_at = timezone.now()
parent.save()

print(f"Parent {parent.parent_name} logged in at {parent.last_login_at}")


# ===== Example 7: Create Usage Log =====

from account.models import ParentAppUsageLog
from datetime import date

parent = ParentProfile.objects.get(id=3)

log, created = ParentAppUsageLog.objects.get_or_create(
    parent=parent,
    date=date.today(),
    defaults={
        'total_minutes': 45,
        'session_count': 3
    }
)

if created:
    print(f"New usage log created: {log.total_minutes} minutes")
else:
    print(f"Usage log already exists: {log.total_minutes} minutes")


# ===== Example 8: Get Parent Dashboard Stats =====

from classroom.models import ClassBooking, StudentTransaction
from django.db.models import Sum, Count, Q

parent = ParentProfile.objects.get(id=3)
student = parent.student

# کلاس‌ها
total_classes = ClassBooking.objects.filter(student=student).count()
completed = ClassBooking.objects.filter(student=student, status='completed').count()
cancelled = ClassBooking.objects.filter(student=student, status='cancelled').count()
upcoming = ClassBooking.objects.filter(
    student=student,
    status='reserved',
    availability__is_expired=False
).count()

# پرداخت‌ها
total_spent = StudentTransaction.objects.filter(
    student=student,
    status='completed'
).aggregate(Sum('amount'))['amount__sum'] or 0

pending = StudentTransaction.objects.filter(
    student=student,
    status='pending'
).aggregate(Sum('amount'))['amount__sum'] or 0

print(f"\nDashboard for {parent.parent_name}:")
print(f"  Child: {student.name or student.username}")
print(f"  Total Classes: {total_classes}")
print(f"  Completed: {completed} | Cancelled: {cancelled} | Upcoming: {upcoming}")
print(f"  Total Spent: {total_spent:,}")
print(f"  Pending: {pending:,}")


# ===== Example 9: Get Class History =====

parent = ParentProfile.objects.get(id=3)
classes = ClassBooking.objects.filter(
    student=parent.student
).select_related('teacher', 'subject', 'availability').order_by('-created_at')[:5]

print(f"\nRecent Classes for {parent.parent_name}:")
for cls in classes:
    print(f"  - {cls.subject.title}")
    print(f"    Teacher: {cls.teacher.name}")
    print(f"    Date: {cls.availability.date}")
    print(f"    Status: {cls.status}")
    print(f"    Price: {cls.final_price:,}")
    print()


# ===== Example 10: Get Payment History =====

parent = ParentProfile.objects.get(id=3)
transactions = StudentTransaction.objects.filter(
    student=parent.student
).select_related('booking').order_by('-payment_date')[:5]

print(f"\nPayment History for {parent.parent_name}:")
for trans in transactions:
    print(f"  - {trans.get_transaction_type_display()}: {trans.amount:,}")
    print(f"    Status: {trans.status}")
    print(f"    Date: {trans.payment_date}")
    if trans.booking:
        print(f"    Class: {trans.booking.subject.title}")
    print()


# ===== API Testing with cURL =====
"""
# 1. Parent Login (with student ID)
curl -X POST http://localhost:8000/api/parent/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "5",
    "parent_password": "SecurePassword123!"
  }'

# 1b. Parent Login (with phone number)
curl -X POST http://localhost:8000/api/parent/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "09123456789",
    "parent_password": "SecurePassword123!"
  }'

# 1c. Parent Login (with email)
curl -X POST http://localhost:8000/api/parent/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "parent@example.com",
    "parent_password": "SecurePassword123!"
  }'

# 2. Parent Dashboard
curl -X GET "http://localhost:8000/api/parent/dashboard/?child_id=5" \
  -H "Authorization: Bearer <token>"

# 3. Child Class History
curl -X GET "http://localhost:8000/api/parent/child-class-history/?child_id=5" \
  -H "Authorization: Bearer <token>"

# 4. Child Payment History
curl -X GET "http://localhost:8000/api/parent/child-payment-history/?child_id=5" \
  -H "Authorization: Bearer <token>"

# 5. Payment Summary
curl -X GET "http://localhost:8000/api/parent/payment-summary/?child_id=5" \
  -H "Authorization: Bearer <token>"

# 6. Update Usage Time
curl -X POST http://localhost:8000/api/parent/update-usage-time/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "child_id": 5,
    "daily_usage_limit_minutes": 60,
    "allowed_start_time": "14:00",
    "allowed_end_time": "21:00"
  }'

# 7. Parent Profile
curl -X GET "http://localhost:8000/api/parent/profile/?child_id=5" \
  -H "Authorization: Bearer <token>"
"""


# ===== Django Admin Management =====
"""
1. Open Django Admin: http://localhost:8000/admin/
2. Navigate to: Account > Parent Profiles
3. Actions:
   - Add Parent: Click "Add Parent Profile" button
   - Edit Parent: Click on parent name
   - Delete Parent: Select parent and choose delete action
   - Filter: Use filters on the right side
   - Search: Use search box to find parents

4. Bulk Actions:
   - Select multiple parents
   - Choose action from dropdown
   - Click "Go"
"""


# ===== Troubleshooting =====
"""
Problem: "Student not found"
Solution: Make sure student_id is correct and student has role='user'

Problem: "Parent profile not found"
Solution: Create parent profile first using Example 1

Problem: "Invalid password"
Solution: Make sure you're using parent_password, not student password

Problem: "Permission denied"
Solution: Check if parent has required permissions (can_view_class_history, etc.)

Problem: Migration failed
Solution: Run: python manage.py makemigrations account
         Then: python manage.py migrate account
"""
