# Parent Portal Implementation - خلاصه پیاده‌سازی

## ✅ پیاده‌سازی تکمیل شده

### 1. مدل‌های جدید (Models)
**فایل:** `account/models.py`

#### ParentProfile Model
```python
class ParentProfile(BaseModel):
    # ارتباط
    student = ForeignKey(User, role='user')
    parent_name = CharField(max_length=200)
    phone = CharField(max_length=20)
    email = EmailField()
    
    # امنیت (رمز هش‌شده)
    parent_password_hash = CharField(max_length=255)
    
    # مجوزها (دانه‌بندی)
    can_view_class_history = BooleanField(default=True)
    can_view_payments = BooleanField(default=True)
    can_select_teacher = BooleanField(default=False)
    can_set_usage_time = BooleanField(default=True)
    
    # محدودیت‌های زمانی
    daily_usage_limit_minutes = IntegerField(null=True, blank=True)
    allowed_start_time = TimeField(null=True, blank=True)
    allowed_end_time = TimeField(null=True, blank=True)
    
    # وضعیت
    is_active = BooleanField(default=True)
    last_login_at = DateTimeField(null=True, blank=True)
    
    # Methods
    def verify_password(raw_password) -> bool
    def set_password(raw_password) -> None
```

#### ParentAppUsageLog Model
```python
class ParentAppUsageLog(BaseModel):
    parent = ForeignKey(ParentProfile)
    date = DateField()
    total_minutes = IntegerField()
    session_count = IntegerField()
    unique_together = ('parent', 'date')
```

---

### 2. Serializers
**فایل:** `api/parent_serializers.py` (جدید)

- `ParentLoginSerializer`: ورود والد
- `ChildClassHistorySerializer`: تاریخچه کلاس‌ها
- `ChildPaymentHistorySerializer`: تاریخچه پرداخت‌ها
- `ChildPaymentSummarySerializer`: خلاصه مالی
- `ChildProfileForParentSerializer`: پروفایل کودک
- `ParentDashboardSerializer`: داشبورد والد
- `ParentProfileSerializer`: اطلاعات والد
- `ParentUpdateUsageTimeSerializer`: محدودیت‌های زمانی
- `ParentAppUsageLogSerializer`: ثبت استفاده
- `TeachingSubjectForParentSelectionSerializer`: انتخاب موضوع
- `TeacherAvailabilityForParentSelectionSerializer`: انتخاب زمان
- `ParentRegistrationSerializer`: ثبت‌نام والد

---

### 3. API Views
**فایل:** `api/views.py`

#### 1. ParentLoginAPIView
```
POST /api/parent/login/
Request: {identifier (student_id OR phone OR email), parent_password}
Response: {parent_token, parent_id, parent_name, student_id, student_name, permissions}
```

#### 2. ParentDashboardAPIView
```
GET /api/parent/dashboard/?child_id=5
Response: {
    child: {id, name, username, birth_date, gender, bio, avatars},
    total_classes, completed_classes, cancelled_classes,
    upcoming_classes, total_spent, pending_payment
}
```

#### 3. ChildClassHistoryAPIView
```
GET /api/parent/child-class-history/?child_id=5&status=completed
Response: List of classes with pagination
Fields: id, class_date, start_time, end_time, teacher, subject, status, prices
```

#### 4. ChildPaymentHistoryAPIView
```
GET /api/parent/child-payment-history/?child_id=5&status=completed
Response: List of transactions with pagination
Fields: id, type, amount, booking, class, teacher, status, date
```

#### 5. ChildPaymentSummaryAPIView
```
GET /api/parent/payment-summary/?child_id=5
Response: {
    total_paid, total_pending, total_refunded,
    total_failed, transaction_count
}
```

#### 6. ParentUpdateUsageTimeAPIView
```
POST /api/parent/update-usage-time/
Request: {child_id, daily_usage_limit_minutes, allowed_start_time, allowed_end_time}
Response: {id, parent_name, student_id, usage_limits}
```

#### 7. ParentProfileAPIView
```
GET /api/parent/profile/?child_id=5
Response: {
    id, student_id, parent_name, phone, email,
    permissions, usage_limits, is_active, last_login
}
```

---

### 4. URL Patterns
**فایل:** `api/urls.py`

