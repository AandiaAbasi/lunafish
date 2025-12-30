# API پیام‌های پشتیبانی | Support Message API

## نمای کلی | Overview

ماژول پیام‌های پشتیبانی امکان ارسال پیام‌ها و فایل‌های پیوست برای معلمان را فراهم می‌کند.

The Support Message module enables teachers to send messages and file attachments to support team.

---

## نقاط پایانی | Endpoints

### 1. ارسال پیام | Send Message

**URL:** `/api/support-messages/`  
**Method:** `POST`  
**Authentication:** Required

#### درخواست | Request

```bash
curl -X POST http://localhost:8000/api/support-messages/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "teacher_id=5" \
  -F "sender_id=5" \
  -F "message_text=درخواست برای کمک" \
  -F "attachments=@file1.pdf" \
  -F "attachments=@file2.jpg"
```

#### بدنه درخواست | Request Body (Multipart/Form-Data)

| فیلد | نوع | الزامی | توضیح |
|-----|-----|--------|-------|
| teacher_id | Integer | بله | شناسه معلمی که پیام برای او است |
| sender_id | Integer | بله | شناسه فرستنده (معلم یا ادمین) |
| message_text | String | نه | متن پیام (اختیاری اگر فایل پیوست داشته باشد) |
| attachments | File[] | نه | فایل‌های پیوست (اختیاری، چند فایل ممکن) |

#### پاسخ موفقیت | Success Response (201 Created)

```json
{
  "id": 1,
  "teacher_id": 5,
  "sender_id": 5,
  "sender_name": "محمد علی",
  "message_text": "درخواست برای کمک",
  "status": "sent",
  "created_at": "2024-12-26T14:30:00Z",
  "attachments": [
    {
      "id": 1,
      "file_url": "http://localhost:8000/media/support_messages/2024/12/file1.pdf",
      "file_name": "file1.pdf"
    }
  ]
}
```

#### خطاهای ممکن | Possible Errors

| کد | پیام | توضیح |
|----|------|-------|
| 400 | Message text or attachment is required | هیچ متن یا فایلی ارسال نشد |
| 404 | Teacher not found | معلم با این شناسه وجود ندارد |
| 404 | Sender not found | فرستنده با این شناسه وجود ندارد |
| 500 | Internal Server Error | خطای داخلی سرور |

---

### 2. دریافت لیست پیام‌ها | Get Messages List

**URL:** `/api/support-messages/`  
**Method:** `GET`  
**Authentication:** Required

#### پارامترهای Query | Query Parameters

| پارامتر | نوع | توضیح |
|--------|-----|-------|
| teacher_id | Integer | فیلتر پیام‌های یک معلم |
| status | String | فیلتر براساس وضعیت: `sent` یا `read` |
| page | Integer | شماره صفحه (پیش‌فرض: 1) |

#### درخواست نمونه | Example Request

```bash
curl -X GET "http://localhost:8000/api/support-messages/?teacher_id=5&status=sent&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### پاسخ | Response (200 OK)

```json
{
  "count": 25,
  "next": "/api/support-messages/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "teacher_id": 5,
      "sender_id": 5,
      "sender_name": "محمد علی",
      "message_text": "درخواست برای کمک",
      "status": "sent",
      "created_at": "2024-12-26T14:30:00Z",
      "read_at": null,
      "attachments": [
        {
          "id": 1,
          "file_url": "http://localhost:8000/media/support_messages/2024/12/file1.pdf",
          "file_name": "file1.pdf"
        }
      ]
    }
  ]
}
```

---

### 3. علامت‌گذاری پیام به‌عنوان خوانده‌شده | Mark as Read

**URL:** `/api/support-messages/<message_id>/`  
**Method:** `PATCH`  
**Authentication:** Required

#### درخواست نمونه | Example Request

```bash
curl -X PATCH http://localhost:8000/api/support-messages/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### پاسخ | Response (200 OK)

