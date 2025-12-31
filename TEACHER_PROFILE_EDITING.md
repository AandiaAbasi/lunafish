# راهنمای ویرایش پروفایل معلم | Teacher Profile Editing Guide

## فهرست مطالب
1. [Endpoint](#endpoint)
2. [فیلدهای قابل ویرایش](#فیلدهای-قابل-ویرایش)
3. [نمونه‌های عملی](#نمونههای-عملی)
4. [حذف فیلم معرفی](#حذف-فیلم-معرفی)
5. [پاسخ‌های API](#پاسخهای-api)
6. [کدهای خطا](#کدهای-خطا)

---

## Endpoint

```
GET /api/profile/      (دریافت اطلاعات کاربر فعلی)
POST /api/profile/     (ویرایش اطلاعات)
```

**احراز هویت:** توکن الزامی است
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## فیلدهای قابل ویرایش

### اطلاعات شخصی

| فیلد | نوع | توصیف | مثال |
|-----|------|-------|------|
| `name` | string | نام نمایشی | علی محمدی |
| `email` | string | ایمیل | ali@example.com |
| `phone` | string | شماره تماس | 09123456789 |
| `bio` | string | درباره من | معلم باتجربه و متعهد |
| `gender` | string | جنسیت | male, female, custom, prefer_not_to_say |
| `birth_date` | string | تاریخ تولد (شمسی) | 1403-05-24 |
| `profile_photo_path` | file | عکس پروفایل | JPG, JPEG, PNG, GIF |

### اطلاعات حرفه‌ای

| فیلد | نوع | توصیف | مثال |
|-----|------|-------|------|
| `qualifications` | string | مدارک تحصیلی | کارشناسی ارشد زبان انگلیسی، مدرک TEFL |
| `languages_taught` | string | زبان‌های تدریس‌شده | انگلیسی, فرانسوی |
| `specialization` | string | تخصص | تدریس مکالمه و مهارت‌های تجاری |
| `resume_summary` | string | خلاصه تجربه | 15 سال تجربه تدریس در دبیرستان |
| `experience_years` | integer | سال‌های تجربه | 15 |
| `hourly_rate` | decimal | قیمت ساعتی | 250000 |

### فیلم معرفی

| فیلد | نوع | توصیف | نکته |
|-----|------|-------|------|
| `introduction_video` | file | فایل ویدئوی معرفی | MP4, AVI, MOV, WebM, FLV, MKV, 3GP, M4V, OGV |

---

## نمونه‌های عملی

### ✅ نمونه 1: دریافت اطلاعات پروفایل

**درخواست:**
```bash
curl -X GET https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**پاسخ:**
```json
{
    "success": true,
    "teacher": {
        "username": "ali.teacher",
        "name": "علی محمدی",
        "email": "ali@example.com",
        "phone": "09123456789",
        "bio": "معلم باتجربه",
        "gender": "male",
        "birth_date": "1403-05-24",
        "qualifications": "کارشناسی ارشد",
        "languages_taught": "انگلیسی, فرانسوی",
        "specialization": "تدریس مکالمه",
        "resume_summary": "15 سال تجربه",
        "introduction_video": "/media/videos/intro_123.mp4",
        "hourly_rate": "250000.00",
        "experience_years": 15,
        "is_teacher_verified": true
    }
}
```

---

### ✅ نمونه 2: ویرایش اطلاعات شخصی

**درخواست:**
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "name=علی محمدی&email=ali@example.com&phone=09123456789&gender=male&birth_date=1403-05-24&bio=معلم باتجربه"
```

**یا با cURL form-data:**
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=علی محمدی" \
  -F "email=ali@example.com" \
  -F "phone=09123456789" \
  -F "gender=male" \
  -F "birth_date=1403-05-24" \
  -F "bio=معلم باتجربه"
```

**پاسخ موفق (200 OK):**
```json
{
    "success": true,
    "message": "Teacher profile updated successfully",
    "teacher": {
        "name": "علی محمدی",
        "email": "ali@example.com",
        "phone": "09123456789",
        "bio": "معلم باتجربه",
        "gender": "male",
        "birth_date": "1403-05-24"
    }
}
```

---

### ✅ نمونه 3: ویرایش اطلاعات حرفه‌ای

**درخواست:**
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "qualifications=کارشناسی ارشد زبان انگلیسی، مدرک TEFL" \
  -F "languages_taught=انگلیسی, فرانسوی" \
  -F "specialization=تدریس مکالمه" \
  -F "resume_summary=15 سال تجربه تدریس در دبیرستان و دانشگاه" \
  -F "hourly_rate=250000" \
  -F "experience_years=15"
```

**پاسخ موفق:**
```json
{
    "success": true,
    "message": "Teacher profile updated successfully",
    "teacher": {
        "qualifications": "کارشناسی ارشد زبان انگلیسی، مدرک TEFL",
        "languages_taught": "انگلیسی, فرانسوی",
        "specialization": "تدریس مکالمه",
        "resume_summary": "15 سال تجربه تدریس در دبیرستان و دانشگاه",
        "hourly_rate": "250000.00",
        "experience_years": 15
    }
}
```

---

### ✅ نمونه 4: آپلود فیلم معرفی

**درخواست:**
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=علی محمدی" \
  -F "introduction_video=@/path/to/video.mp4"
```

**پاسخ موفق:**
```json
{
    "success": true,
    "message": "Teacher profile updated successfully",
    "teacher": {
        "name": "علی محمدی",
        "introduction_video": "/media/videos/intro_abc123xyz.mp4"
    }
}
```

---

### ✅ نمونه 5: آپلود عکس پروفایل

**درخواست:**
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=علی محمدی" \
  -F "profile_photo_path=@/path/to/photo.jpg"
```

**پاسخ موفق:**
```json
{
    "success": true,
    "message": "Teacher profile updated successfully",
    "teacher": {
        "name": "علی محمدی",
        "profile_photo_path": "/media/photos/profile_abc123xyz.jpg"
    }
}
```

---

### ✅ نمونه 6: تغییر همه اطلاعات در یک درخواست

**درخواست:**
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=علی محمدی" \
  -F "email=ali@example.com" \
  -F "phone=09123456789" \
  -F "bio=معلم باتجربه و متعهد" \
  -F "gender=male" \
  -F "birth_date=1403-05-24" \
  -F "qualifications=کارشناسی ارشد" \
  -F "languages_taught=انگلیسی, فرانسوی" \
  -F "specialization=تدریس مکالمه" \
  -F "resume_summary=15 سال تجربه" \
  -F "experience_years=15" \
  -F "hourly_rate=250000" \
  -F "introduction_video=@/path/to/video.mp4" \
  -F "profile_photo_path=@/path/to/photo.jpg"
```

---

## حذف فیلم معرفی

برای حذف فیلم معرفی، بفرستید: `introduction_video=null` یا `introduction_video=`

### روش 1: با Form-Data

```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "introduction_video="
```

### روش 2: با URL-Encoded

```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "introduction_video="
```

**پاسخ موفق:**
```json
{
    "success": true,
    "message": "Teacher profile updated successfully",
    "teacher": {
        "introduction_video": null
    }
}
```

---

## حذف عکس پروفایل

برای حذف عکس پروفایل، بفرستید: `profile_photo_path=null` یا `profile_photo_path=`

### روش 1: با Form-Data

```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "profile_photo_path="
```

### روش 2: با URL-Encoded

```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "profile_photo_path="
```

**پاسخ موفق:**
```json
{
    "success": true,
    "message": "Teacher profile updated successfully",
    "teacher": {
        "profile_photo_path": null
    }
}
```

---

## پاسخ‌های API

### ✅ 200 OK - موفق
```json
{
    "success": true,
    "message": "Teacher profile updated successfully",
    "teacher": { ... }
}
```

### ❌ 400 Bad Request - داده نامعتبر

**ایمیل یکی شده:**
```json
{
    "success": false,
    "message": "Invalid data provided",
    "errors": {
        "email": ["This email is already registered."]
    }
}
```

**شماره تماس یکی شده:**
```json
{
    "success": false,
    "message": "Invalid data provided",
    "errors": {
        "phone": ["This phone number is already registered."]
    }
}
```

**تاریخ غلط:**
```json
{
    "success": false,
    "message": "Invalid data provided",
    "errors": {
        "birth_date": ["Birth date must be in YYYY-MM-DD format (Jalali calendar)"]
    }
}
```

### ❌ 401 Unauthorized - بدون احراز هویت
```json
{
    "success": false,
    "message": "Not authenticated"
}
```

---

## کدهای خطا

| کد | معنی | حل |
|----|------|-----|
| 200 | موفق | اطلاعات به‌روز شدند |
| 400 | درخواست نامعتبر | داده‌های ارسالی را بررسی کنید |
| 401 | بدون احراز هویت | توکن را چک کنید یا دوباره وارد شوید |
| 403 | ممنوع | کاربر معلم نیست |
| 405 | روش HTTP اشتباه | از POST یا GET استفاده کنید |

---

## نکات مهم

### 🔐 احراز هویت
- توکن الزامی است
- توکن باید در هدر `Authorization` قرار گیرد
- فرمت: `Authorization: Bearer YOUR_TOKEN`

### ✅ تاریخ شمسی
- فرمت: **YYYY-MM-DD**
- مثال: `1403-05-24` (صحیح)
- ❌ `2024-08-15` (میلادی - غلط)

### 📱 شماره تماس
- فرمت: **09xxxxxxxxx**
- مثال: `09123456789` (صحیح)
- ❌ `9123456789` (بدون 0)
- ❌ `+989123456789` (با کد کشور)

### 👥 جنسیت
- `male` - مرد
- `female` - زن
- `custom` - سایر
- `prefer_not_to_say` - نمی‌خواهم بگویم

### 🎥 فیلم معرفی
- فرمت‌های پشتیبانی: **MP4, AVI, MOV, WebM, FLV, MKV, 3GP, M4V, OGV**
- حداکثر اندازه: **معمولاً 100MB**
- برای حذف: بفرستید `introduction_video=null`

### 📷 عکس پروفایل
- فرمت‌های پشتیبانی: **JPG, JPEG, PNG, GIF**
- حداکثر اندازه: **معمولاً 5MB**
- برای حذف: بفرستید `profile_photo_path=null`

### 📝 نام کاربری
- **نمی‌تواند** تغییر کند
- فقط معلم می‌تواند توسط ادمین تغییر بیابد

### 💰 قیمت ساعتی
- نوع: اعشاری (Decimal)
- مثال: `250000` یا `250000.50`
- واحد: ریال یا واحد پول محلی

---

## مثال کامل: ثبت‌نام و تکمیل پروفایل

### مرحله 1: ورود و دریافت توکن
```bash
curl -X POST https://api.example.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "09123456789", "password": "password123"}'

# پاسخ:
# {
#     "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#     "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
# }
```

### مرحله 2: دریافت پروفایل فعلی
```bash
curl -X GET https://api.example.com/api/profile/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### مرحله 3: ویرایش پروفایل
```bash
curl -X POST https://api.example.com/api/profile/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "name=علی محمدی" \
  -F "email=ali@example.com" \
  -F "phone=09123456789" \
  -F "bio=معلم باتجربه" \
  -F "gender=male" \
  -F "birth_date=1403-05-24" \
  -F "qualifications=کارشناسی ارشد" \
  -F "languages_taught=انگلیسی, فرانسوی" \
  -F "experience_years=15" \
  -F "hourly_rate=250000" \
  -F "introduction_video=@/path/to/video.mp4"
```

### مرحله 4: تایید تکمیل پروفایل
```bash
# دریافت پروفایل برای تایید
curl -X GET https://api.example.com/api/profile/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## قابلیت‌های API

| قابلیت | توضیح |
|--------|-------|
| ✅ GET | دریافت اطلاعات پروفایل فعلی |
| ✅ POST | ویرایش اطلاعات پروفایل |
| ✅ Partial Update | می‌تونید فقط برخی فیلدها رو تغییر بدید |
| ✅ Form-Data | پشتیبانی برای آپلود فیلم |
| ✅ Validation | بررسی خودکار داده‌های ورودی |
| ✅ Unique Check | بررسی عدم تکرار ایمیل و شماره تماس |

---

## مراجع

- **Base URL:** `https://api.example.com`
- **Content-Type:** `application/x-www-form-urlencoded` یا `form-data`
- **Authentication:** Bearer Token (الزامی)
- **Rate Limit:** معمولاً 100 درخواست در ساعت
- **Documentation:** [Swagger/OpenAPI](https://api.example.com/swagger/)

---

**آخرین به‌روزرسانی:** 31 دسامبر 2025