```python
path('parent/login/', ParentLoginAPIView.as_view()),
path('parent/dashboard/', ParentDashboardAPIView.as_view()),
path('parent/child-class-history/', ChildClassHistoryAPIView.as_view()),
path('parent/child-payment-history/', ChildPaymentHistoryAPIView.as_view()),
path('parent/payment-summary/', ChildPaymentSummaryAPIView.as_view()),
path('parent/update-usage-time/', ParentUpdateUsageTimeAPIView.as_view()),
path('parent/profile/', ParentProfileAPIView.as_view()),
```

---

### 5. Django Admin Integration
**فایل:** `account/admin.py`

#### ParentProfileAdmin
- List display: parent_name, student_link, phone, is_active, last_login
- Filters: is_active, permissions, created_at
- Search: parent_name, phone, email, student_name
- Fieldsets: Student, Permissions, Usage Time, Status, Timestamps
- Actions: activate_parents, deactivate_parents

#### ParentAppUsageLogAdmin
- List display: parent_link, date, total_minutes, session_count
- Filters: date, created_at
- Search: parent_name, student_name
- Date hierarchy: date
- Read-only: All fields (auto-generated)

---

### 6. Documentation Files Created
1. **PARENT_PORTAL_API.md** - مستندات کامل API
2. **PARENT_PORTAL_SETUP.md** - راهنمای راه‌اندازی
3. **PARENT_PORTAL_EXAMPLES.py** - مثال‌های عملی و testing

---

## 🔐 امنیت

### Password Hashing
- از `django.contrib.auth.hashers.make_password()` استفاده می‌شود
- رمز والد از رمز دانش‌آموز **متفاوت** است
- هرگز رمز ذخیره نمی‌شود

### Authentication
- والدین با `student_id + parent_password` وارد می‌شوند
- متفاوت از ورود دانش‌آموز/معلم
- Token صادر می‌شود برای دسترسی‌های بعدی

### Authorization
- مجوزهای دانه‌بندی شده برای هر والد
- Admins می‌توانند مجوزها را تغییر دهند
- والدین فقط اطلاعات فرزند خود را می‌بینند

---

## 📊 Database Schema

```
Parent Profiles Table:
┌─────────────────────────────────────────┐
│ parent_profiles                         │
├─────────────────────────────────────────┤
│ id (PK)                                 │
│ student_id (FK → users)                │
│ parent_name                             │
│ phone                                   │
│ email                                   │
│ parent_password_hash                    │
│ can_view_class_history                  │
│ can_view_payments                       │
│ can_select_teacher                      │
│ can_set_usage_time                      │
│ daily_usage_limit_minutes               │
│ allowed_start_time                      │
│ allowed_end_time                        │
│ is_active                               │
│ last_login_at                           │
│ created_at                              │
│ updated_at                              │
└─────────────────────────────────────────┘

Usage Logs Table:
┌─────────────────────────────────────────┐
│ parent_app_usage_logs                   │
├─────────────────────────────────────────┤
│ id (PK)                                 │
│ parent_id (FK → parent_profiles)       │
│ date                                    │
│ total_minutes                           │
│ session_count                           │
│ created_at                              │
│ updated_at                              │
└─────────────────────────────────────────┘
```

---

## 🔄 User Flow

### 1. والد ورود می‌کند
```
والد → POST /api/parent/login/ (student_id, parent_password)
           ↓
       سرور بررسی می‌کند
           ↓
       Token صادر می‌شود
           ↓
       والد → پاسخ: {token, permissions}
```

### 2. والد داشبورد را مشاهده می‌کند
```
والد → GET /api/parent/dashboard/?child_id=5
           ↓
       سرور اطلاعات کودک و آمار را جمع می‌کند
           ↓
       والد → پاسخ: {child, stats}
```

### 3. والد کلاس‌های کودک را می‌بیند
```
والد → GET /api/parent/child-class-history/?child_id=5
           ↓
       سرور لیست کلاس‌ها را می‌فرستد
           ↓
       والد → پاسخ: {classes}
```

### 4. والد محدودیت زمان را تنظیم می‌کند
```
والد → POST /api/parent/update-usage-time/
       (daily_limit, start_time, end_time)
           ↓
       سرور به‌روزرسانی می‌کند
           ↓
       والد → پاسخ: {updated_data}
```

---

## 🧪 Testing

