# راهنمای ویرایش پروفایل | Profile Editing Guide

## فهرست مطالب
1. [ویرایش پروفایل دانش‌آموز](#ویرایش-پروفایل-دانشآموز)
2. [ویرایش پروفایل معلم](#ویرایش-پروفایل-معلم)
3. [تغییر رمز عبور](#تغییر-رمز-عبور)
4. [انتخاب آواتار](#انتخاب-آواتار)
5. [کدهای خطا](#کدهای-خطا)

---

## ویرایش پروفایل دانش‌آموز

### Endpoint
```
POST /api/profile/
```

### توضیحات
دانش‌آموز می‌تواند اطلاعات شخصی خود را تکمیل یا ویرایش کند.

### فیلدهای قابل ویرایش

| فیلد | نوع | توصیف | مثال |
|-----|------|-------|------|
| `name` | string | نام نمایشی | علی محمدی |
| `email` | string | ایمیل | ali@example.com |
| `phone` | string | شماره تماس | 09123456789 |
| `bio` | string | درباره من | معلومات شخصی |
| `birth_date` | string | تاریخ تولد (شمسی) | 1403-05-24 |
| `gender` | string | جنسیت | male, female, custom, prefer_not_to_say |
| `profile_photo_path` | file | عکس پروفایل | (JPG, PNG, GIF) |

### نمونه درخواست

**بدون فایل:**
```json
{
    "name": "علی محمدی",
    "email": "ali@example.com",
    "phone": "09123456789",
    "bio": "دانش‌آموز جدی و متعهد",
    "birth_date": "1403-05-24",
    "gender": "male"
}
```

### نمونه پاسخ موفق (200 OK)
```json
{
    "success": true,
    "message": "Profile updated successfully",
    "user": {
        "id": 42,
        "username": "ali.mohammad",
        "name": "علی محمدی",
        "email": "ali@example.com",
        "phone": "09123456789",
        "bio": "دانش‌آموز جدی و متعهد",
        "role": "user",
        "profile_photo_path": null,
        "is_teacher_verified": false,
        "created_at": "2024-01-15T10:00:00Z"
    }
}
```

### نمونه cURL
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "علی محمدی",
    "email": "ali@example.com",
    "phone": "09123456789",
    "bio": "دانش‌آموز جدی و متعهد",
    "birth_date": "1403-05-24",
    "gender": "male"
  }'
```

---

## ویرایش پروفایل معلم

### Endpoint
```
POST /api/profile/
```

### توضیحات
معلم می‌تواند اطلاعات حرفه‌ای و شخصی خود را ویرایش کند.

### فیلدهای قابل ویرایش

| فیلد | نوع | توصیف | مثال |
|-----|------|-------|------|
| `name` | string | نام نمایشی | علی محمدی |
| `email` | string | ایمیل | teacher@example.com |
| `phone` | string | شماره تماس | 09123456789 |
| `bio` | string | درباره من | معلم باتجربه |
| `qualifications` | string | مدرک تحصیلی | کارشناسی ارشد زبان انگلیسی |
| `languages_taught` | string | زبان‌های تدریس‌شده | انگلیسی, فرانسوی |
| `specialization` | string | تخصص | تدریس مکالمه |
| `resume_summary` | string | خلاصه رزومه | 15 سال تجربه تدریس |
| `introduction_video` | file | فایل ویدئوی معرفی | (MP4, AVI, MOV, ...) |
| `hourly_rate` | decimal | قیمت ساعتی | 250000 |
| `experience_years` | integer | سال‌های تجربه | 15 |
| `profile_photo_path` | file | عکس پروفایل | (JPG, PNG, GIF) |

### نمونه درخواست

```
name: علی محمدی
email: teacher@example.com
phone: 09123456789
bio: معلم انگلیسی با تجربه
qualifications: کارشناسی ارشد زبان انگلیسی، مدرک TEFL
languages_taught: انگلیسی, فرانسوی
specialization: تدریس مکالمه و مهارت‌های تجاری
resume_summary: 15 سال تجربه تدریس در دبیرستان و دانشگاه
introduction_video: <file> (فایل ویدئو)
hourly_rate: 250000
experience_years: 15
profile_photo_path: <file> (عکس پروفایل)
```

### نمونه پاسخ موفق (200 OK)
```json
{
    "success": true,
    "message": "Teacher profile updated successfully",
    "teacher": {
        "id": 42,
        "username": "ali.teacher",
        "name": "علی محمدی",
        "email": "teacher@example.com",
        "phone": "09123456789",
        "bio": "معلم انگلیسی با تجربه",
        "role": "teacher",
        "qualifications": "کارشناسی ارشد زبان انگلیسی",
        "languages_taught": "انگلیسی, فرانسوی",
        "specialization": "تدریس مکالمه",
        "resume_summary": "15 سال تجربه",
        "introduction_video": "/media/videos/intro_12345.mp4",
        "hourly_rate": "250000.00",
        "experience_years": 15,
        "is_teacher_verified": true
    }
}
```

### نمونه cURL
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=علی محمدی" \
  -F "email=teacher@example.com" \
  -F "phone=09123456789" \
  -F "bio=معلم انگلیسی با تجربه" \
  -F "qualifications=کارشناسی ارشد" \
  -F "languages_taught=انگلیسی, فرانسوی" \
  -F "specialization=تدریس مکالمه" \
  -F "introduction_video=@/path/to/video.mp4" \
  -F "hourly_rate=250000" \
  -F "experience_years=15" \
  -F "profile_photo_path=@/path/to/photo.jpg"
```

---

## تغییر رمز عبور

### Endpoint
```
POST /api/change-password/
```

### فیلدهای مورد نیاز

| فیلد | نوع | توصیف |
|-----|------|-------|
| `old_password` | string | رمز عبور فعلی |
| `new_password` | string | رمز عبور جدید (حداقل 8 کاراکتر) |
| `confirm_password` | string | تأیید رمز عبور جدید |

### نمونه درخواست
```json
{
    "old_password": "OldPassword123",
    "new_password": "NewPassword456",
    "confirm_password": "NewPassword456"
}
```

### نمونه پاسخ موفق (200 OK)
```json
{
    "success": true,
    "message": "Password changed successfully"
}
```

### نمونه cURL
```bash
curl -X POST https://api.example.com/api/change-password/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPassword123",
    "new_password": "NewPassword456",
    "confirm_password": "NewPassword456"
  }'
```

### خطاهای ممکن
- **400 Bad Request**: رمز عبور قدیم نادرست است
- **400 Bad Request**: رمز عبور جدید و تأیید آن تطابق ندارند
- **400 Bad Request**: رمز عبور خیلی کوتاه است

---

## انتخاب آواتار

### دریافت لیست آواتارها

**Endpoint:** `GET /api/avatars/`

**نمونه پاسخ:**
```json
[
    {
        "id": 1,
        "name": "آواتار 1",
        "image": "https://api.example.com/media/avatars/1.png"
    },
    {
        "id": 2,
        "name": "آواتار 2",
        "image": "https://api.example.com/media/avatars/2.png"
    }
]
```

### انتخاب آواتار

**Endpoint:** `POST /api/select-avatar/`

**درخواست:**
```json
{
    "avatar_template_id": 1
}
```

**پاسخ موفق (200 OK):**
```json
{
    "success": true,
    "message": "Avatar selected successfully",
    "user": {
        "id": 42,
        "selected_avatar": {
            "id": 1,
            "image": "https://api.example.com/media/avatars/1.png"
        }
    }
}
```

### نمونه cURL
```bash
curl -X POST https://api.example.com/api/select-avatar/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "avatar_template_id": 1
  }'
```

---

## آپلود تصویر پروفایل

### Endpoint
```
POST /api/profile/
```

### توضیح
می‌توانید از `form-data` برای آپلود تصویر استفاده کنید.

### نمونه cURL
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=علی محمدی" \
  -F "email=ali@example.com" \
  -F "phone=09123456789" \
  -F "profile_photo_path=@/path/to/image.jpg"
```

### محدودیت‌های فایل
- **فرمت‌های مجاز:** JPG, JPEG, PNG, GIF
- **حداکثر اندازه:** معمولاً 5MB

---

## آپلود ویدئوی معرفی

### Endpoint
```
POST /api/profile/
```

### توضیح
معلمان می‌توانند از `form-data` برای آپلود ویدئوی معرفی استفاده کنند.

### نمونه cURL
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=علی محمدی" \
  -F "introduction_video=@/path/to/video.mp4"
```

### محدودیت‌های فایل
- **فرمت‌های مجاز:** MP4, AVI, MOV, WebM, FLV, MKV, 3GP, M4V, OGV
- **حداکثر اندازه:** معمولاً 100MB

---

## کدهای خطا

### 400 Bad Request
```json
{
    "success": false,
    "message": "Invalid data provided",
    "errors": {
        "email": ["This field may not be blank."],
        "phone": ["Enter a valid phone number."]
    }
}
```

**دلایل ممکن:**
- ایمیل یا شماره تماس نامعتبر
- فیلد الزامی خالی است
- داده در فرمت غلط است

### 401 Unauthorized
```json
{
    "success": false,
    "message": "Not authenticated"
}
```

**حل:**
- توکن شما منقضی شده است
- دوباره وارد سیستم شوید

### 403 Forbidden
```json
{
    "success": false,
    "message": "Only teachers can use this endpoint"
}
```

**معنی:**
- این endpoint فقط برای معلمان است

### 404 Not Found
```json
{
    "error": "Avatar template not found"
}
```

**حل:**
- شناسه آواتار نادرست است
- دوباره لیست آواتارها را بخواهید

---

## نکات مهم

### 🔐 احراز هویت
تمام درخواست‌ها باید شامل توکن باشند:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### ✅ تاریخ شمسی
تاریخ باید در فرمت **شمسی** و **YYYY-MM-DD** باشد:
- ✅ `1403-05-24` (صحیح)
- ❌ `2024-08-15` (میلادی - غلط)

### 📱 شماره تماس
شماره تماس باید به صورت **09xxxxxxxxx** باشد:
- ✅ `09123456789` (صحیح)
- ❌ `9123456789` (بدون 0 - غلط)
- ❌ `+989123456789` (با کد کشور - غلط)

### 🔤 نام کاربری
نام کاربری **نمی‌تواند** تغییر کند. شامل:
- نام (name)
- username (نام کاربری)

### 📊 مقادیر Enum
برخی فیلدها مقادیر محدود دارند:

**جنسیت:**
- `male` - مرد
- `female` - زن
- `custom` - سایر
- `prefer_not_to_say` - نمی‌خواهم بگویم

**سطح تدریس:**
- `beginner` - مبتدی
- `intermediate` - متوسط
- `advanced` - پیشرفته

---

## مثال کامل: ویرایش پروفایل دانش‌آموز

### مرحله 1: دریافت توکن (پس از ورود)
```bash
# پاسخ ورود شامل توکن است
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### مرحله 2: ویرایش پروفایل
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "name=علی محمدی" \
  -F "email=ali@example.com" \
  -F "phone=09123456789" \
  -F "bio=دانش‌آموز فعال" \
  -F "birth_date=1403-05-24" \
  -F "gender=male"
```

### مرحله 3: پاسخ
```json
{
    "success": true,
    "message": "Profile updated successfully",
    "user": {
        "id": 42,
        "name": "علی محمدی",
        "email": "ali@example.com",
        "phone": "09123456789",
        "bio": "دانش‌آموز فعال"
    }
}
```

---

## مراجع
- **Base URL:** `https://api.example.com`
- **Content-Type:** `application/json` (یا `form-data` برای فایل‌ها)
- **Authentication:** Bearer Token
- **Rate Limit:** معمولاً 100 درخواست در ساعت

---

**آخرین به‌روزرسانی:** 31 دسامبر 2025
