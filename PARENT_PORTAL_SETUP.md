# راهنمای کامل سیستم دسترسی والدین - Parent Portal Setup Guide

## فهرست
1. [نمای کلی](#نمای-کلی)
2. [مدل‌های جدید](#مدلهای-جدید)
3. [ترتیب اجرا](#ترتیب-اجرا)
4. [مثال‌های عملی](#مثالهای-عملی)
5. [تنظیمات Django Admin](#تنظیمات-django-admin)

---

## نمای کلی

### مشکل
والدین نیاز دارند به:
- تاریخچه کلاس‌های کودکشان دسترسی داشته باشند
- پرداخت‌های کودک را کنترل کنند
- معلم برای کودک انتخاب کنند
- زمان استفاده اپلیکیشن توسط کودک را محدود کنند
- با روش‌های متعدد وارد شوند (شناسه دانش‌آموز، شماره تماس، ایمیل)

### راه‌حل
1. مدل `ParentProfile` برای ذخیره اطلاعات والد
2. مدل `ParentAppUsageLog` برای ردیابی استفاده
3. APIs جداگانه برای ورود والد و کنترل

---

## مدل‌های جدید

### 1. ParentProfile Model
**فایل:** `account/models.py`

```python
class ParentProfile(BaseModel):
    """والدین می‌توانند با شناسه دانش‌آموز یا شماره تماس یا ایمیل + parent_password وارد شوند"""
    
    # ارتباط
    student = models.ForeignKey(User, ...)  # کودک
    parent_name = models.CharField(max_length=200)  # نام والد
    phone = models.CharField(max_length=20)  # شماره تماس
    email = models.EmailField()  # ایمیل
    
    # امنیت
    parent_password_hash = models.CharField(max_length=255)  # رمز هش‌شده
    
    # مجوزها
    can_view_class_history = True  # مشاهده کلاس‌ها
    can_view_payments = True  # مشاهده پرداخت‌ها
    can_select_teacher = False  # انتخاب معلم (اختیاری)
    can_set_usage_time = True  # تنظیم زمان
    
    # محدودیت‌های زمانی
    daily_usage_limit_minutes = IntegerField()  # حداکثر دقایق روزانه
    allowed_start_time = TimeField()  # شروع استفاده مجاز (08:00)
    allowed_end_time = TimeField()  # پایان استفاده مجاز (22:00)
    
    # وضعیت
    is_active = BooleanField(default=True)  # فعال/غیرفعال
    last_login_at = DateTimeField()  # آخرین ورود
```

### 2. ParentAppUsageLog Model
**فایل:** `account/models.py`

```python
class ParentAppUsageLog(BaseModel):
    """ثبت استفاده روزانه کودک"""
    
    parent = models.ForeignKey(ParentProfile, ...)
    date = models.DateField()  # تاریخ
    total_minutes = IntegerField()  # کل دقایق
    session_count = IntegerField()  # تعداد جلسات
```

---

## ترتیب اجرا

### مرحله 1: مایگریشن
```bash
# مایگریشن را بسازید
python manage.py makemigrations account

# مایگریشن را اعمال کنید
python manage.py migrate account
```

### مرحله 2: ثبت در Admin
**فایل:** `account/admin.py`

```python
admin.site.register(ParentProfile, ParentProfileAdmin)
admin.site.register(ParentAppUsageLog, ParentAppUsageLogAdmin)
```

### مرحله 3: مدل‌های Serializer
**فایل:** `api/parent_serializers.py` (جدید)

- `ParentLoginSerializer`: ورود والد
- `ChildClassHistorySerializer`: تاریخچه کلاس
- `ChildPaymentHistorySerializer`: تاریخچه پرداخت
- `ParentProfileSerializer`: اطلاعات والد
- `ParentUpdateUsageTimeSerializer`: به‌روزرسانی محدودیت‌های زمانی

### مرحله 4: Views
**فایل:** `api/views.py`

- `ParentLoginAPIView`: ورود والد
- `ParentDashboardAPIView`: داشبورد والد
- `ChildClassHistoryAPIView`: تاریخچه کلاس
- `ChildPaymentHistoryAPIView`: تاریخچه پرداخت
- `ChildPaymentSummaryAPIView`: خلاصه مالی
- `ParentUpdateUsageTimeAPIView`: به‌روزرسانی زمان
- `ParentProfileAPIView`: نمایش اطلاعات والد

### مرحله 5: URLs
**فایل:** `api/urls.py`

```python
# ===== Parent Portal APIs =====
path('parent/login/', views.ParentLoginAPIView.as_view(), name='parent_login'),
path('parent/dashboard/', views.ParentDashboardAPIView.as_view(), name='parent_dashboard'),
path('parent/child-class-history/', views.ChildClassHistoryAPIView.as_view(), ...),
path('parent/child-payment-history/', views.ChildPaymentHistoryAPIView.as_view(), ...),
path('parent/payment-summary/', views.ChildPaymentSummaryAPIView.as_view(), ...),
path('parent/update-usage-time/', views.ParentUpdateUsageTimeAPIView.as_view(), ...),
path('parent/profile/', views.ParentProfileAPIView.as_view(), ...),
```

---

## مثال‌های عملی

### مثال 1: ایجاد والد در کد

```python
from account.models import ParentProfile, User
from django.contrib.auth.hashers import make_password

# دانش‌آموز را پیدا کنید
student = User.objects.get(id=5)

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

# رمز را تنظیم کنید
parent.set_password("securepassword123")
parent.save()
```

### مثال 2: ورود والد

**با شناسه دانش‌آموز:**
```bash
POST /api/parent/login/
Content-Type: application/json

{
  "identifier": "5",
  "parent_password": "securepassword123"
}
```

**با شماره تماس:**
```bash
POST /api/parent/login/
Content-Type: application/json

{
  "identifier": "09123456789",
  "parent_password": "securepassword123"
}
```

**با ایمیل:**
```bash
POST /api/parent/login/
Content-Type: application/json

{
  "identifier": "parent@email.com",
  "parent_password": "securepassword123"
}
```

**پاسخ:**
```json
{
  "parent_token": "abc123xyz...",
  "parent_id": 3,
  "parent_name": "محمد علی احمدی",
  "student_id": 5,
  "student_name": "فاطمه احمدی",
  "can_view_class_history": true,
  "can_view_payments": true
}
```

### مثال 3: مشاهده داشبورد

```bash
GET /api/parent/dashboard/?child_id=5
```

### مثال 4: مشاهده کلاس‌های تکمیل‌شده

```bash
GET /api/parent/child-class-history/?child_id=5&status=completed
```

### مثال 5: تنظیم محدودیت زمان

```bash
POST /api/parent/update-usage-time/
Content-Type: application/json

{
  "child_id": 5,
  "daily_usage_limit_minutes": 60,  # 1 ساعت
  "allowed_start_time": "14:00",    # از 2 بعدازظهر
  "allowed_end_time": "21:00"       # تا 9 شب
}
```

---

## تنظیمات Django Admin

### دسترسی به Parent Profiles

1. Django Admin خود را باز کنید: `http://localhost:8000/admin/`
2. به بخش `Account` رفتید
3. `Parent Profiles` را انتخاب کنید

### عملیات در Admin

#### افزودن والد جدید
1. دکمه "Add Parent Profile" را کلیک کنید
2. دانش‌آموز را انتخاب کنید
3. نام، شماره و ایمیل را وارد کنید
4. مجوزها را تنظیم کنید
5. محدودیت‌های زمانی را تعیین کنید
6. "Save" را کلیک کنید

#### ویرایش والد موجود
1. والد را از لیست انتخاب کنید
2. اطلاعات را ویرایش کنید
3. "Save" را کلیک کنید

#### غیرفعال کردن والد
1. والد را انتخاب کنید
2. Checkbox `is_active` را بردارید
3. "Save" را کلیک کنید

#### جستجو
می‌توانید با موارد زیر جستجو کنید:
- نام والد
- شماره تماس
- ایمیل
- نام دانش‌آموز

### فیلترها
- `is_active`: فعال/غیرفعال
- `can_view_class_history`: می‌تواند کلاس‌ها را ببیند
- `can_view_payments`: می‌تواند پرداخت‌ها را ببیند
- `can_select_teacher`: می‌تواند معلم انتخاب کند
- `can_set_usage_time`: می‌تواند زمان را تنظیم کند

---

## API Reference Quick List

| Endpoint | Method | توضیح |
|----------|--------|-------|
| `/api/parent/login/` | POST | ورود والد |
| `/api/parent/dashboard/` | GET | داشبورد والد |
| `/api/parent/child-class-history/` | GET | تاریخچه کلاس‌ها |
| `/api/parent/child-payment-history/` | GET | تاریخچه پرداخت‌ها |
| `/api/parent/payment-summary/` | GET | خلاصه مالی |
| `/api/parent/update-usage-time/` | POST | تنظیم محدودیت زمان |
| `/api/parent/profile/` | GET | اطلاعات والد |

---

## نکات مهم

### 1. رمز والد
- رمز والد از رمز دانش‌آموز **متفاوت** است
- رمز والد فقط برای ورود والد استفاده می‌شود
- رمز هش‌شده در `parent_password_hash` ذخیره می‌شود

### 2. مجوزها
- هر والد می‌تواند مجوزهای مختلفی داشته باشد
- Admins می‌توانند مجوزها را برای هر والد تغییر دهند
- `can_select_teacher` معمولاً برای والدین معمولی `False` است

### 3. محدودیت‌های زمانی
- `daily_usage_limit_minutes`: 0-1440 (0 = بدون محدودیت)
- `allowed_start_time` و `allowed_end_time`: ساعت شروع و پایان روز
- مثال: 08:00-22:00 یعنی کودک فقط در این ساعات می‌تواند استفاده کند

### 4. تاریخچه استفاده
- `ParentAppUsageLog` به صورت خودکار ساخته می‌شود
- والدین می‌توانند استفاده روزانه کودک را رصد کنند
- Admins می‌توانند اطلاعات استفاده را مشاهده کنند

---

## Troubleshooting

### مشکل: "Parent profile not found"
**حل:** اطمینان دارید که والد برای این دانش‌آموز وجود دارد

### مشکل: "Invalid password"
**حل:** رمز والد را درست وارد کنید (از رمز دانش‌آموز متفاوت است)

### مشکل: "Permission denied"
**حل:** بررسی کنید که والد مجوز دسترسی را دارد (`can_view_class_history` = True)

---

## Files Modified/Created

### فایل‌های تغییر یافته:
1. `account/models.py` - افزودن ParentProfile و ParentAppUsageLog
2. `account/admin.py` - افزودن Admin classes برای والدین
3. `api/views.py` - افزودن parent portal views
4. `api/urls.py` - افزودن URL patterns

### فایل‌های جدید:
1. `api/parent_serializers.py` - تمام serializers والدین
2. `PARENT_PORTAL_API.md` - مستندات کامل API
3. `PARENT_PORTAL_SETUP.md` - این فایل

---

## Next Steps

1. **Migration اجرا کنید:**
   ```bash
   python manage.py makemigrations account
   python manage.py migrate account
   ```

2. **والد نمونه ایجاد کنید:**
   ```bash
   python manage.py shell
   # سپس مثال 1 را اجرا کنید
   ```

3. **APIs را تست کنید:**
   - Postman یا cURL استفاده کنید
   - یا `curl` از terminal استفاده کنید

4. **Django Admin را اکتشاف کنید:**
   - `http://localhost:8000/admin/`
   - به Parent Profiles رفتید

---

## سوالات متداول (FAQ)

**Q: آیا والد می‌تواند کودک دیگری را مشاهده کند؟**
A: خیر، والد فقط می‌تواند اطلاعات فرزند خود را ببیند.

**Q: آیا می‌توانم رمز والد را تغییر دهم؟**
A: بله، admins می‌توانند رمز را در Django Admin تغییر دهند.

**Q: اگر والد رمز خود را فراموش کند چه؟**
A: Admin می‌تواند رمز را ریست کند.

**Q: آیا والد می‌تواند معلم را انتخاب کند؟**
A: فقط اگر `can_select_teacher` = True باشد.

**Q: حداکثر دقایق روزانه چیست؟**
A: می‌توانید هر عددی را تنظیم کنید (0 = بدون محدودیت).
