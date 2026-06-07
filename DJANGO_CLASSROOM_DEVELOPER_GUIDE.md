# راهنمای توسعه‌دهنده Django — اضافه کردن کلاس آنلاین به پلتفرم

## خلاصه

این داکیومنت توضیح می‌دهد چگونه اپ `classes` را به پروژه Django موجود اضافه کنید. این اپ کلاس آنلاین با قابلیت‌های چت بلادرنگ، دست بلند کردن، واکنش، تخته‌سفید، و کنترل‌های استاد را فراهم می‌کند.

**پیش‌نیازها:**
- پروژه Django موجود با مدل User (و مدل‌های Teacher/Student)
- Centrifugo مستقر شده (برای realtime)
- Mediasoup/lunafish-rtc (برای صدا/تصویر)

---

## ۱. ساختار فایل‌ها

```
lunafish-control/classes/
├── __init__.py
├── apps.py              # AppConfig
├── conf.py              # تنظیمات قابل پیکربندی
├── models.py            # مدل‌های DB (OnlineClass, ClassEnrollment, HandRaise, ClassMessage, ClassReaction)
├── views.py             # API endpoints (فعلاً dev mode — باید production شود)
├── urls.py              # URL routing
├── serializers.py       # DRF serializers
├── permissions.py       # Permission classes (IsTeacher, IsClassTeacher, etc.)
├── broadcast.py         # ارسال رویداد به Centrifugo
├── signals.py           # Django signals
├── utils.py             # تشخیص نقش کاربر (teacher/student)
├── admin.py             # Django admin
├── migrations/          # Database migrations
└── tests/               # تست‌ها
```

---

## ۲. نصب و پیکربندی

### ۲.۱ اضافه کردن به INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'corsheaders',
    'rest_framework',
    'classes',  # ← اضافه کنید
]
```

### ۲.۲ تنظیمات لازم در settings.py

```python
# --- Centrifugo ---
CENTRIFUGO_TOKEN_SECRET = os.getenv('CENTRIFUGO_TOKEN_SECRET', 'your-secret')
CENTRIFUGO_API_KEY = os.getenv('CENTRIFUGO_API_KEY', 'your-api-key')
CENTRIFUGO_API_URL = os.getenv('CENTRIFUGO_API_URL', 'http://centrifugo:8000/api')
CENTRIFUGO_WS_URL = os.getenv('CENTRIFUGO_WS_URL', 'wss://smartinhub.ir/realtime/connection/websocket')

# --- RTC (Mediasoup) ---
RTC_JWT_SECRET = os.getenv('RTC_JWT_SECRET', 'your-rtc-secret')
RTC_WS_URL = os.getenv('RTC_WS_URL', 'wss://smartinhub.ir/rtc/ws')
RTC_TOKEN_TTL_SECONDS = int(os.getenv('RTC_TOKEN_TTL_SECONDS', '3600'))

# --- تشخیص نقش کاربر (یکی از روش‌های زیر) ---

# روش ۱: فیلد role روی User
CLASSES_USER_ROLE_FIELD = 'role'
CLASSES_TEACHER_ROLE_VALUE = 'teacher'
CLASSES_STUDENT_ROLE_VALUE = 'student'

# روش ۲: مدل‌های جدا
# CLASSES_TEACHER_MODEL = 'your_app.Teacher'
# CLASSES_STUDENT_MODEL = 'your_app.Student'
# CLASSES_TEACHER_USER_FIELD = 'user'
# CLASSES_STUDENT_USER_FIELD = 'user'

