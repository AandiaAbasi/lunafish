# راهنمای پیاده‌سازی کلاس آنلاین در React Native

## آدرس‌های Production

| سرویس | آدرس |
|--------|-------|
| Django API | `https://fofofish.app/api/v1/` |
| Centrifugo WS | `wss://fofofish.app/realtime/connection/websocket` |
| Mediasoup WS | `wss://fofofish.app/rtc/ws` |

---

## احراز هویت

تمام درخواست‌ها به جز login نیاز به توکن JWT دارند:

```
Authorization: Bearer <access_token>
```

---

## API کلاس آنلاین

Base URL: `https://fofofish.app/api/v1/classes/`

تمام endpointها نیاز به `IsAuthenticated` دارند.

---

### ۱. لیست کلاس‌ها

```http
GET /api/v1/classes/
```

- استاد: کلاس‌هایی که خودش ساخته
- دانش‌آموز: کلاس‌هایی که در آن‌ها ثبت‌نام شده

**Response:**

```json
[
  {
    "id": "uuid",
    "title": "ریاضی ۱۰۱",
    "description": "...",
    "teacher": {
      "id": 1,
      "username": "teacher1",
      "name": "استاد محمدی",
      "email": "...",
      "phone": "...",
      "role": "teacher",
      "firstName": "استاد محمدی",
      "lastName": ""
    },
    "scheduled_start": "2026-06-10T10:00:00Z",
    "scheduled_end": "2026-06-10T12:00:00Z",
    "actual_start": null,
    "actual_end": null,
    "room_id": "uuid",
    "max_students": 100,
    "allow_student_chat": true,
    "allow_student_reactions": true,
    "require_approval_to_join": false,
    "enable_recording": false,
    "status": "scheduled",
    "enrolled_count": 5,
    "is_full": false,
    "duration_minutes": 120,
    "actual_duration_minutes": 0,
    "created_at": "2026-06-08T10:00:00Z",
    "updated_at": "2026-06-08T10:00:00Z"
  }
]
```

---

### ۲. ساخت کلاس (فقط استاد)

```http
POST /api/v1/classes/
Content-Type: application/json

{
  "title": "ریاضی ۱۰۱",
  "description": "درس اول",
  "scheduled_start": "2026-06-10T10:00:00Z",
  "scheduled_end": "2026-06-10T12:00:00Z",
  "max_students": 50,
  "allow_student_chat": true,
  "allow_student_reactions": true,
  "enable_recording": false
}
```

- `teacher_id` اختیاری — اگر نباشد، کاربر فعلی تنظیم می‌شود

---

### ۳. شروع کلاس (فقط استاد)

```http
POST /api/v1/classes/{class_id}/start/
```

- فقط کلاس‌های `scheduled` قابل شروع هستند
- وضعیت به `active` تغییر می‌کند
- رویداد `class.started` به Centrifugo ارسال می‌شود

---

### ۴. پایان کلاس (فقط استاد)

```http
POST /api/v1/classes/{class_id}/end/
```

- فقط کلاس‌های `active` قابل پایان هستند
- رویداد `class.ended` به Centrifugo ارسال می‌شود

---

### ۵. لغو کلاس (فقط استاد)

```http
POST /api/v1/classes/{class_id}/cancel/
```

---

### ۶. ثبت‌نام دانش‌آموز (فقط استاد)

```http
POST /api/v1/classes/{class_id}/enroll/
Content-Type: application/json

{
  "student_id": 5,
  "can_unmute": false,
  "can_share_video": true,
  "can_share_screen": false,
  "is_moderator": false
}
```

- استاد دانش‌آموزان را ثبت‌نام می‌کند
- رویداد `class.enrolled` به کانال شخصی دانش‌آموز ارسال می‌شود

---

### ۷. ورود به کلاس (JOIN) — مهم‌ترین endpoint

```http
POST /api/v1/classes/{class_id}/join/
```

**شرایط:**
- کلاس باید `active` باشد
- کاربر باید استاد یا دانش‌آموز ثبت‌نام‌شده باشد

**Response:**

