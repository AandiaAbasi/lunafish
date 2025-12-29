# API Endpoints Documentation
# مستندات نقاط پایانی API

## نقاط پایانی کامل سیستم

---

## 🏠 صفحه اصلی

### صفحه خانگی
```
GET /api/home/
```
- **توضیح**: اطلاعات صفحه خانگی
- **مجوز**: عمومی
- **پارامترها**: ندارد

---

## 🔐 احراز هویت

### ارسال OTP
```
POST /api/send-otp/
```
**جسم درخواست:**
```json
{
  "phone_number": "09120000000"
}
```
**پاسخ:**
```json
{
  "message": "OTP ارسال شد",
  "expires_in": 300
}
```

### تأیید OTP
```
POST /api/verify-otp/
```
**جسم درخواست:**
```json
{
  "phone_number": "09120000000",
  "otp": "123456"
}
```
**پاسخ:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": 1
}
```

### تکمیل ثبت‌نام
```
POST /api/complete-registration/
```
**مجوز:** نیاز دارد `Authorization: Bearer TOKEN`

**جسم درخواست:**
```json
{
  "full_name": "علی محمدی",
  "avatar": "file.jpg",
  "grade": "1"
}
```

### بررسی نام کاربری
```
POST /api/check-username/
```
**جسم درخواست:**
```json
{
  "username": "ali_mohammadi"
}
```
**پاسخ:**
```json
{
  "available": true
}
```

### ورود با رمز
```
POST /api/login-password/
```
**جسم درخواست:**
```json
{
  "username": "ali_mohammadi",
  "password": "password123"
}
```

---

## 👨‍🏫 احراز هویت معلم

### ورود معلم با رمز
```
POST /api/teacher/login-password/
```
**جسم درخواست:**
```json
{
  "username": "teacher_name",
  "password": "password123"
}
```

### ارسال OTP معلم
```
POST /api/teacher/send-otp/
```
**جسم درخواست:**
```json
{
  "phone_number": "09120000000"
}
```

### تأیید OTP معلم
```
POST /api/teacher/verify-otp/
```
**جسم درخواست:**
```json
{
  "phone_number": "09120000000",
  "otp": "123456"
}
```

### تکمیل ثبت‌نام معلم
```
POST /api/teacher/complete-registration/
```
**جسم درخواست:**
```json
{
  "full_name": "دکتر علی محمدی",
  "bio": "معلم تجربی",
  "avatar": "file.jpg"
}
```

---

## 📧 احراز هویت مبتنی بر ایمیل

### ارسال OTP ایمیل (دانش‌آموز)
```
POST /api/user/send-email-otp/
```
**جسم درخواست:**
```json
{
  "email": "user@example.com"
}
```

### تأیید OTP ایمیل (دانش‌آموز)
```
POST /api/user/verify-email-otp/
```
**جسم درخواست:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

### ارسال OTP ایمیل (معلم)
```
POST /api/teacher/send-email-otp/
```
**جسم درخواست:**
```json
{
  "email": "teacher@example.com"
}
```

### تأیید OTP ایمیل (معلم)
```
POST /api/teacher/verify-email-otp/
```
**جسم درخواست:**
```json
{
  "email": "teacher@example.com",
  "otp": "123456"
}
```

---

## 👤 مدیریت پروفایل

### دریافت اطلاعات کاربر
```
GET /api/fetch-user/
```
**مجوز:** نیاز دارد `Authorization: Bearer TOKEN`

**پاسخ:**
```json
{
  "id": 1,
  "username": "ali_mohammadi",
  "full_name": "علی محمدی",
  "phone_number": "09120000000",
  "email": "ali@example.com",
  "role": "student",
  "grade": "1",
  "avatar": "http://..."
}
```

### نمایش پروفایل
```
GET /api/profile/
POST /api/profile/
```
**مجوز:** نیاز دارد `Authorization: Bearer TOKEN`

**جسم درخواست (POST):**
```json
{
  "full_name": "علی محمدی",
  "bio": "نویسنده",
  "avatar": "file.jpg"
}
```

### تکمیل پروفایل دانش‌آموز
```
POST /api/complete-student-profile/
```
**جسم درخواست:**
```json
{
  "full_name": "علی محمدی",
  "grade": "1",
  "school": "دبیرستان فردوسی"
}
```

### تکمیل پروفایل معلم
```
POST /api/complete-teacher-profile/
```
**جسم درخواست:**
```json
{
  "full_name": "دکتر علی محمدی",
  "bio": "معلم تجربی",
  "experience_years": 10,
  "specialization": "علوم تجربی"
}
```

### ارتقا به معلم
```
POST /api/promote-to-teacher/
```
**مجوز:** دانش‌آموز موجود

**جسم درخواست:**
```json
{
  "bio": "می‌خواهم معلم شوم",
  "certificate": "file.pdf"
}
```

---

## 🎨 قالب‌های آواتار

### لیست آواتارها
```
GET /api/avatars/
```
**مجوز:** عمومی

**پاسخ:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "Avatar 1",
      "image": "http://..."
    }
  ]
}
```

