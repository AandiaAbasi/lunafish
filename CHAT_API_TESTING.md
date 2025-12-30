# Chat API Testing Guide

## Quick Start

سیستم چت رو می‌تونید به ۲ روش تست کنید:

### 1️⃣ استفاده از Management Command (توصیه می‌شود)

```bash
python manage.py test_chat_api
```

این اسکریپت:
- ✅ داده‌های تستی ایجاد می‌کند
- ✅ تمام API endpoints رو تست می‌کند
- ✅ Permissions رو بررسی می‌کند
- ✅ Reactions رو تست می‌کند
- ✅ نتایج رو به صورت خوب‌خوانا نمایش می‌دهد

### 2️⃣ استفاده از Python Script

```bash
python test_chat_api.py
```

---

## مشخصات API

### 📌 Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/<id>/` | دریافت تاریخچه پیام‌ها |
| POST | `/api/chat/<id>/send/` | ارسال پیام |
| POST | `/api/chat/message/<id>/react/` | افزودن واکنش |
| GET | `/api/chat/<id>/participants/` | لیست شرکت‌کنندگان |

### 🔐 Authentication

تمام endpoints نیاز به JWT Token دارند:

```
Authorization: Bearer <token>
```

### 📝 Message Types

- `text` - پیام متنی
- `image` - تصویر
- `video` - ویدیو
- `audio` - صدا
- `pdf` - فایل PDF
- `sticker` - استیکر

### 😊 Reaction Types

- `like` (👍)
- `dislike` (👎)
- `heart` (❤️)
- `clap` (👏)
- `star` (⭐)

---

## مثال‌های استفاده

### 1. دریافت تاریخچه چت

```python
import requests

headers = {'Authorization': f'Bearer {token}'}
response = requests.get('https://api.example.com/api/chat/5/', headers=headers)
messages = response.json()

for msg in messages:
    print(f"{msg['sender_name']}: {msg['text']}")
```

### 2. ارسال پیام

```python
payload = {
    'message_type': 'text',
    'text': 'سلام دوستان!'
}

response = requests.post(
    'https://api.example.com/api/chat/5/send/',
    json=payload,
    headers=headers
)

new_message = response.json()
print(f"Message sent: {new_message['id']}")
```

### 3. افزودن واکنش

```python
payload = {'reaction_type': 'like'}

response = requests.post(
    'https://api.example.com/api/chat/message/1/react/',
    json=payload,
    headers=headers
)

# اگر واکنش قبلاً اضافه شده بود، حذف می‌شود (toggle)
if response.status_code == 201:
    print("Reaction added")
elif response.status_code == 204:
    print("Reaction removed")
```

### 4. لیست شرکت‌کنندگان

```python
response = requests.get(
    'https://api.example.com/api/chat/5/participants/',
    headers=headers
)

participants = response.json()
for p in participants:
    print(f"{p['user_name']} ({p['role']})")
```

---

## نمونه Response

### Chat History Response

```json
[
  {
    "id": 1,
    "chat_room": 5,
    "sender": 10,
    "sender_name": "علی",
    "sender_avatar": "https://cdn.example.com/avatars/10.png",
    "message_type": "text",
    "text": "سلام!",
    "file": null,
    "reactions": [
      {
        "id": 1,
        "user": 11,
        "user_name": "فاطمه",
        "reaction_type": "like",
        "created_at": "2025-01-01T10:30:00Z"
      }
    ],
    "reactions_count": 1,
    "is_deleted": false,
    "created_at": "2025-01-01T10:00:00Z"
  }
]
```

### Send Message Response

```json
{
  "id": 2,
  "chat_room": 5,
  "sender": 10,
  "sender_name": "علی",
  "sender_avatar": "https://cdn.example.com/avatars/10.png",
  "message_type": "text",
  "text": "سلام جواب شما",
  "file": null,
  "reactions": [],
  "reactions_count": 0,
  "is_deleted": false,
  "created_at": "2025-01-01T10:15:00Z"
}
```

---

## خطاهای معمول

### 403 Forbidden
**معنی:** کاربر شرکت‌کننده این چت نیست

**حل:** مطمئن شوید کاربر به عنوان ChatParticipant اضافه شده است

### 404 Not Found
**معنی:** چت یا پیام وجود ندارد

**حل:** ID های صحیح رو بررسی کنید

### 400 Bad Request
**معنی:** داده ارسال شده نادرست است

**حل:** payload رو بررسی کنید (message_type، text، یا file)

---

## مدل‌های داده

### ChatRoom
```
- id (Integer)
- type (CharField: 'support' | 'classroom')
- teaching_subject (OneToOneField, nullable)
- created_at
- updated_at
```

### ChatParticipant
```
- id (Integer)
- chat_room (ForeignKey)
- user (ForeignKey)
- role (CharField: 'teacher' | 'student' | 'admin')
- created_at
- updated_at
```

### Message
```
- id (Integer)
- chat_room (ForeignKey)
- sender (ForeignKey)
- message_type (CharField)
- text (TextField, nullable)
- file (FileField, nullable)
- is_deleted (Boolean)
- created_at
- updated_at
```

### MessageReaction
```
- id (Integer)
- message (ForeignKey)
- user (ForeignKey)
- reaction_type (CharField)
- created_at
- updated_at
```

---

## Admin Interface

مدل‌های چت رو می‌تونید در Django Admin مدیریت کنید:

```
/admin/classroom/chatroom/
/admin/classroom/chatparticipant/
/admin/classroom/message/
/admin/classroom/messagereaction/
```

---

## توسعه آینده

برای پیاده‌سازی real-time messaging:

```bash
# Django Channels نصب کنید
pip install django-channels

# WebSocket consumer اضافه کنید
classroom/consumers.py
```

---

## مشکل‌گیری

اگر مشکلی پیش آمد:

1. **مهاجرت‌ها رو انجام دهید:**
   ```bash
   python manage.py migrate classroom
   ```

2. **داده‌های تستی رو دوباره ایجاد کنید:**
   ```bash
   python manage.py test_chat_api
   ```

3. **Logs رو بررسی کنید:**
   ```bash
   tail -f logs/django.log
   ```

---

## نکات مهم

✅ **Soft Delete فقط:** پیام‌ها حذف نرم هستند (is_deleted = True)

✅ **Permission Checking:** فقط شرکت‌کنندگان می‌تونند پیام بفرستند

✅ **Reaction Toggle:** اگر واکنش اضافه شده باشد، دوباره اضافه کردن آن حذفش می‌کند

✅ **File Upload:** فایل‌ها با تاریخ و فرمت صحیح ذخیره می‌شوند

✅ **Bilingual:** API کامل دوزبانه (انگلیسی/فارسی) است