```json
{
  "class": {
    "id": "uuid",
    "title": "ریاضی ۱۰۱",
    "description": "...",
    "teacher": { "id": 1, "firstName": "استاد", "lastName": "محمدی", "role": "teacher" },
    "status": "active",
    "settings": {
      "allowStudentChat": true,
      "allowStudentReactions": true,
      "allowStudentVideo": true,
      "enableRecording": false,
      "requireApprovalToJoin": false
    },
    "scheduledStart": "2026-06-10T10:00:00Z",
    "scheduledEnd": "2026-06-10T12:00:00Z",
    "actualStart": "2026-06-10T10:02:00Z",
    "actualEnd": null,
    "roomId": "uuid",
    "enrolledCount": 5,
    "maxStudents": 50
  },
  "rtc": {
    "token": "jwt-for-mediasoup",
    "wsUrl": "wss://fofofish.app/rtc/ws",
    "roomId": "uuid",
    "iceServers": [],
    "permissions": {
      "consume": true,
      "produceAudio": true,
      "produceVideo": true,
      "produceScreen": true,
      "manageRecording": true
    }
  },
  "realtime": {
    "token": "jwt-for-centrifugo",
    "wsUrl": "wss://fofofish.app/realtime/connection/websocket",
    "channels": [
      "class:uuid",
      "$user:1",
      "class:uuid:control"
    ]
  },
  "whiteboard": {
    "subscriptionToken": "jwt-for-whiteboard-channel",
    "channel": "whiteboard:class:uuid",
    "canDraw": true
  },
  "user": {
    "id": 1,
    "firstName": "استاد",
    "lastName": "محمدی",
    "role": "teacher"
  },
  "participants": [
    {
      "id": "1",
      "user": { "id": 1, "firstName": "استاد", "lastName": "محمدی", "role": "teacher" },
      "role": "teacher",
      "isHandRaised": false,
      "isMuted": true,
      "isVideoOn": false,
      "isScreenSharing": false,
      "isSpotlighted": false,
      "canUnmute": true,
      "canShareVideo": true,
      "canShareScreen": true,
      "canDrawOnWhiteboard": true
    }
  ]
}
```

**Permissions بر اساس نقش:**

| فیلد | استاد | دانش‌آموز |
|------|--------|------------|
| `consume` | `true` | `true` |
| `produceAudio` | `true` | `enrollment.can_unmute` |
| `produceVideo` | `true` | `enrollment.can_share_video` |
| `produceScreen` | `true` | `enrollment.can_share_screen` |
| `manageRecording` | `true` | `false` |
| `canDraw` (whiteboard) | `true` | `false` (تا grant شود) |

---

### ۸. خروج از کلاس

```http
POST /api/v1/classes/{class_id}/leave/
```

- رویداد `participant.left` ارسال می‌شود

---

### ۹. چت — ارسال پیام

```http
POST /api/v1/classes/{class_id}/messages/
Content-Type: application/json

{
  "content": "سلام استاد!",
  "is_private": false,
  "recipient_id": null
}
```

- اگر `is_private: true` باشد، `recipient_id` اجباری است
- رویداد `chat.message` به Centrifugo ارسال می‌شود
- اگر `allow_student_chat` غیرفعال باشد، دانش‌آموز نمی‌تواند پیام بفرستد (403)

---

### ۱۰. چت — دریافت تاریخچه

```http
GET /api/v1/classes/{class_id}/messages/?limit=50
```

- پیام‌های خصوصی فقط برای فرستنده، گیرنده، و استاد قابل مشاهده است
- حداکثر 300 پیام (قابل تنظیم)

---

### ۱۱. چت — حذف پیام

```http
DELETE /api/v1/classes/{class_id}/messages/{message_id}/
```

- فرستنده یا استاد می‌تواند حذف کند
- رویداد `chat.deleted` ارسال می‌شود

---

### ۱۲. دست بلند کردن

```http
POST /api/v1/classes/{class_id}/hand/raise/
```