### انتخاب آواتار
```
POST /api/select-avatar/
```
**مجوز:** نیاز دارد `Authorization: Bearer TOKEN`

**جسم درخواست:**
```json
{
  "avatar_id": 1
}
```

---

## 🔒 تنظیمات و امنیت

### تغییر رمز عبور
```
POST /api/change-password/
```
**مجوز:** نیاز دارد `Authorization: Bearer TOKEN`

**جسم درخواست:**
```json
{
  "old_password": "password123",
  "new_password": "newpassword456"
}
```

### خروج
```
POST /api/logout/
```
**مجوز:** نیاز دارد `Authorization: Bearer TOKEN`

---

## 📚 محتوای اصلی

### لیست مقالات
```
GET /api/articles/
```
**پارامترهای کوئری:**
- `search`: جستجو در عنوان
- `page`: شماره صفحه

**پاسخ:**
```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "title": "مقاله 1",
      "content": "محتوا...",
      "author": "علی",
      "created_at": "2025-01-01"
    }
  ]
}
```

### جزئیات مقاله
```
GET /api/articles/{id}/
```

### لیست سوالات متداول
```
GET /api/faqs/
```

### درباره
```
GET /api/about/
```

### شرایط و ضوابط
```
GET /api/terms/
```

### حریم خصوصی
```
GET /api/privacy/
```

### تماس با ما
```
GET /api/contact/
```

### شماره تماس
```
GET /api/contact/phone/
```

---

## ⏰ شکاف‌های زمانی معلم

### لیست شکاف‌های زمانی
```
GET /api/teacher/availability/
```
**مجوز:** معلم
**پارامترهای کوئری:**
- `date`: تاریخ خاص (YYYY-MM-DD)
- `day_of_week`: روز هفته (0-6)

**پاسخ:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "teacher": 1,
      "day_of_week": 1,
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "capacity": 2,
      "booked": 1,
      "is_active": true
    }
  ]
}
```

### ایجاد شکاف زمانی
```
POST /api/teacher/availability/create/
```
**مجوز:** معلم

**جسم درخواست:**
```json
{
  "day_of_week": 1,
  "start_time": "09:00:00",
  "end_time": "10:00:00",
  "capacity": 2,
  "hourly_rate": 100000
}
```

### ایجاد گروهی شکاف‌های زمانی
```
POST /api/teacher/availability/bulk-create/
```
**مجوز:** معلم

**جسم درخواست:**
```json
{
  "availabilities": [
    {
      "day_of_week": 1,
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "capacity": 2
    },
    {
      "day_of_week": 2,
      "start_time": "10:00:00",
      "end_time": "11:00:00",
      "capacity": 2
    }
  ]
}
```

### بروزرسانی شکاف زمانی
```
POST /api/teacher/availability/{id}/update/
```
**مجوز:** معلم (مالک)

**جسم درخواست:**
```json
{
  "capacity": 3,
  "hourly_rate": 120000,
  "is_active": true
}
```

### حذف شکاف زمانی
```
POST /api/teacher/availability/{id}/delete/
```
**مجوز:** معلم (مالک)

---

## 📖 موضوعات تدریسی (کلاس‌ها)

### لیست موضوعات تدریسی
```
GET /api/teaching-subjects/
```
**پارامترهای کوئری:**
- `teacher`: شناسه معلم
- `level`: سطح درس
- `is_active`: فعال بودن

**پاسخ:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "title": "انگلیسی سطح 1",
      "description": "درس انگلیسی برای مبتدیان",
      "teacher": 1,
      "level": "beginner",
      "price": 150000,
      "image": "http://...",
      "is_active": true,
      "created_at": "2025-01-01"
    }
  ]
}
```

