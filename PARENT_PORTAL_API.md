# Parent Portal APIs - درگاه والدین

## Overview

والدین می‌توانند با `شناسه دانش‌آموز` یا `شماره تماس` یا `ایمیل` + `parent_password` وارد شوند و:
1. **تاریخچه کلاس‌های کودک** را ببینند
2. **ریز پرداخت‌های کودک** را مشاهده کنند  
3. **معلم برای کودک انتخاب** کنند (اگر مجوز داشته باشند)
4. **زمان مجاز استفاده اپلیکیشن** توسط کودک را تعیین کنند

## Models

### 1. ParentProfile
والد مرتبط با یک دانش‌آموز (هر دانش‌آموز می‌تواند چند والد داشته باشد)

**Fields:**
- `student`: ForeignKey → User (role='user')
- `parent_name`: نام کامل والد
- `phone`: شماره تماس
- `email`: ایمیل
- `parent_password_hash`: رمز والد (هش‌شده)

**Permissions:**
- `can_view_class_history`: مشاهده تاریخچه کلاس‌ها (default: True)
- `can_view_payments`: مشاهده پرداخت‌ها (default: True)
- `can_select_teacher`: انتخاب معلم برای کودک (default: False)
- `can_set_usage_time`: تنظیم محدودیت زمان (default: True)

**Usage Time Fields:**
- `daily_usage_limit_minutes`: حداکثر دقایق روزانه (اختیاری)
- `allowed_start_time`: شروع بازه مجاز استفاده (اختیاری، مثال: 08:00)
- `allowed_end_time`: پایان بازه مجاز استفاده (اختیاری، مثال: 22:00)

**Status:**
- `is_active`: دسترسی فعال/غیرفعال
- `last_login_at`: آخرین ورود

### 2. ParentAppUsageLog
ثبت استفاده روزانه کودک از اپلیکیشن (برای کنترل والد)

**Fields:**
- `parent`: ForeignKey → ParentProfile
- `date`: تاریخ
- `total_minutes`: کل دقایق استفاده
- `session_count`: تعداد جلسات

---

## API Endpoints

### 1. Parent Login
**`POST /api/parent/login/`**

والدین برای ورود می‌توانند از شناسه دانش‌آموز، شماره تماس یا ایمیل استفاده کنند.

**Request (با شناسه دانش‌آموز):**
```json
{
  "identifier": "5",
  "parent_password": "password123"
}
```

**Request (با شماره تماس):**
```json
{
  "identifier": "09123456789",
  "parent_password": "password123"
}
```

**Request (با ایمیل):**
```json
{
  "identifier": "parent@email.com",
  "parent_password": "password123"
}
```

