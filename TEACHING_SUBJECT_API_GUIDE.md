# Teaching Subject (Classroom) API Guide

## Overview
API برای مدیریت موضوعات تدریس (کلاس‌ها) معلمان. این API اجازه می‌دهد:
- ایجاد موضوعات تدریس جدید
- دریافت لیست موضوعات
- ویرایش موضوعات موجود
- حذف موضوعات

---

## Base URL
```
/api/
```

---

## Endpoints

### 1. List & Create Teaching Subjects

#### GET - دریافت لیست موضوعات
```
GET /api/teaching-subjects/
```

**Authentication:** Required (Bearer Token)

**Role Requirements:**
- `teacher`: تنها موضوعات خود را می‌بیند
- `student`: تنها موضوعات فعال را می‌بیند
- `admin`: تمام موضوعات را می‌بیند

**Query Parameters:**
```
?teacher=<teacher_id>        # Filter by teacher ID
?level=<level>               # Filter by level (beginner, intermediate, advanced)
?is_active=<true|false>      # Filter by active status
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/teaching-subjects/?level=beginner" \
  -H "Authorization: Bearer <access_token>"
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "id": 1,
      "teacher": 5,
      "teacher_name": "John Doe",
      "title": "انگلیسی مبتدی - الفبا",
      "description": "یادگیری الفبای انگلیسی برای کودکان",
      "level": "beginner",
      "level_display": "مبتدی",
      "cover_image": "https://example.com/subjects/images/english.jpg",
      "demo_video": "https://example.com/subjects/videos/english-demo.mp4",
      "min_age": 5,
      "max_age": 10,
      "is_active": true,
      "created_at": "2025-01-10T10:30:00Z",
      "updated_at": "2025-01-10T10:30:00Z"
    },
    {
      "id": 2,
      "teacher": 5,
      "teacher_name": "John Doe",
      "title": "انگلیسی متوسط - کالیسه",
      "description": "تحکیم مهارت‌های کالیسه انگلیسی",
      "level": "intermediate",
      "level_display": "متوسط",
      "cover_image": null,
      "demo_video": null,
      "min_age": 10,
      "max_age": 15,
      "is_active": true,
      "created_at": "2025-01-11T14:00:00Z",
      "updated_at": "2025-01-11T14:00:00Z"
    }
  ]
}
```

---

#### POST - ایجاد موضوع تدریس جدید
```
POST /api/teaching-subjects/
```

**Authentication:** Required (Bearer Token)

**Role Requirements:** Only `teacher` role

**Request Body (multipart/form-data):**
```json
{
  "title": "انگلیسی مبتدی - الفبا",
  "description": "یادگیری الفبای انگلیسی برای کودکان",
  "level": "beginner",
  "cover_image": "<image_file>",
  "demo_video": "<video_file>",
  "min_age": 5,
  "max_age": 10,
  "is_active": true
}
```

**Fields Description:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | عنوان موضوع |
| description | text | Yes | توضیح مفصل |
| level | choice | Yes | سطح: `beginner`, `intermediate`, `advanced` |
| cover_image | image | No | عکس کاور |
| demo_video | file | No | فیلم نمونه (MP4, WebM, etc) |
| min_age | integer | No | حداقل سن دانش‌آموز |
| max_age | integer | No | حداکثر سن دانش‌آموز |
| is_active | boolean | No | وضعیت فعال (پیش‌فرض: true) |

**Example Request (cURL):**
```bash
curl -X POST "http://localhost:8000/api/teaching-subjects/" \
  -H "Authorization: Bearer <access_token>" \
  -F "title=انگلیسی مبتدی - الفبا" \
  -F "description=یادگیری الفبای انگلیسی" \
  -F "level=beginner" \
  -F "min_age=5" \
  -F "max_age=10" \
  -F "cover_image=@path/to/image.jpg" \
  -F "demo_video=@path/to/video.mp4"
```

**Example Request (Python/Requests):**
```python
import requests

token = "your_access_token"
headers = {"Authorization": f"Bearer {token}"}

data = {
    "title": "انگلیسی مبتدی - الفبا",
    "description": "یادگیری الفبای انگلیسی برای کودکان",
    "level": "beginner",
    "min_age": 5,
    "max_age": 10,
}

files = {
    "cover_image": open("image.jpg", "rb"),
    "demo_video": open("video.mp4", "rb")
}

response = requests.post(
    "http://localhost:8000/api/teaching-subjects/",
    headers=headers,
    data=data,
    files=files
)
print(response.json())
```