### ایجاد موضوع تدریسی
```
POST /api/teaching-subjects/create/
```
**مجوز:** معلم

**جسم درخواست:**
```json
{
  "title": "انگلیسی سطح 1",
  "description": "درس انگلیسی برای مبتدیان",
  "level": "beginner",
  "price": 150000,
  "image": "file.jpg",
  "is_active": true
}
```

### دریافت جزئیات موضوع
```
GET /api/teaching-subjects/{id}/
```

**پاسخ:**
```json
{
  "id": 1,
  "title": "انگلیسی سطح 1",
  "description": "درس انگلیسی برای مبتدیان",
  "teacher": {
    "id": 1,
    "name": "علی محمدی"
  },
  "level": "beginner",
  "price": 150000,
  "image": "http://...",
  "rating": 4.5,
  "reviews_count": 10,
  "students_count": 25,
  "is_active": true,
  "created_at": "2025-01-01"
}
```

### بروزرسانی موضوع تدریسی
```
POST /api/teaching-subjects/{id}/update/
```
**مجوز:** معلم (مالک)

**جسم درخواست:**
```json
{
  "title": "انگلیسی سطح 1 (بهینه‌شده)",
  "price": 160000,
  "is_active": true
}
```

### حذف موضوع تدریسی
```
POST /api/teaching-subjects/{id}/delete/
```
**مجوز:** معلم (مالک)

---

## 📋 خلاصه Endpoints

| روش | مسیر | توضیح | مجوز |
|------|------|-------|------|
| GET | `/api/home/` | صفحه اصلی | عمومی |
| POST | `/api/send-otp/` | ارسال OTP | عمومی |
| POST | `/api/verify-otp/` | تأیید OTP | عمومی |
| POST | `/api/complete-registration/` | تکمیل ثبت‌نام | توکن |
| POST | `/api/check-username/` | بررسی نام کاربری | عمومی |
| GET | `/api/fetch-user/` | دریافت اطلاعات | توکن |
| GET | `/api/profile/` | نمایش پروفایل | توکن |
| POST | `/api/profile/` | بروزرسانی پروفایل | توکن |
| POST | `/api/change-password/` | تغییر رمز | توکن |
| POST | `/api/logout/` | خروج | توکن |
| GET | `/api/articles/` | لیست مقالات | عمومی |
| GET | `/api/avatars/` | لیست آواتارها | عمومی |
| GET | `/api/teacher/availability/` | لیست شکاف‌ها | معلم |
| POST | `/api/teacher/availability/create/` | ایجاد شکاف | معلم |
| GET | `/api/teaching-subjects/` | لیست کلاس‌ها | عمومی |
| POST | `/api/teaching-subjects/create/` | ایجاد کلاس | معلم |

---

## 🔑 توکن و مجوز

### استفاده از توکن
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### تجدید توکن
```
POST /api/token/refresh/
```
**جسم درخواست:**
```json
{
  "refresh": "refresh_token_here"
}
```

---

## ❌ کدهای خطا

| کد | معنی |
|------|------|
| 200 | موفق |
| 201 | ایجاد شده |
| 204 | بدون محتوا |
| 400 | درخواست نامعتبر |
| 401 | عدم احراز هویت |
| 403 | دسترسی ممنوع |
| 404 | یافت نشد |
| 409 | تضاد |
| 500 | خطای سرور |

---

## 📝 یادداشت‌های مهم

1. **توکن JWT**: تمام درخواست‌های محدود به احراز هویت نیاز به توکن دارند
2. **صفحه‌بندی**: لیست‌های بزرگ از صفحه‌بندی پشتیبانی می‌کنند
3. **فیلتر**: بیشتر لیست‌ها فیلتراسیون را پشتیبانی می‌کنند
4. **محدودیت نرخ**: 100 درخواست در دقیقه
5. **زمان حذف**: اطلاعات 30 روز بعد حذف می‌شود

---

## 📞 تماس

برای سوالات بیشتر:
- Email: support@fofofish.com
- Phone: +98-21-XXXX-XXXX