**Response (200 OK):** (شناسه، شماره تماس یا ایمیل درست نیست)
- 400: No parent profile found
- 400: Invalid password (رمز والد درست نیست)
  "parent_token": "abc123xyz...",
  "parent_id": 3,
  "parent_name": "محمد علی احمدی",
  "student_id": 5,
  "student_name": "فاطمه احمدی",
  "can_view_class_history": true,
  "can_view_payments": true,
  "can_select_teacher": false,
  "can_set_usage_time": true
}
```

**Errors:**
- 400: Student not found
- 400: No parent profile found
- 400: Invalid password

---

### 2. Parent Dashboard
**`GET /api/parent/dashboard/`**

خلاصه‌ای از وضعیت کودک

**Query Parameters:**
- `child_id` (optional): شناسه کودک (اگر والد بیش از یک فرزند داشته باشد)

**Response (200 OK):**
```json
{
  "child": {
    "id": 5,
    "name": "فاطمه احمدی",
    "username": "fatemeh_ahmadi",
    "birth_date": "1404-06-15",
    "gender": "female",
    "bio": "دانش‌آموز کلاس دوم دبستان",
    "profile_photo_path": "/media/avatars/...",
    "selected_avatar_image": "/media/avatars/..."
  },
  "total_classes": 12,
  "completed_classes": 8,
  "cancelled_classes": 1,
  "no_show_classes": 0,
  "upcoming_classes": 3,
  "total_spent": "2450000",
  "total_pending_payment": "0"
}
```

---

### 3. Child Class History
**`GET /api/parent/child-class-history/`**

تاریخچه کلاس‌های کودک

**Query Parameters:**
- `child_id` (required): شناسه کودک
- `status` (optional): `reserved`, `completed`, `cancelled`, `no_show`
- `ordering` (optional): default: `-created_at` (جدیدترین‌ها اول)

**Response (200 OK):**
```json
{
  "count": 12,
  "next": "http://...",
  "previous": null,
  "results": [
    {
      "id": 45,
      "class_date": "1403/12/25",
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "teacher_name": "مریم علیزاده",
      "teacher_id": 2,
      "subject_title": "انگلیسی مبتدی - حروف",
      "subject_id": 3,
      "status": "completed",
      "price": "150000",
      "discount_amount": "0",
      "final_price": "150000"
    },
    ...
  ]
}
```

**Status Values:**
- `reserved`: رزرو شده (آینده)
- `completed`: تکمیل شده
- `cancelled`: لغو شده
- `no_show`: حاضر نشد

---

### 4. Child Payment History
**`GET /api/parent/child-payment-history/`**

ریز پرداخت‌های کودک

**Query Parameters:**
- `child_id` (required): شناسه کودک
- `transaction_type` (optional): `class_payment`, `refund`
- `status` (optional): `pending`, `completed`, `failed`, `refunded`
- `ordering` (optional): default: `-created_at`

**Response (200 OK):**
```json
{
  "count": 8,
  "results": [
    {
      "id": 32,
      "transaction_type": "class_payment",
      "amount": "150000",
      "booking_id": 45,
      "class_title": "انگلیسی مبتدی - حروف",
      "teacher_name": "مریم علیزاده",
      "description": "پرداخت برای کلاس انگلیسی",
      "status": "completed",
      "payment_date": "2024-12-25T09:00:00Z"
    },
    ...
  ]
}
```

---

### 5. Payment Summary
**`GET /api/parent/payment-summary/`**

خلاصه وضعیت مالی کودک

**Query Parameters:**
- `child_id` (required): شناسه کودک

**Response (200 OK):**
```json
{
  "total_paid": "2450000",
  "total_pending": "0",
  "total_refunded": "0",
  "total_failed": "0",
  "transaction_count": 8
}
```

---

### 6. Update App Usage Time
**`POST /api/parent/update-usage-time/`**

تنظیم محدودیت زمان استفاده کودک

**Request:**
```json
{
  "child_id": 5,
  "daily_usage_limit_minutes": 120,
  "allowed_start_time": "08:00",
  "allowed_end_time": "22:00"
}
```

**Response (200 OK):**
```json
{
  "id": 3,
  "parent_name": "محمد علی احمدی",
  "student_id": 5,
  "daily_usage_limit_minutes": 120,
  "allowed_start_time": "08:00:00",
  "allowed_end_time": "22:00:00"
}
```

**Validation Rules:**
- `daily_usage_limit_minutes`: 0-1440 (min، 0 = بدون محدودیت)
- `allowed_end_time` > `allowed_start_time`

**Errors:**
- 400: Invalid time range
- 403: Permission denied (والد مجوز تنظیم زمان ندارد)

---

### 7. Parent Profile
**`GET /api/parent/profile/`**

نمایش اطلاعات والد

**Query Parameters:**
- `child_id` (required): شناسه کودک

**Response (200 OK):**
```json
{
  "id": 3,
  "student_id": 5,
  "student_name": "فاطمه احمدی",
  "child_full_name": "fatemeh_ahmadi",
  "parent_name": "محمد علی احمدی",
  "phone": "09123456789",
  "email": "parent@example.com",
  "can_view_class_history": true,
  "can_view_payments": true,
  "can_select_teacher": false,
  "can_set_usage_time": true,
  "is_active": true,
  "last_login_at": "2024-12-25T10:30:00Z"
}
```

---

## Implementation Details

### 1. Parent Password Hashing
```python
# Password hashing (in model)
from django.contrib.auth.hashers import make_password, check_password