# روش ۳: تابع سفارشی
# CLASSES_USER_ROLE_RESOLVER = 'your_app.utils.get_user_role'
```

### ۲.۳ اضافه کردن URLs

```python
# config/urls.py
urlpatterns = [
    # ...
    path('api/v1/classes/', include('classes.urls')),
]
```

### ۲.۴ Migration

```bash
python manage.py makemigrations classes
python manage.py migrate classes
```

---

## ۳. مدل‌ها

### OnlineClass — کلاس آنلاین

```python
class OnlineClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='classes_teaching')
    
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True)
    actual_end = models.DateTimeField(null=True)
    
    room_id = models.UUIDField(default=uuid.uuid4, unique=True)  # برای Mediasoup
    
    max_students = models.IntegerField(default=100)
    allow_student_chat = models.BooleanField(default=True)
    allow_student_reactions = models.BooleanField(default=True)
    require_approval_to_join = models.BooleanField(default=False)
    enable_recording = models.BooleanField(default=False)
    
    status = models.CharField(choices=[
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ], default='scheduled')
```

### ClassEnrollment — ثبت‌نام دانش‌آموز

```python
class ClassEnrollment(models.Model):
    class_session = models.ForeignKey(OnlineClass, related_name='enrollments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='enrolled_classes')
    
    can_unmute = models.BooleanField(default=False)
    can_share_video = models.BooleanField(default=True)
    can_share_screen = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    
    joined_at = models.DateTimeField(null=True)
    left_at = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = ('class_session', 'student')
```

### HandRaise — دست بلند کردن

```python
class HandRaise(models.Model):
    class_session = models.ForeignKey(OnlineClass, related_name='raised_hands')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='hand_raises')
    raised_at = models.DateTimeField(auto_now_add=True)
    lowered_at = models.DateTimeField(null=True)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    acknowledged_at = models.DateTimeField(null=True)