- فقط دانش‌آموز (استاد نمی‌تواند)
- اگر قبلاً دست بلند شده، دوباره ایجاد نمی‌شود
- رویداد `hand.raised` ارسال می‌شود

---

### ۱۳. پایین آوردن دست

```http
POST /api/v1/classes/{class_id}/hand/lower/
```

- رویداد `hand.lowered` ارسال می‌شود

---

### ۱۴. تأیید دست (فقط استاد)

```http
POST /api/v1/classes/{class_id}/hands/{user_id}/acknowledge/
```

- رویداد `hand.acknowledged` ارسال می‌شود

---

### ۱۵. لیست دست‌های بلند شده

```http
GET /api/v1/classes/{class_id}/hands/
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "student": { "id": 5, "firstName": "علی", "lastName": "رضایی", "role": "user" },
      "raisedAt": "2026-06-10T10:15:00Z",
      "loweredAt": null,
      "acknowledgedBy": null,
      "acknowledgedAt": null,
      "isActive": true,
      "isAcknowledged": false,
      "durationSeconds": 45
    }
  ]
}
```

---

### ۱۶. واکنش (ایموجی)

```http
POST /api/v1/classes/{class_id}/reactions/
Content-Type: application/json

{
  "emoji": "👍"
}
```

- ایموجی‌های مجاز: `👍` `❤️` `👏` `🎉` `🤔` `😮`
- محدودیت: حداکثر ۱۰ واکنش در دقیقه (429 Too Many Requests)
- رویداد `reaction.added` ارسال می‌شود

---

### ۱۷. اجازه صحبت (فقط استاد)

```http
POST /api/v1/classes/{class_id}/grant-mic/{user_id}/
```

- `enrollment.can_unmute = True` می‌شود
- رویداد `mic.granted` به کانال شخصی دانش‌آموز ارسال می‌شود
- رویداد `participant.updated` به کانال کلاس ارسال می‌شود

---

### ۱۸. گرفتن اجازه صحبت (فقط استاد)

```http
POST /api/v1/classes/{class_id}/revoke-mic/{user_id}/
```

- `enrollment.can_unmute = False` می‌شود
- رویداد `mic.revoked` ارسال می‌شود

---

### ۱۹. اخراج دانش‌آموز (فقط استاد)

```http
POST /api/v1/classes/{class_id}/kick/{user_id}/
Content-Type: application/json

{
  "reason": "مزاحمت"
}
```

- `enrollment.left_at` تنظیم می‌شود
- رویداد `kicked` به کانال شخصی دانش‌آموز
- رویداد `participant.left` به کانال کلاس

---

### ۲۰. برجسته کردن ویدیو (فقط استاد)

```http
POST /api/v1/classes/{class_id}/spotlight/{user_id}/
```

- رویداد `spotlight.changed` به کانال کلاس
- رویداد `spotlight.enabled` به کانال شخصی

---

### ۲۱. اجازه تخته‌سفید (فقط استاد)

```http
POST /api/v1/classes/{class_id}/whiteboard/grant/{user_id}/
```

- رویداد `whiteboard.granted` به کانال شخصی
- رویداد `whiteboard.permission_changed` به کانال کلاس

---

### ۲۲. گرفتن اجازه تخته‌سفید (فقط استاد)

```http
POST /api/v1/classes/{class_id}/whiteboard/revoke/{user_id}/
```

---

### ۲۳. پاک کردن تخته‌سفید (فقط استاد)

```http
POST /api/v1/classes/{class_id}/whiteboard/clear/
```

- رویداد `whiteboard.cleared` به کانال کلاس

---

### ۲۴. لیست شرکت‌کنندگان

```http
GET /api/v1/classes/{class_id}/participants/
```