parent = ParentProfile(student=student, parent_name="...")
parent.set_password("password123")  # Hashes password
parent.save()

# Verification
if parent.verify_password("password123"):
    # Correct password
    pass
```

### 2. Parent Login Flow
1. والد `identifier` (شناسه دانش‌آموز یا شماره تماس یا ایمیل) + `parent_password` را ارسال می‌کند
2. سرور User را بر اساس identifier پیدا می‌کند:
   - اگر تمام رقم باشد: به عنوان شناسه جستجو کن
   - اگر ایمیل باشد: به عنوان ایمیل جستجو کن
   - وگرنه: به عنوان شماره تماس جستجو کن
3. سرور ParentProfile را پیدا می‌کند
4. رمز را بررسی می‌کند
5. `last_login_at` را به‌روزرسانی می‌کند
6. Token برای والد صادر می‌کند

### 3. Permission Control
هر والد می‌تواند مجوزهای مختلفی داشته باشد:
```python
if parent.can_view_class_history:
    # Show classes
    
if parent.can_select_teacher:
    # Allow teacher selection
    
if parent.can_set_usage_time:
    # Allow usage time control
```

### 4. Usage Time Control
- `daily_usage_limit_minutes`: کل دقایق در روز
- `allowed_start_time`: شروع بازه (مثال: 08:00)
- `allowed_end_time`: پایان بازه (مثال: 22:00)

**Example:**
```json
{
  "daily_usage_limit_minutes": 90,
  "allowed_start_time": "14:00",
  "allowed_end_time": "21:00"
}
```
معنی: کودک فقط بین ساعت 14:00 تا 21:00 می‌تواند اپلیکیشن را بازکند و حداکثر 90 دقیقه استفاده کند.

---

## Django Admin Integration

### Parent Profiles List
- Search by: parent name, phone, email, student name
- Filter by: is_active, permissions, created_at
- Inline display for student's parents

### Usage Logs
- View by date hierarchy
- Filter by parent or date range
- Read-only (auto-generated from user activity)

---

## Example Usage Flow

### 1. Parent Registration (by Admin or Student)
```python
from account.models import ParentProfile, User

student = User.objects.get(id=5)
parent = ParentProfile.objects.create(
    student=student,
    parent_name="محمد علی احمدی",
    phone="09123456789",
    email="parent@example.com",
    can_view_class_history=True,
    can_view_payments=True,
    can_select_teacher=False,
    can_set_usage_time=True,
    daily_usage_limit_minutes=120,
    allowed_start_time="08:00",
    allowed_end_time="22:00",
    is_active=True
)
parent.set_password("securepassword123")
parent.save()
```

### 2. Parent Login
```bash
POST /api/parent/login/
{
  "student_id": 5,
  "parent_password": "securepassword123"
}
```

### 3. View Dashboard
```bash
GET /api/parent/dashboard/?child_id=5
```

### 4. View Class History
```bash
GET /api/parent/child-class-history/?child_id=5&status=completed
```

### 5. View Payments
```bash
GET /api/parent/child-payment-history/?child_id=5
```

### 6. Update Usage Time
```bash
POST /api/parent/update-usage-time/
{
  "child_id": 5,
  "daily_usage_limit_minutes": 90
}
```

---

## Security Considerations

1. **Password Security:**
   - Passwords are hashed using Django's `make_password()`
   - Verified using `check_password()`
   - Never stored in plain text

2. **Authentication:**
   - Parent login is separate from student/teacher login
   - Parent token is managed independently
   - Last login is tracked for security audits

3. **Permissions:**
   - Each parent has granular permissions
   - Admins can grant/revoke permissions per parent
   - Only parents with `can_view_class_history` can see classes

4. **Data Access:**
   - Parents can only view their own child's data
   - Admin can view all parent profiles
   - Logs are immutable and auto-generated

---

## Migration

To create migration for ParentProfile and ParentAppUsageLog:

```bash
python manage.py makemigrations account
python manage.py migrate account
```

This will create:
- `parent_profiles` table
- `parent_app_usage_logs` table
- Proper indexes and constraints
