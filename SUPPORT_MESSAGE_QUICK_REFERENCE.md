# راهنمای سریع API پیام‌های پشتیبانی | Support Message API Quick Reference

## نقاط انتهایی | Endpoints

### ارسال پیام | Send Message
```
POST /api/support-messages/
Content-Type: multipart/form-data

teacher_id: 5 (required)
sender_id: 5 (required)
message_text: "درخواست کمک" (optional)
attachments: file1.pdf, file2.jpg (optional)
```

### دریافت لیست | Get Messages
```
GET /api/support-messages/?teacher_id=5&status=sent&page=1
```

### علامت‌گذاری خوانده‌شده | Mark as Read
```
PATCH /api/support-messages/1/
```

---

## نمونه درخواست‌های cURL

### ارسال پیام
```bash
curl -X POST http://localhost:8000/api/support-messages/ \
  -H "Authorization: Bearer TOKEN" \
  -F "teacher_id=5" \
  -F "sender_id=5" \
  -F "message_text=درخواست" \
  -F "attachments=@file.pdf"
```

### دریافت لیست
```bash
curl http://localhost:8000/api/support-messages/?teacher_id=5 \
  -H "Authorization: Bearer TOKEN"
```

### علامت‌گذاری خوانده‌شده
```bash
curl -X PATCH http://localhost:8000/api/support-messages/1/ \
  -H "Authorization: Bearer TOKEN"
```

---

## پاسخ‌های نمونه

### 201 Created (ارسال موفق)
```json
{
  "id": 1,
  "teacher_id": 5,
  "sender_id": 5,
  "sender_name": "محمد علی",
  "message_text": "درخواست",
  "status": "sent",
  "created_at": "2024-12-26T14:30:00Z",
  "attachments": [
    {
      "id": 1,
      "file_url": "/media/support_messages/2024/12/file.pdf",
      "file_name": "file.pdf"
    }
  ]
}
```

### 200 OK (لیست پیام‌ها)
```json
{
  "count": 10,
  "next": "/api/support-messages/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## خطاهای رایج

| خطا | سبب | راه حل |
|-----|-----|--------|
| 400 | Message text or attachment is required | حداقل متن یا فایل اضافه کنید |
| 404 | Teacher not found | teacher_id درست است؟ |
| 404 | Sender not found | sender_id درست است؟ |
| 500 | Internal Server Error | لاگ‌های سرور را بررسی کنید |

---

## فیلدهای الزامی | Required Fields

**ارسال پیام:**
- ✅ teacher_id (Integer)
- ✅ sender_id (Integer)
- ⭕ message_text (String) یا attachments (Files) - یک‌ی از دو لازم

**دریافت لیست:**
- ⭕ teacher_id (Query Parameter, optional)
- ⭕ status (Query Parameter, optional)
- ⭕ page (Query Parameter, optional)

---

## کد وضعیت‌ها

| کد | وضعیت |
|----|-------|
| 200 | موفق - GET/PATCH |
| 201 | ایجاد شد - POST |
| 400 | درخواست نامعتبر |
| 404 | یافت نشد |
| 500 | خطای سرور |

---

## پارامترهای فیلتر

```
?teacher_id=5          # پیام‌های معلم 5
?status=sent           # فقط ارسال‌شده
?status=read           # فقط خوانده‌شده
?page=2                # صفحه 2
```

ترکیب: `?teacher_id=5&status=sent&page=1`

---

## مدل‌های داده

### SupportMessage
- id: شناسه یکتا
- teacher_id: معلم دریافت‌کننده
- sender_id: فرستنده (معلم یا ادمین)
- message_text: متن پیام
- status: وضعیت (sent/read)
- read_at: زمان خواندن
- created_at: تاریخ ایجاد

### SupportMessageAttachment
- id: شناسه یکتا
- message: پیام مرتبط
- file: فایل پیوست
- created_at: تاریخ ایجاد

---

## نکات اضافی

1. **صفحه‌بندی**: 10 پیام در هر صفحه
2. **فایل‌های پیوست**: تا 5 فایل در هر پیام (قابل تغییر)
3. **اندازه فایل**: بر اساس تنظیمات سرور
4. **ترجمه‌ها**: دو زبان Farsi و English پشتیبانی‌شده
5. **Admin Panel**: تمام پیام‌ها در Django Admin قابل مشاهده

---

## مستندات کامل

برای مستندات کامل، مراجعه کنید: [SUPPORT_MESSAGE_API.md](SUPPORT_MESSAGE_API.md)