**Response:**
```json
{
  "results": [
    {
      "id": "1",
      "user": { "id": 1, "firstName": "استاد", "lastName": "محمدی", "role": "teacher" },
      "role": "teacher",
      "isHandRaised": false,
      "isMuted": true,
      "isVideoOn": false,
      "isScreenSharing": false,
      "isSpotlighted": false,
      "canUnmute": true,
      "canShareVideo": true,
      "canShareScreen": true,
      "canDrawOnWhiteboard": true
    },
    {
      "id": "5",
      "user": { "id": 5, "firstName": "علی", "lastName": "رضایی", "role": "user" },
      "role": "student",
      "isHandRaised": true,
      "isMuted": true,
      "isVideoOn": false,
      "isScreenSharing": false,
      "isSpotlighted": false,
      "canUnmute": false,
      "canShareVideo": true,
      "canShareScreen": false,
      "canDrawOnWhiteboard": false
    }
  ]
}
```

---

### ۲۵. لیست ثبت‌نام‌ها (فقط استاد)

```http
GET /api/v1/classes/{class_id}/enrollments/
```

---

## Centrifugo — رویدادهای بلادرنگ

### اتصال

بعد از join، با `realtime.token` و `realtime.wsUrl` به Centrifugo وصل شوید:

```typescript
import { Centrifuge } from 'centrifuge';

const client = new Centrifuge(joinResponse.realtime.wsUrl, {
  token: joinResponse.realtime.token
});
client.connect();
```

### کانال‌ها

از `realtime.channels` در join response:

| کانال | کی Subscribe شود |
|--------|-------------------|
| `class:{classId}` | همه — چت، واکنش، دست، ورود/خروج |
| `$user:{userId}` | شخصی — mic granted/revoked, kicked, spotlight |
| `class:{classId}:control` | فقط استاد (در channels لیست شده اگر استاد باشید) |

### رویدادهای کانال class

```typescript
subscription.on('publication', (ctx) => {
  const { event, data } = ctx.data;
});
```

| event | data | توضیح |
|-------|------|--------|
| `chat.message` | `{id, sender, content, isPrivate, createdAt}` | پیام جدید |
| `chat.deleted` | `{message_id}` | پیام حذف شد |
| `reaction.added` | `{user, emoji, timestamp}` | واکنش جدید |
| `hand.raised` | `{id, student, raisedAt, isActive, isAcknowledged}` | دست بلند شد |
| `hand.lowered` | `{user_id}` | دست پایین آمد |
| `hand.acknowledged` | `{user_id, acknowledged_by}` | دست تأیید شد |
| `participant.joined` | `{id, user, role, canUnmute, ...}` | کاربر وارد شد |
| `participant.left` | `{user_id}` | کاربر خارج شد |
| `participant.updated` | `{user_id, canUnmute: bool}` | اجازه تغییر کرد |
| `spotlight.changed` | `{user_id}` | ویدیو برجسته شد |
| `class.started` | `{...class data}` | کلاس شروع شد |
| `class.ended` | `{...class data}` | کلاس پایان یافت |
| `whiteboard.permission_changed` | `{user_id, can_draw}` | اجازه تخته‌سفید |
| `whiteboard.cleared` | `{}` | تخته‌سفید پاک شد |

### رویدادهای کانال شخصی ($user:{userId})

| event | data | عمل در UI |
|-------|------|-----------|
| `mic.granted` | `{class_id}` | دکمه unmute فعال شود + نوتیفیکیشن |
| `mic.revoked` | `{class_id}` | فوری mute + نوتیفیکیشن |
| `kicked` | `{class_id, reason}` | خروج اجباری + پیام |
| `spotlight.enabled` | `{class_id}` | نوتیفیکیشن |
| `whiteboard.granted` | `{class_id}` | ابزارهای رسم فعال |
| `whiteboard.revoked` | `{class_id}` | ابزارهای رسم غیرفعال |
| `class.enrolled` | `{class_id}` | کلاس جدید در لیست |

---

## تخته‌سفید — رسم زنده

### Subscribe

با `whiteboard.subscriptionToken` از join response:

```typescript
const sub = client.newSubscription(joinResponse.whiteboard.channel, {
  token: joinResponse.whiteboard.subscriptionToken
});
sub.subscribe();
```

### رویدادها (دریافت از دیگران)

```typescript
sub.on('publication', (ctx) => {
  const event = ctx.data; // event.type = "stroke.start" | "stroke.move" | ...
});
```