### 1. با cURL
```bash
# Login (with student ID)
curl -X POST http://localhost:8000/api/parent/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "5", "parent_password": "pass123"}'

# Login (with phone)
curl -X POST http://localhost:8000/api/parent/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "09123456789", "parent_password": "pass123"}'

# Login (with email)
curl -X POST http://localhost:8000/api/parent/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "parent@email.com", "parent_password": "pass123"}'

# Dashboard
curl -X GET "http://localhost:8000/api/parent/dashboard/?child_id=5"

# Update usage time
curl -X POST http://localhost:8000/api/parent/update-usage-time/ \
  -H "Content-Type: application/json" \
  -d '{"child_id": 5, "daily_usage_limit_minutes": 60}'
```

### 2. با Django Shell
```python
python manage.py shell
# سپس مثال‌های در PARENT_PORTAL_EXAMPLES.py را اجرا کنید
```

### 3. با Postman
- Import requests از فایل documentation
- Set variables برای student_id, parent_password
- Run collection

---

## 📝 مثال: ایجاد والد

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
parent.set_password("SecurePassword123!")
parent.save()
```

---

## 🚀 راه‌اندازی

### مرحله 1: Migration
```bash
python manage.py makemigrations account
python manage.py migrate account
```

### مرحله 2: ایجاد والد نمونه
```bash
python manage.py shell
# اجرا کردن مثال‌های بالا
```

### مرحله 3: تست APIs
```bash
# استفاده از cURL یا Postman
```

### مرحله 4: Django Admin
```
http://localhost:8000/admin/
Account > Parent Profiles
```

---

## 📋 Checklist

- ✅ ParentProfile model ایجاد شده
- ✅ ParentAppUsageLog model ایجاد شده
- ✅ Parent serializers نوشته شده
- ✅ Parent views پیاده‌سازی شده
- ✅ URL patterns اضافه شده
- ✅ Django Admin configuration انجام شده
- ✅ مستندات نوشته شده
- ✅ مثال‌های عملی فراهم شده
- ⏳ Migration باید اجرا شود

---

## 🔗 فایل‌های مرتبط

| فایل | توضیح |
|-----|-------|
| `account/models.py` | ParentProfile, ParentAppUsageLog models |
| `account/admin.py` | ParentProfileAdmin, ParentAppUsageLogAdmin |
| `api/parent_serializers.py` | تمام parent serializers |
| `api/views.py` | تمام parent API views |
| `api/urls.py` | parent API URL patterns |
| `PARENT_PORTAL_API.md` | مستندات کامل API |
| `PARENT_PORTAL_SETUP.md` | راهنمای راه‌اندازی |
| `PARENT_PORTAL_EXAMPLES.py` | مثال‌های عملی |

---

## 💡 نکات مهم

1. **رمز والد ≠ رمز دانش‌آموز**
   - والد رمز خود را دارد
   - ورود والد از ورود دانش‌آموز متفاوت است

2. **مجوزهای دانه‌بندی شده**
   - هر والد می‌تواند مجوزهای مختلفی داشته باشد
   - Admins کنترل کامل دارند

3. **محدودیت‌های زمانی**
   - والدین می‌توانند زمان استفاده کودک را محدود کنند
   - شامل: حداکثر دقایق روزانه + ساعت شروع/پایان

4. **Tracking**
   - `last_login_at` برای audit trail
   - `ParentAppUsageLog` برای ردیابی استفاده

---

## ❓ سوالات متداول

**Q: آیا می‌توانم والد بدون رمز ایجاد کنم؟**
A: خیر، رمز الزامی است. باید `set_password()` را صدا بزنید.

**Q: آیا والد می‌تواند چند کودک را کنترل کند؟**
A: دقیقاً اینطور است - هر والد فقط یک کودک را کنترل می‌کند.

**Q: اگر والد `daily_usage_limit_minutes = 0` تنظیم کند؟**
A: 0 معنی بدون محدودیت است.

**Q: آیا والد می‌تواند معلم برای کودک انتخاب کند؟**
A: فقط اگر `can_select_teacher = True`.

---

## 📞 Support

برای سوالات یا مشکلات:
1. مستندات را بررسی کنید (PARENT_PORTAL_API.md)
2. مثال‌های عملی را اجرا کنید (PARENT_PORTAL_EXAMPLES.py)
3. Django Admin را بررسی کنید
4. logs را چک کنید
