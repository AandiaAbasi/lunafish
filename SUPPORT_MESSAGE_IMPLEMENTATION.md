# خلاصه اجرای سیستم پیام پشتیبانی | Support Message System Implementation Summary

## نمای کلی | Overview

تاریخ اجرا: ۲۶ دسامبر ۲۰۲۴  
Implementation Date: December 26, 2024

سیستم پیام‌های پشتیبانی امکان ارسال پیام‌ها و فایل‌های پیوست برای معلمان فراهم می‌کند.

---

## اجزای اجرا شده | Implemented Components

### 1. مدل‌های پایگاه داده | Database Models

#### classroom/models.py

**SupportMessage Model:**
- `teacher`: ForeignKey(User, role='teacher')
- `sender`: ForeignKey(User, nullable)
- `message_text`: TextField(nullable)
- `status`: CharField(choices=['sent', 'read'])
- `read_at`: DateTimeField(nullable)
- `mark_as_read()`: روش برای علامت‌گذاری به‌عنوان خوانده‌شده
- Meta: ordering by -created_at, indexed on (teacher, -created_at) and (status, -created_at)

**SupportMessageAttachment Model:**
- `message`: ForeignKey(SupportMessage, related_name='attachments')
- `file`: FileField(upload_to=upload_to_dynamic)
- Meta: verbose_name for Farsi translations

### 2. سریالایزرها | Serializers

#### api/classroom_serializers.py

**SupportMessageAttachmentSerializer**
- Nested serializer for file attachments
- Fields: id, file_url (with absolute URL), file_name

**SupportMessageSerializer**
- Read/Write serializer for support messages
- Fields: id, teacher_id, sender_id, message_text, status, created_at, read_at, attachments

**SupportMessageCreateSerializer**
- Validation serializer for message creation
- Ensures: message_text OR attachments required
- Handles: FileField lists

### 3. دیدها | Views

#### api/views.py

**SupportMessageAPIView**
- POST: Create new message with optional file attachments
  - Validates teacher and sender exist
  - Creates SupportMessageAttachment for each file
  - Returns: message details with attachment URLs
- GET: List messages with filtering
  - Parameters: teacher_id, status, page
  - Pagination: 10 items per page
  - Returns: paginated list with count and next/previous

**SupportMessageDetailAPIView**
- PATCH: Mark message as read
  - Updates status to 'read'
  - Sets read_at timestamp
  - Returns: updated message status

### 4. URLs

#### api/urls.py

```python
path('support-messages/', views.SupportMessageAPIView.as_view(), name='support_messages'),
path('support-messages/<int:message_id>/', views.SupportMessageDetailAPIView.as_view(), name='support_message_detail'),
```

### 5. Admin Integration

#### classroom/admin.py

**SupportMessageAdmin**
- List display: teacher_name, sender_name, status_badge, message_preview, created_at
- Filters: status, created_at, teacher, read_at
- Search: teacher name, sender name, message text
- Inline: SupportMessageAttachmentInline for file management
- Status badge with color coding (green=read, blue=sent)

**SupportMessageAttachmentInline**
- TabularInline for managing attachments
- File preview with download link
- Created_at display

### 6. ترجمه‌ها | Translations

#### locale/fa/LC_MESSAGES/django.po
- Support Message messages (15+ keys)
- کلیدهای: Sent, Read, Message text, Status, Teacher not found, etc.

#### locale/en/LC_MESSAGES/django.po
- English translations for support message system

### 7. مستندات | Documentation

#### SUPPORT_MESSAGE_API.md
- Complete API documentation
- Bilingual (Farsi/English)
- Usage examples: Python, JavaScript, cURL
- Error handling and HTTP status codes
- Database model documentation

---

## جریان استفاده | Usage Flow

### 1. معلم ارسال پیام می‌کند | Teacher Sends Message

```
POST /api/support-messages/
{
  "teacher_id": 5,
  "sender_id": 5,
  "message_text": "درخواست کمک",
  "attachments": [file1, file2]
}
```

Response: 201 Created with message details

### 2. لیست پیام‌ها دریافت می‌کند | Get Messages List

```
GET /api/support-messages/?teacher_id=5&status=sent
```

Response: 200 OK with paginated results

### 3. پیام خوانده شد | Message Marked as Read

```
PATCH /api/support-messages/1/
```

Response: 200 OK with updated status

---

## نکات فنی | Technical Notes