```json
{
  "id": 1,
  "status": "read",
  "read_at": "2024-12-26T14:35:00Z"
}
```

---

## نمونه کدهای استفاده | Usage Examples

### Python (requests)

```python
import requests
from requests.toolbelt.multipart.encoder import MultipartEncoder

url = "http://localhost:8000/api/support-messages/"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

# ارسال پیام با فایل
with open("document.pdf", "rb") as f:
    files = {
        "teacher_id": (None, "5"),
        "sender_id": (None, "5"),
        "message_text": (None, "درخواست برای کمک"),
        "attachments": ("document.pdf", f, "application/pdf")
    }
    response = requests.post(url, headers=headers, files=files)
    print(response.json())

# دریافت لیست
response = requests.get(f"{url}?teacher_id=5", headers=headers)
print(response.json())

# علامت‌گذاری خوانده‌شده
response = requests.patch(f"{url}1/", headers=headers)
print(response.json())
```

### JavaScript (Fetch)

```javascript
const token = "YOUR_TOKEN";

// ارسال پیام با فایل
const formData = new FormData();
formData.append("teacher_id", "5");
formData.append("sender_id", "5");
formData.append("message_text", "درخواست برای کمک");
formData.append("attachments", document.getElementById("fileInput").files[0]);

fetch("/api/support-messages/", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`
  },
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));

// دریافت لیست
fetch("/api/support-messages/?teacher_id=5", {
  headers: {"Authorization": `Bearer ${token}`}
})
.then(res => res.json())
.then(data => console.log(data));

// علامت‌گذاری خوانده‌شده
fetch("/api/support-messages/1/", {
  method: "PATCH",
  headers: {"Authorization": `Bearer ${token}`}
})
.then(res => res.json())
.then(data => console.log(data));
```

### cURL Examples

```bash
# ارسال پیام
curl -X POST http://localhost:8000/api/support-messages/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "teacher_id=5" \
  -F "sender_id=5" \
  -F "message_text=درخواست برای کمک" \
  -F "attachments=@file.pdf"

# دریافت لیست
curl http://localhost:8000/api/support-messages/?teacher_id=5 \
  -H "Authorization: Bearer YOUR_TOKEN"

# علامت‌گذاری خوانده‌شده
curl -X PATCH http://localhost:8000/api/support-messages/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## کدهای وضعیت HTTP | HTTP Status Codes

| کد | معنی |
|----|------|
| 200 | درخواست موفق (GET, PATCH) |
| 201 | منبع ایجاد شد (POST) |
| 400 | درخواست نامعتبر |
| 404 | منبع یافت نشد |
| 500 | خطای سرور |

---

## نکات مهم | Important Notes

1. **حداقل یک متن یا فایل ضروری است**: پیام نمی‌تواند خالی باشد
2. **اندازه فایل**: حداکثر اندازه فایل پیوست بر اساس تنظیمات سرور تعیین می‌شود
3. **اعتبارسنجی معلم**: معلم باید با `role='teacher'` باشد
4. **اعتبارسنجی فرستنده**: فرستنده باید معلم یا ادمین باشد
5. **صفحه‌بندی**: هر صفحه حاوی 10 پیام است

---

## مدل‌های پایگاه داده | Database Models

### SupportMessage
- `id`: Integer (Primary Key)
- `teacher`: ForeignKey (User with role='teacher')
- `sender`: ForeignKey (User, nullable)
- `message_text`: TextField (nullable)
- `status`: CharField ('sent' or 'read')
- `read_at`: DateTimeField (nullable)
- `created_at`: DateTimeField (auto)
- `updated_at`: DateTimeField (auto)

### SupportMessageAttachment
- `id`: Integer (Primary Key)
- `message`: ForeignKey (SupportMessage)
- `file`: FileField
- `created_at`: DateTimeField (auto)
- `updated_at`: DateTimeField (auto)