**Response (201 Created):**
```json
{
  "id": 3,
  "teacher": 5,
  "teacher_name": "John Doe",
  "title": "انگلیسی مبتدی - الفبا",
  "description": "یادگیری الفبای انگلیسی برای کودکان",
  "level": "beginner",
  "level_display": "مبتدی",
  "cover_image": "https://example.com/subjects/images/english_1.jpg",
  "demo_video": null,
  "min_age": 5,
  "max_age": 10,
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Error Responses:**

**403 Forbidden (غیر معلم):**
```json
{
  "error": "تنها معلمان می‌توانند موضوع تدریس ایجاد کنند"
}
```

**400 Bad Request (داده نامعتبر):**
```json
{
  "title": ["این فیلد الزامی است"],
  "level": ["انتخاب کنید: beginner, intermediate, advanced"]
}
```

---

### 2. Retrieve Teaching Subject

#### GET - دریافت جزئیات موضوع
```
GET /api/teaching-subjects/{id}/
```

**Parameters:**
| Parameter | Type | Location | Required |
|-----------|------|----------|----------|
| id | integer | path | Yes |

**Authentication:** Required (Bearer Token)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/teaching-subjects/1/" \
  -H "Authorization: Bearer <access_token>"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "teacher": 5,
  "teacher_name": "John Doe",
  "title": "انگلیسی مبتدی - الفبا",
  "description": "یادگیری الفبای انگلیسی برای کودکان",
  "level": "beginner",
  "level_display": "مبتدی",
  "cover_image": "https://example.com/subjects/images/english.jpg",
  "demo_video": "https://example.com/subjects/videos/english-demo.mp4",
  "min_age": 5,
  "max_age": 10,
  "is_active": true,
  "created_at": "2025-01-10T10:30:00Z",
  "updated_at": "2025-01-10T10:30:00Z"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "error": "موضوع تدریسی یافت نشد"
}
```

**403 Forbidden (فقط برای موضوعات غیرفعال):**
```json
{
  "error": "دسترسی محدود است"
}
```

---

### 3. Update Teaching Subject

#### PUT - ویرایش کامل موضوع
```
PUT /api/teaching-subjects/{id}/
```

**Parameters:**
| Parameter | Type | Location | Required |
|-----------|------|----------|----------|
| id | integer | path | Yes |

**Authentication:** Required (Bearer Token)

**Role Requirements:** Owner (معلم) or Admin

**Request Body (multipart/form-data):**
```json
{
  "title": "انگلیسی مبتدی - الفبا و اعداد",
  "description": "یادگیری الفبا و اعداد انگلیسی برای کودکان",
  "level": "beginner",
  "cover_image": "<image_file>",
  "demo_video": "<video_file>",
  "min_age": 4,
  "max_age": 11,
  "is_active": true
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/api/teaching-subjects/1/" \
  -H "Authorization: Bearer <access_token>" \
  -F "title=انگلیسی مبتدی - الفبا و اعداد" \
  -F "description=یادگیری الفبا و اعداد انگلیسی" \
  -F "level=beginner" \
  -F "min_age=4" \
  -F "max_age=11"
```

**Response (200 OK):**
```json
{
  "id": 1,
  "teacher": 5,
  "teacher_name": "John Doe",
  "title": "انگلیسی مبتدی - الفبا و اعداد",
  "description": "یادگیری الفبا و اعداد انگلیسی برای کودکان",
  "level": "beginner",
  "level_display": "مبتدی",
  "cover_image": "https://example.com/subjects/images/english_updated.jpg",
  "demo_video": "https://example.com/subjects/videos/english-demo-v2.mp4",
  "min_age": 4,
  "max_age": 11,
  "is_active": true,
  "created_at": "2025-01-10T10:30:00Z",
  "updated_at": "2025-01-15T14:45:00Z"
}
```

**Error Responses:**

**403 Forbidden (عدم دسترسی):**
```json
{
  "error": "شما دسترسی به ویرایش این موضوع ندارید"
}
```

**404 Not Found:**
```json
{
  "error": "موضوع تدریسی یافت نشد"
}
```

---

#### PATCH - ویرایش جزئی موضوع
```
PATCH /api/teaching-subjects/{id}/
```

**Same as PUT but you only need to include fields you want to update**

**Example Request (تغییر فقط عنوان):**
```bash
curl -X PATCH "http://localhost:8000/api/teaching-subjects/1/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "انگلیسی مبتدی - نسخه ۲"}'
```