### File Upload Handling
- Uses `upload_to_dynamic` from `core.utils`
- Organized by date: `/support_messages/YYYY/MM/filename`
- Multiple file upload via `request.FILES.getlist('attachments')`

### Parser Configuration
```python
parser_classes = (MultiPartParser, FormParser, JSONParser)
```
Enables: file uploads, form data, JSON requests

### Database Performance
- Indexed on (teacher, -created_at)
- Indexed on (status, -created_at)
- Ordered by -created_at for newest first

### Validation Rules
1. Message text OR attachment required
2. Teacher must have role='teacher'
3. Sender must have role='teacher' or 'admin'
4. Message can be marked read only once

---

## فایل‌های اصلاح شده | Modified Files

| فایل | نوع تغییر | توضیح |
|-----|----------|-------|
| classroom/models.py | ایجاد | SupportMessage + SupportMessageAttachment models |
| api/classroom_serializers.py | ایجاد | 3 serializers for support messages |
| api/views.py | ایجاد | SupportMessageAPIView + SupportMessageDetailAPIView |
| api/urls.py | ایجاد | 2 URL patterns |
| classroom/admin.py | ایجاد | Admin classes + inline |
| locale/fa/LC_MESSAGES/django.po | ایجاد | 70+ translation keys (Farsi) |
| locale/en/LC_MESSAGES/django.po | ایجاد | 70+ translation keys (English) |
| SUPPORT_MESSAGE_API.md | ایجاد | Complete API documentation |

---

## توابع API | API Endpoints

### POST /api/support-messages/
Create new support message with optional file attachments

**Request:** Multipart/Form-Data
- teacher_id (Integer, required)
- sender_id (Integer, required)
- message_text (String, optional)
- attachments (File[], optional)

**Response:** 201 Created
```json
{
  "id": 1,
  "teacher_id": 5,
  "sender_id": 5,
  "sender_name": "محمد علی",
  "message_text": "درخواست کمک",
  "status": "sent",
  "created_at": "2024-12-26T14:30:00Z",
  "attachments": [...]
}
```

### GET /api/support-messages/
List support messages with filtering

**Query Parameters:**
- teacher_id (Integer, optional)
- status (String: 'sent' or 'read', optional)
- page (Integer, optional, default: 1)

**Response:** 200 OK
```json
{
  "count": 25,
  "next": "/api/support-messages/?page=2",
  "previous": null,
  "results": [...]
}
```

### PATCH /api/support-messages/<message_id>/
Mark message as read

**Response:** 200 OK
```json
{
  "id": 1,
  "status": "read",
  "read_at": "2024-12-26T14:35:00Z"
}
```

---

## تست کردن | Testing

### Unit Tests Location
`api/tests.py` - Ready for test cases

### Test Coverage Needed
1. Create support message with text
2. Create support message with attachment
3. Create support message with both text and attachment
4. Fail to create with neither text nor attachment
5. Filter messages by teacher_id
6. Filter messages by status
7. Mark message as read
8. Get message details
9. File attachment URL generation

### Test Command
```bash
python manage.py test api.tests
```

---

## نگاه‌های آینده | Future Enhancements

### Phase 2: Real-time Features
- WebSocket for online/real-time messaging
- Notification system
- Message read receipts
- Typing indicators

### Phase 3: Advanced Features
- Message threads/conversations
- Reply system
- Admin dashboard for support messages
- Analytics on message types
- Auto-response templates

---

## نیازهای سیستمی | System Requirements

- Django 3.2+
- Django REST Framework 3.12+
- Python 3.8+
- jdatetime (for date conversion)
- drf-spectacular (for API documentation)

---

## نتیجه‌گیری | Conclusion

سیستم پیام‌های پشتیبانی با موفقیت پیاده‌سازی شد. معلمان اکنون می‌توانند:

✅ پیام‌های متنی ارسال کنند  
✅ فایل‌های پیوست اضافه کنند  
✅ لیست پیام‌هایشان را مشاهده کنند  
✅ پیام‌ها را به‌عنوان خوانده‌شده علامت‌گذاری کنند  

The support messaging system is now fully implemented. Teachers can:

✅ Send text messages  
✅ Attach files  
✅ View their message history  
✅ Mark messages as read  

---

**تاریخ اتمام:** ۲۶ دسامبر ۲۰۲۴  
**Completion Date:** December 26, 2024