| type | payload | توضیح |
|------|---------|--------|
| `stroke.start` | `{strokeId, userId, tool, style, point}` | شروع رسم |
| `stroke.move` | `{strokeId, points: [[x,y],...]}` | ادامه رسم (هر 33ms) |
| `stroke.end` | `{strokeId}` | پایان رسم |
| `undo` | `{userId, targetId}` | بازگردانی |
| `clear` | `{userId}` | پاک کردن همه |
| `cursor` | `{userId, userName, x, y, color}` | مکان‌نمای دیگران |

### Publish (ارسال — فقط اگر canDraw)

```typescript
sub.publish({
  type: "stroke.start",
  strokeId: uuid(),
  userId: currentUser.id,
  tool: "pen",
  style: { color: "#000000", width: 3, opacity: 1 },
  point: [x, y]
});
```

- نقاط را هر **33ms** batch کنید (30 بار/ثانیه)
- از `Ramer-Douglas-Peucker` برای ساده‌سازی نقاط استفاده کنید
- هر stroke یک `strokeId` یکتا دارد

---

## Mediasoup (WebRTC) — صدا و تصویر

### اتصال

با `rtc.token` و `rtc.wsUrl` از join response:

```typescript
const ws = new WebSocket(joinResponse.rtc.wsUrl);
ws.send(JSON.stringify({ type: 'authenticate', token: joinResponse.rtc.token }));
```

### Permissions

بر اساس `rtc.permissions`:

- `consume: true` → می‌تواند صدا/تصویر دیگران را ببیند
- `produceAudio` → اجازه صحبت (استاد همیشه true، دانش‌آموز بعد از grant)
- `produceVideo` → اجازه دوربین
- `produceScreen` → اجازه اشتراک صفحه

---

## فلوی کامل

```
۱. Login → دریافت access_token
۲. GET /classes/ → لیست کلاس‌های قابل ورود
۳. POST /classes/{id}/join/ → دریافت توکن‌ها + شرکت‌کنندگان
۴. Connect Centrifugo → subscribe to channels
۵. Connect Mediasoup → join room, consume/produce
۶. رندر UI
۷. تعاملات:
   - ارسال پیام → POST /messages/ → Centrifugo delivers to all
   - دست بلند → POST /hand/raise/ → Centrifugo delivers
   - واکنش → POST /reactions/ → flying emoji
   - رسم تخته‌سفید → direct publish to Centrifugo (no Django)
۸. POST /classes/{id}/leave/ → خروج
```

---

## خطاهای احتمالی

| HTTP Status | معنی |
|-------------|-------|
| 401 | توکن نامعتبر یا منقضی |
| 403 | اجازه ندارید (مثلاً دانش‌آموز سعی در شروع کلاس) |
| 400 | درخواست نامعتبر (مثلاً join کلاس غیرفعال) |
| 404 | منبع یافت نشد |
| 429 | محدودیت نرخ (واکنش‌ها: max 10/min) |

---

## پکیج‌های مورد نیاز

```json
{
  "centrifuge": "^5.6.0",
  "mediasoup-client": "^3.7.0",
  "react-native-webrtc": "^124.0.0",
  "zustand": "^4.5.0",
  "@shopify/react-native-skia": "latest",
  "react-native-gesture-handler": "^2.x",
  "react-native-reanimated": "^3.x",
  "perfect-freehand": "^1.2.0"
}
```

---

## نکات مهم

1. **توکن Centrifugo** از join API دریافت می‌شود — hardcode نکنید
2. **تخته‌سفید مستقیم publish می‌کند** — بدون عبور از Django
3. **دانش‌آموز بدون اجازه نمی‌تواند:** صحبت کند، اشتراک صفحه بگذارد، روی تخته‌سفید بنویسد
4. **استاد باید ابتدا `start` بزند** — join فقط روی کلاس `active` کار می‌کند
5. **استاد دانش‌آموز را `enroll` می‌کند** — دانش‌آموز خودش نمی‌تواند enroll شود
6. **RTL** — تمام UI باید راست‌چین باشد، فونت شبنم