```

### ClassMessage — پیام چت

```python
class ClassMessage(models.Model):
    class_session = models.ForeignKey(OnlineClass, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='class_messages_sent')
    content = models.TextField()
    is_private = models.BooleanField(default=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### ClassReaction — واکنش

```python
class ClassReaction(models.Model):
    EMOJI_CHOICES = [('👍',''), ('❤️',''), ('👏',''), ('🎉',''), ('🤔',''), ('😮','')]
    
    class_session = models.ForeignKey(OnlineClass, related_name='reactions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='class_reactions')
    emoji = models.CharField(max_length=10, choices=EMOJI_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## ۴. Centrifugo — ارسال رویداد

### ۴.۱ broadcast.py — توابع ارسال

```python
# classes/broadcast.py
import requests
from django.conf import settings

def _publish(channel: str, data: dict) -> bool:
    """ارسال به یک کانال Centrifugo"""
    try:
        resp = requests.post(
            settings.CENTRIFUGO_API_URL,
            json={"method": "publish", "params": {"channel": channel, "data": data}},
            headers={
                "Authorization": f"apikey {settings.CENTRIFUGO_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=3,
        )
        return resp.status_code == 200
    except Exception as e:
        logger.warning(f"[Centrifugo] publish failed: {e}")
        return False

def publish_to_class(class_id: str, event: str, data: dict) -> bool:
    """ارسال به تمام شرکت‌کنندگان کلاس"""
    return _publish(f"class:{class_id}", {"event": event, "data": data})

def publish_to_user(user_id: str, event: str, data: dict) -> bool:
    """ارسال به یک کاربر خاص (کانال شخصی)"""
    return _publish(f"$user:{user_id}", {"event": event, "data": data})

def publish_to_class_control(class_id: str, event: str, data: dict) -> bool:
    """ارسال به کانال کنترل استاد"""
    return _publish(f"class:{class_id}:control", {"event": event, "data": data})
```

### ۴.۲ تولید توکن Centrifugo

```python
import jwt
import time
from django.conf import settings

def generate_centrifugo_connection_token(user_id: str, ttl: int = 7200) -> str:
    """توکن اتصال — کاربر با این توکن به Centrifugo وصل می‌شود"""
    now = int(time.time())
    return jwt.encode(
        {"sub": str(user_id), "exp": now + ttl, "iat": now},
        settings.CENTRIFUGO_TOKEN_SECRET,
        algorithm="HS256"
    )

def generate_whiteboard_subscription_token(user_id: str, class_id: str, can_publish: bool = False, ttl: int = 7200) -> str:
    """توکن subscribe تخته‌سفید — با اجازه publish برای استاد"""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "channel": f"whiteboard:class:{class_id}",
        "exp": now + ttl,
        "iat": now,
    }
    if can_publish:
        payload["allow"] = {"publish": True}
    
    return jwt.encode(payload, settings.CENTRIFUGO_TOKEN_SECRET, algorithm="HS256")

def generate_rtc_token(user_id: str, room_id: str, permissions: dict, ttl: int = 3600) -> str:
    """توکن RTC — برای اتصال به Mediasoup"""
    now = int(time.time())
    return jwt.encode(
        {
            "sub": str(user_id),
            "room": str(room_id),
            "permissions": permissions,
            "exp": now + ttl,
            "iat": now,
        },
        settings.RTC_JWT_SECRET,
        algorithm="HS256"
    )
```

---

## ۵. API Endpoints — پیاده‌سازی Production

### ۵.۱ Join — ورود به کلاس

**مهم‌ترین endpoint.** کلاینت وقتی وارد کلاس می‌شود این را فراخوانی می‌کند و تمام توکن‌ها و اطلاعات لازم را دریافت می‌کند.

```python
@action(detail=True, methods=["post"])
def join(self, request, pk=None):
    """
    POST /api/v1/classes/{class_id}/join/
    
    Response باید شامل:
    - class: اطلاعات کلاس
    - rtc: توکن Mediasoup + permissions
    - realtime: توکن Centrifugo + WebSocket URL
    - whiteboard: توکن subscribe تخته‌سفید + canDraw
    - user: اطلاعات کاربر فعلی
    """
    class_instance = self.get_object()
    user = request.user
    
    # بررسی enrollment
    enrollment = ClassEnrollment.objects.filter(
        class_session=class_instance,
        student=user,
        left_at__isnull=True
    ).first()
    
    is_teacher = class_instance.teacher == user
    
    if not is_teacher and not enrollment:
        return Response({"error": "Not enrolled"}, status=403)
    
    # تولید توکن‌ها
    centrifugo_token = generate_centrifugo_connection_token(user.id)
    
    # Permissions بر اساس نقش
    if is_teacher:
        permissions = {
            "consume": True,
            "produceAudio": True,
            "produceVideo": True,
            "produceScreen": True,
            "manageRecording": True,
        }
        can_draw = True
    else:
        permissions = {
            "consume": True,
            "produceAudio": enrollment.can_unmute,
            "produceVideo": enrollment.can_share_video,
            "produceScreen": enrollment.can_share_screen,
            "manageRecording": False,
        }
        can_draw = False  # تا وقتی استاد اجازه بدهد
    
    rtc_token = generate_rtc_token(user.id, class_instance.room_id, permissions)
    wb_token = generate_whiteboard_subscription_token(user.id, str(class_instance.id), can_draw)
    
    # اعلام ورود
    publish_to_class(str(class_instance.id), "participant.joined", {
        "id": str(user.id),
        "user": UserSerializer(user).data,
        "role": "teacher" if is_teacher else "student",
        "isHandRaised": False,
        "isMuted": True,
        "isVideoOn": False,
        ...
    })
    
    # ثبت زمان ورود
    if enrollment:
        enrollment.joined_at = timezone.now()
        enrollment.save(update_fields=['joined_at'])
    
    return Response({
        "class": OnlineClassSerializer(class_instance).data,
        "rtc": {
            "token": rtc_token,
            "wsUrl": settings.RTC_WS_URL,
            "roomId": str(class_instance.room_id),
            "iceServers": settings.RTC_ICE_SERVERS,
            "permissions": permissions,
        },
        "realtime": {
            "token": centrifugo_token,
            "wsUrl": settings.CENTRIFUGO_WS_URL,
            "channels": [
                f"class:{class_instance.id}",
                f"$user:{user.id}"
            ],
        },
        "whiteboard": {
            "subscriptionToken": wb_token,
            "canDraw": can_draw,
        },
        "user": UserSerializer(user).data,
    })
```

### ۵.۲ Chat — ارسال پیام

```python
@action(detail=True, methods=["post"], url_path="messages")
def send_message(self, request, pk=None):
    """
    POST /api/v1/classes/{class_id}/messages/
    Body: { "content": "سلام!" }
    
    ۱. ذخیره در DB
    ۲. Publish به Centrifugo
    ۳. برگرداندن پیام
    """
    class_instance = self.get_object()
    content = request.data.get("content", "").strip()
    
    if not content:
        return Response({"error": "content is required"}, status=400)
    
    # ذخیره
    message = ClassMessage.objects.create(
        class_session=class_instance,
        sender=request.user,
        content=content,
    )
    
    # Publish
    message_data = ClassMessageSerializer(message).data
    publish_to_class(str(class_instance.id), "chat.message", message_data)
    
    return Response(message_data, status=201)
```

### ۵.۳ Hand Raise — دست بلند کردن

```python
@action(detail=True, methods=["post"], url_path="hand/raise")
def raise_hand(self, request, pk=None):
    """POST /api/v1/classes/{class_id}/hand/raise/"""
    class_instance = self.get_object()
    
    # ایجاد یا reuse دست فعلی
    hand, created = HandRaise.objects.get_or_create(
        class_session=class_instance,
        student=request.user,
        lowered_at__isnull=True,
    )
    
    publish_to_class(str(class_instance.id), "hand.raised", {
        "id": str(hand.id),
        "student": UserSerializer(request.user).data,
        "raisedAt": hand.raised_at.isoformat(),
        "isAcknowledged": False,
    })
    
    return Response(HandRaiseSerializer(hand).data)

@action(detail=True, methods=["post"], url_path="hand/lower")
def lower_hand(self, request, pk=None):
    """POST /api/v1/classes/{class_id}/hand/lower/"""
    class_instance = self.get_object()
    
    HandRaise.objects.filter(
        class_session=class_instance,
        student=request.user,
        lowered_at__isnull=True,
    ).update(lowered_at=timezone.now())
    
    publish_to_class(str(class_instance.id), "hand.lowered", {
        "user_id": str(request.user.id)
    })
    
    return Response({"ok": True})
```

### ۵.۴ Reactions — واکنش

```python
@action(detail=True, methods=["post"], url_path="reactions")
def send_reaction(self, request, pk=None):
    """POST /api/v1/classes/{class_id}/reactions/  Body: {"emoji": "👍"}"""
    emoji = request.data.get("emoji", "👍")
    
    # اختیاری: ذخیره (برای آنالیتیکس)
    # ClassReaction.objects.create(...)
    
    # فوری publish — نیازی به ذخیره نیست
    publish_to_class(pk, "reaction.added", {
        "user": UserSerializer(request.user).data,
        "emoji": emoji,
        "timestamp": timezone.now().isoformat(),
    })
    
    return Response({"ok": True})
```

### ۵.۵ Teacher Controls — کنترل‌های استاد

```python
@action(detail=True, methods=["post"], url_path="grant-mic/(?P<user_id>[^/.]+)")
def grant_mic(self, request, pk=None, user_id=None):
    """اجازه صحبت به دانش‌آموز"""
    # بروزرسانی DB
    ClassEnrollment.objects.filter(
        class_session_id=pk, student_id=user_id
    ).update(can_unmute=True)
    
    # اطلاع‌رسانی به دانش‌آموز (کانال شخصی)
    publish_to_user(user_id, "mic.granted", {"class_id": pk})
    
    # اطلاع‌رسانی به همه (برای UI update)
    publish_to_class(pk, "participant.updated", {"user_id": user_id, "canUnmute": True})
    
    return Response({"ok": True})

@action(detail=True, methods=["post"], url_path="revoke-mic/(?P<user_id>[^/.]+)")
def revoke_mic(self, request, pk=None, user_id=None):
    """گرفتن اجازه صحبت"""
    ClassEnrollment.objects.filter(
        class_session_id=pk, student_id=user_id
    ).update(can_unmute=False)
    
    publish_to_user(user_id, "mic.revoked", {"class_id": pk})
    publish_to_class(pk, "participant.updated", {"user_id": user_id, "canUnmute": False})
    
    return Response({"ok": True})

@action(detail=True, methods=["post"], url_path="kick/(?P<user_id>[^/.]+)")
def kick_user(self, request, pk=None, user_id=None):
    """اخراج دانش‌آموز"""
    reason = request.data.get("reason", "")
    
    # بروزرسانی enrollment
    ClassEnrollment.objects.filter(
        class_session_id=pk, student_id=user_id
    ).update(left_at=timezone.now())
    
    publish_to_user(user_id, "kicked", {"class_id": pk, "reason": reason})
    publish_to_class(pk, "participant.left", {"user_id": user_id})
    
    return Response({"ok": True})

@action(detail=True, methods=["post"], url_path="spotlight/(?P<user_id>[^/.]+)")
def spotlight_user(self, request, pk=None, user_id=None):
    """برجسته کردن ویدیوی دانش‌آموز"""
    publish_to_class(pk, "spotlight.changed", {"user_id": user_id})
    publish_to_user(user_id, "spotlight.enabled", {"class_id": pk})
    return Response({"ok": True})
```

### ۵.۶ Whiteboard Permissions — تخته‌سفید

```python
@action(detail=True, methods=["post"], url_path="whiteboard/grant/(?P<user_id>[^/.]+)")
def whiteboard_grant(self, request, pk=None, user_id=None):
    """اجازه نوشتن روی تخته‌سفید"""
    publish_to_user(user_id, "whiteboard.granted", {"class_id": pk})
    publish_to_class(pk, "whiteboard.permission_changed", {"user_id": user_id, "can_draw": True})
    return Response({"ok": True})

@action(detail=True, methods=["post"], url_path="whiteboard/revoke/(?P<user_id>[^/.]+)")
def whiteboard_revoke(self, request, pk=None, user_id=None):
    """گرفتن اجازه تخته‌سفید"""
    publish_to_user(user_id, "whiteboard.revoked", {"class_id": pk})
    publish_to_class(pk, "whiteboard.permission_changed", {"user_id": user_id, "can_draw": False})
    return Response({"ok": True})

@action(detail=True, methods=["post"], url_path="whiteboard/clear")
def whiteboard_clear(self, request, pk=None):
    """پاک کردن تخته‌سفید (فقط استاد)"""
    publish_to_class(pk, "whiteboard.cleared", {})
    return Response({"ok": True})
```

---

## ۶. Centrifugo Configuration

### ۶.۱ config.json (Production)

```json
{
  "engine": "redis",
  "redis_address": "redis:6379",
  "redis_password": "${REDIS_PASSWORD}",
  "redis_db": 3,
  
  "http_stream": true,
  "sse": true,
  
  "presence": true,
  "history_size": 300,
  "history_ttl": "1800s",
  
  "namespaces": [
    {
      "name": "class",
      "presence": true,
      "history_size": 300,
      "history_ttl": "1800s",
      "join_leave": true,
      "force_recovery": true,
      "allow_subscribe_for_client": true
    },
    {
      "name": "whiteboard",
      "presence": true,
      "history_size": 500,
      "history_ttl": "3600s",
      "force_recovery": true,
      "allow_publish_for_subscriber": true,
      "allow_subscribe_for_client": true
    },
    {
      "name": "user",
      "presence": false,
      "history_size": 50,
      "history_ttl": "300s"
    }
  ],
  
  "allowed_origins": ["*"],
  "log_level": "info"
}
```

### ۶.۲ نکات مهم Centrifugo

| تنظیم | توضیح |
|--------|--------|
| `allow_subscribe_for_client: true` | هر کاربر authenticated می‌تواند بدون subscription token به کانال subscribe کند |
| `allow_publish_for_subscriber: true` | (فقط whiteboard) کاربرانی که subscription token با `allow.publish` دارند می‌توانند مستقیماً publish کنند |
| `force_recovery: true` | وقتی کاربر reconnect می‌شود، پیام‌های از دست رفته را دریافت می‌کند |
| `history_size` + `history_ttl` | تعداد و مدت نگهداری پیام‌ها برای recovery |

### ۶.۳ کانال‌ها

| فرمت کانال | نوع | توضیح |
|-------------|------|--------|
| `class:{class_id}` | عمومی | تمام شرکت‌کنندگان — چت، واکنش، دست |
| `whiteboard:class:{class_id}` | عمومی + publish | تخته‌سفید — مستقیم publish توسط کلاینت |
| `$user:{user_id}` | شخصی | رویدادهای خصوصی (mic granted, kicked) |
| `class:{class_id}:control` | خصوصی استاد | کنترل‌های مدیریتی |

**نکته:** کانال‌هایی که با `$` شروع می‌شوند personal channels هستند — فقط صاحب توکن با `sub` مطابق می‌تواند subscribe کند.

---

## ۷. Permission System

### ۷.۱ Permission Classes موجود

```python
from classes.permissions import (
    IsTeacher,              # فقط استاد
    IsStudent,              # فقط دانش‌آموز
    IsClassTeacher,         # فقط استاد این کلاس
    IsEnrolledStudent,      # فقط دانش‌آموز ثبت‌نام‌شده
    IsClassParticipant,     # استاد یا دانش‌آموز ثبت‌نام‌شده
    IsMessageSenderOrClassTeacher,  # برای حذف پیام
)
```

### ۷.۲ تشخیص نقش کاربر

`classes/utils.py` یک سیستم pluggable برای تشخیص نقش ارائه می‌دهد:

```python
from classes.utils import get_user_role, is_teacher, is_student

role = get_user_role(user)  # "teacher" | "student" | None
is_teacher(user)  # True/False
is_student(user)  # True/False
```

بر اساس تنظیمات `settings.py` یکی از ۴ روش را استفاده می‌کند (فیلد، مدل جدا، متد، تابع سفارشی).

---

## ۸. تفاوت نسخه Dev و Production

### نسخه فعلی (Dev)

- بدون Authentication (`AllowAny`)
- کاربران با IP شناسایی می‌شوند (in-memory)
- یک استاد، یک دانش‌آموز per IP
- بدون ذخیره در DB (فقط publish به Centrifugo)
- مناسب تست سریع

### تغییرات لازم برای Production

| موضوع | Dev | Production |
|--------|-----|------------|
| Authentication | `AllowAny` | `IsAuthenticated` + role check |
| شناسایی کاربر | IP-based | `request.user` |
| ذخیره پیام | فقط publish | ذخیره DB + publish |
| ذخیره دست | فقط publish | ذخیره DB + publish |
| توکن RTC | Mock | واقعی (JWT با permissions) |
| Enrollment | Auto | بررسی ثبت‌نام |
| Session tracking | In-memory dict | DB (joined_at/left_at) |
| Error handling | Minimal | کامل + logging |

---

## ۹. الگوی عمومی: هر Action چه کار می‌کند

```
Request → ① بررسی Permission → ② Validate → ③ DB Write → ④ Centrifugo Publish → ⑤ Response
```

مثال:

```python
def send_message(request, class_id):
    # ① Permission: IsAuthenticated + IsClassParticipant
    # ② Validate: content not empty, class is active
    # ③ DB Write: ClassMessage.objects.create(...)
    # ④ Publish: publish_to_class(class_id, "chat.message", serialized_data)
    # ⑤ Response: return serialized message
```

**قانون مهم:** هر عملی که بقیه باید بلادرنگ ببینند → Publish به Centrifugo.

---

## ۱۰. تخته‌سفید — Django فقط اجازه‌ها را مدیریت می‌کند

تخته‌سفید **مستقیم client-to-Centrifugo** است. Django نقشی در relay کردن stroke‌ها ندارد.

```
┌─────────┐                  ┌──────────┐                  ┌─────────┐
│ Client A │ ──── publish ──→ │ Centrifugo│ ──── deliver ──→ │ Client B│
│ (teacher)│      stroke.move │          │      stroke.move │(student)│
└─────────┘                  └──────────┘                  └─────────┘
                                  ↑
                                  │ (Django فقط:)
                                  │ - توکن subscribe + publish تولید می‌کند
                                  │ - grant/revoke اجازه‌ها
                                  │ - clear (اختیاری)
```

Django مسئول:
1. تولید `subscription token` با `allow.publish` (برای استاد)
2. Endpoint `whiteboard/grant/{userId}` — اجازه نوشتن
3. Endpoint `whiteboard/revoke/{userId}` — گرفتن اجازه
4. Endpoint `whiteboard/clear` — پاک کردن (publish event)
5. اختیاری: ذخیره snapshot تخته‌سفید (برای late joiners)

---

## ۱۱. تست Local

### اجرا

```bash
# ۱. Django
cd lunafish-control
source venv/bin/activate
python manage.py runserver 0.0.0.0:8080

# ۲. Centrifugo
centrifugo -c deployment/centrifugo/config.dev.json

# ۳. تست با curl
# ورود به کلاس
curl -X POST http://localhost:8080/api/v1/classes/test-class/join/ \
  -H "Content-Type: application/json" \
  -d '{"role": "teacher"}'

# ارسال پیام
curl -X POST http://localhost:8080/api/v1/classes/test-class/messages/ \
  -H "Content-Type: application/json" \
  -d '{"content": "سلام کلاس!"}'

# دست بلند کردن
curl -X POST http://localhost:8080/api/v1/classes/test-class/hand/raise/

# واکنش
curl -X POST http://localhost:8080/api/v1/classes/test-class/reactions/ \
  -H "Content-Type: application/json" \
  -d '{"emoji": "👍"}'

# اجازه صحبت
curl -X POST http://localhost:8080/api/v1/classes/test-class/grant-mic/student-1/

# ریست
curl -X POST http://localhost:8080/api/v1/classes/reset/
```

### بررسی Centrifugo

```bash
# وضعیت
curl -X POST http://localhost:8002/api \
  -H "Authorization: apikey dev-api-key-lunafish-2026" \
  -H "Content-Type: application/json" \
  -d '{"method": "info"}'
```

---

## ۱۲. Environment Variables (Production)

```bash
# Django
CENTRIFUGO_TOKEN_SECRET=6550ce106802367c5d82c0c6231c403a01987a7e773d1c9986227fbd46352a14
CENTRIFUGO_API_KEY=c909f9a813d13f9c8eec2ca0a381f0b60033fb9be30051649264a5449b961661
CENTRIFUGO_API_URL=http://centrifugo:8000/api
CENTRIFUGO_WS_URL=wss://smartinhub.ir/realtime/connection/websocket
RTC_JWT_SECRET=your-rtc-jwt-secret
RTC_WS_URL=wss://smartinhub.ir/rtc/ws
```

---

## ۱۳. Dependencies

```
# requirements.txt additions
PyJWT>=2.8,<3.0        # تولید توکن Centrifugo و RTC
requests>=2.31,<3.0    # ارسال به Centrifugo API
```

---

## ۱۴. Signals (اختیاری)

اپ `classes` سیگنال‌هایی emit می‌کند که می‌توانید به آن‌ها listen کنید:

```python
from classes.signals import (
    class_started,
    class_ended,
    student_joined,
    student_left,
    hand_raised,
    message_sent,
    mic_granted,
    student_kicked,
)

@receiver(student_joined)
def on_student_joined(sender, class_instance, student, **kwargs):
    # مثلاً: ارسال push notification به استاد
    pass
```

---

## ۱۵. چک‌لیست Production

- [ ] `AllowAny` → `IsAuthenticated` + permission classes مناسب
- [ ] ذخیره پیام‌ها و دست‌ها در DB
- [ ] Rate limiting (واکنش‌ها: max 10/min, پیام: max 30/min)
- [ ] Validate emoji choices
- [ ] بررسی class status (فقط active classes قابل join)
- [ ] بررسی enrollment قبل از join
- [ ] بررسی teacher ownership قبل از teacher actions
- [ ] RTC token واقعی (نه mock)
- [ ] Error handling + logging
- [ ] Test coverage
- [ ] Admin panel configured
- [ ] Celery tasks (اختیاری: cleanup ended classes)

---

## ۱۶. فایل‌های مرجع

| فایل | مسیر | توضیح |
|-------|------|--------|
| Models | `classes/models.py` | مدل‌های کامل (آماده production) |
| Views (dev) | `classes/views.py` | نسخه dev (تغییر لازم) |
| Broadcast | `classes/broadcast.py` | توابع Centrifugo (آماده production) |
| Permissions | `classes/permissions.py` | Permission classes (آماده) |
| Utils | `classes/utils.py` | تشخیص نقش (آماده) |
| Serializers | `classes/serializers.py` | Serializers (آماده) |
| URLs | `classes/urls.py` | URL routing (آماده) |
| Centrifugo config | `deployment/centrifugo/config.dev.json` | نمونه config |
| Settings | `config/settings.py` | تنظیمات Django |

---

## ۱۷. خلاصه فلوی داده

```
┌────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Chat Message]                                                     │
│  Client → POST /messages/ → Django → DB + publish_to_class()       │
│                                         → Centrifugo → All clients │
│                                                                     │
│  [Hand Raise]                                                       │
│  Client → POST /hand/raise/ → Django → DB + publish_to_class()    │
│                                          → Centrifugo → All        │
│                                                                     │
│  [Reaction]                                                         │
│  Client → POST /reactions/ → Django → publish_to_class() (no DB)  │
│                                        → Centrifugo → All          │
│                                                                     │
│  [Grant Mic]                                                        │
│  Teacher → POST /grant-mic/X/ → Django → DB update                │
│                                         → publish_to_user(X)       │
│                                         → publish_to_class()       │
│                                                                     │
│  [Whiteboard Drawing]                                               │
│  Client ───────────────────────→ Centrifugo → All clients          │
│  (direct publish, no Django!)      (whiteboard channel)             │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```