**Response (200 OK):** (Same as PUT)

---

### 4. Delete Teaching Subject

#### DELETE - حذف موضوع
```
DELETE /api/teaching-subjects/{id}/
```

**Parameters:**
| Parameter | Type | Location | Required |
|-----------|------|----------|----------|
| id | integer | path | Yes |

**Authentication:** Required (Bearer Token)

**Role Requirements:** Owner (معلم) or Admin

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/teaching-subjects/1/" \
  -H "Authorization: Bearer <access_token>"
```

**Response (204 No Content):**
```
(Empty response body)
```

**Error Responses:**

**403 Forbidden:**
```json
{
  "error": "شما دسترسی به حذف این موضوع ندارید"
}
```

**404 Not Found:**
```json
{
  "error": "موضوع تدریسی یافت نشد"
}
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | درخواست موفق |
| 201 | Created | منبع جدید ایجاد شد |
| 204 | No Content | عملیات موفق بدون محتوا (مثل DELETE) |
| 400 | Bad Request | داده نامعتبر |
| 401 | Unauthorized | احراز هویت نشده |
| 403 | Forbidden | دسترسی ممنوع |
| 404 | Not Found | منبع یافت نشد |
| 500 | Server Error | خطای سرور |

---

## Authentication

تمام درخواست‌ها (به جز احراز هویت و صفحه خانه) نیاز به JWT Bearer Token دارند.

**Header Format:**
```
Authorization: Bearer <your_access_token>
```

**Getting Access Token:**
```bash
# Login with password
curl -X POST "http://localhost:8000/api/login-password/" \
  -H "Content-Type: application/json" \
  -d '{"phone": "09xxxxxxxxx", "password": "your_password"}'

# Response:
{
  "access": "eyJ0eXAiOiJKV1QiLC...",
  "refresh": "eyJ0eXAiOiJKV1QiLC..."
}
```

---

## Role-Based Access

### Teacher (معلم)
- ✅ می‌تواند موضوع ایجاد کند
- ✅ می‌تواند موضوعات خود را دیگر معلمان ببیند
- ✅ می‌تواند موضوعات خود را ویرایش کند
- ✅ می‌تواند موضوعات خود را حذف کند
- ❌ نمی‌تواند موضوعات دیگر معلمان را ویرایش/حذف کند

### Student (دانش‌آموز)
- ✅ می‌تواند تنها موضوعات فعال را ببیند
- ❌ نمی‌تواند موضوع ایجاد کند
- ❌ نمی‌تواند موضوع ویرایش/حذف کند

### Admin (ادمین)
- ✅ می‌تواند تمام موضوعات را ببیند
- ✅ می‌تواند هر موضوعی را ویرایش کند
- ✅ می‌تواند هر موضوعی را حذف کند

---

## Example Workflows

### Workflow 1: معلم ایجاد موضوع جدید

```bash
# 1. Login
TOKEN=$(curl -s -X POST "http://localhost:8000/api/login-password/" \
  -H "Content-Type: application/json" \
  -d '{"phone": "09xxxxxxxxx", "password": "password"}' | jq -r '.access')

# 2. Create subject
curl -X POST "http://localhost:8000/api/teaching-subjects/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=انگلیسی مبتدی" \
  -F "description=کلاس انگلیسی برای کودکان" \
  -F "level=beginner" \
  -F "min_age=5" \
  -F "max_age=10"

# Response: Subject created with ID 1
```

### Workflow 2: معلم موضوع را ویرایش کند

```bash
# Update specific fields
curl -X PATCH "http://localhost:8000/api/teaching-subjects/1/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "انگلیسی مبتدی - نسخه بهتر",
    "min_age": 4
  }'
```

### Workflow 3: دانش‌آموز موضوعات فعال را ببیند

```bash
curl -X GET "http://localhost:8000/api/teaching-subjects/?is_active=true" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```

---

## Notes

1. **Image Upload**: فقط JPG, PNG, GIF قابل قبول است
2. **Video Upload**: فقط MP4, WebM, OGG قابل قبول است (size limit: 500MB)
3. **Age Ranges**: می‌تواند null باشد
4. **Permission Check**: سیستم اتوماتیک teacher ID را از درخواست‌کننده تعیین می‌کند
5. **File Storage**: فایل‌ها در `/subjects/videos/` و `/subjects/images/` ذخیره می‌شوند

