# راهنمای پیاده‌سازی کلاس آنلاین در React Native

## خلاصه

این داکیومنت توضیح کامل نحوه پیاده‌سازی UI/UX کلاس آنلاین در اپلیکیشن React Native را ارائه می‌دهد. بک‌اند Django و Centrifugo آماده هستند — فقط باید فرانت React Native متصل شود.

---

## معماری کلی

```
┌──────────────────────────────────────────────────────────┐
│               React Native App                            │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Zustand    │  │  Centrifuge  │  │  Mediasoup     │  │
│  │  Stores     │  │  Client      │  │  Client (RTC)  │  │
│  └─────────────┘  └──────┬───────┘  └───────┬────────┘  │
│                           │                   │           │
│           WebSocket       │       WebSocket   │           │
└───────────────────────────┼───────────────────┼───────────┘
                            │                   │
                            ▼                   ▼
              ┌───────────────────┐   ┌─────────────────┐
              │    Centrifugo     │   │  Mediasoup RTC  │
              │  (رویدادها)       │   │  (صدا/تصویر)   │
              └────────┬──────────┘   └─────────────────┘
                       │
                       │ HTTP publish
                       ▼
              ┌──────────────────────┐
              │   Django Backend     │
              │  (lunafish-control)  │
              └──────────────────────┘
```

### سه سرویس:

| سرویس | نقش | پروتکل |
|--------|------|---------|
| **Django** (`lunafish-control`) | مدیریت کلاس، احراز هویت، اجازه‌ها، ذخیره پیام‌ها | REST API (HTTP) |
| **Centrifugo** | ارسال بلادرنگ رویدادها (چت، واکنش، دست بلند کردن، تخته‌سفید) | WebSocket |
| **Mediasoup** (`lunafish-rtc`) | پخش صدا/تصویر/اشتراک صفحه (WebRTC SFU) | WebSocket + UDP |

---

## فلوی ورود به کلاس

```
کاربر "ورود به کلاس" می‌زند
    │
    ▼
POST /api/v1/classes/{classId}/join/
Body: { "role": "teacher" | "student" }
    │
    ▼ پاسخ شامل:
    │  - اطلاعات کلاس
    │  - توکن Centrifugo + آدرس WebSocket
    │  - توکن RTC + آدرس WebSocket + permissions
    │  - توکن تخته‌سفید + canDraw
    │
    ▼
اتصال به Centrifugo (WebSocket)
    │  - Subscribe به class:{classId}
    │  - Subscribe به whiteboard:class:{classId}
    │
    ▼
اتصال به Mediasoup (WebSocket)
    │  - Join room
    │  - Consume teacher audio/video
    │  - Produce own audio/video (if permitted)
    │
    ▼
نمایش UI کلاس
```

---

## پاسخ Join API

```typescript
// POST /api/v1/classes/{classId}/join/
// Body: { "role": "teacher" }

// Response:
{
  "class": {
    "id": "uuid",
    "title": "ریاضی ۱۰۱",
    "teacher": { "id": "t1", "firstName": "استاد", "lastName": "محمدی", "role": "teacher" },
    "status": "active",
    "settings": {
      "allowStudentChat": true,
      "allowStudentReactions": true,
      "allowStudentVideo": true,
      "enableRecording": false,
      "requireApprovalToJoin": false
    },
    "enrolledCount": 5,
    "maxStudents": 50
  },
  "rtc": {
    "token": "jwt-token-for-mediasoup",
    "wsUrl": "wss://smartinhub.ir/rtc/ws",
    "roomId": "room-uuid",
    "iceServers": [
      { "urls": ["stun:stun.l.google.com:19302"] },
      { "urls": ["turn:..."], "username": "...", "credential": "..." }
    ],
    "permissions": {
      "consume": true,
      "produceAudio": true,       // استاد: true | دانش‌آموز: false (نیاز به اجازه)
      "produceVideo": true,
      "produceScreen": true,      // استاد: true | دانش‌آموز: false
      "manageRecording": true     // فقط استاد
    }
  },
  "realtime": {
    "token": "jwt-token-for-centrifugo",
    "wsUrl": "wss://smartinhub.ir/realtime/connection/websocket",
    "channels": ["class:uuid", "$user:user-id"]
  },
  "whiteboard": {
    "subscriptionToken": "jwt-with-publish-permission",
    "canDraw": true  // استاد: true | دانش‌آموز: false (تا اجازه داده شود)
  },
  "user": {
    "id": "user-id",
    "firstName": "استاد",
    "lastName": "محمدی",
    "role": "teacher"
  }
}
```

---

## API Endpoints کامل

### مدیریت کلاس

| Method | URL | توضیح |
|--------|-----|--------|
| `POST` | `/api/v1/classes/{id}/join/` | ورود به کلاس (دریافت توکن‌ها) |
| `POST` | `/api/v1/classes/{id}/leave/` | خروج از کلاس |
| `POST` | `/api/v1/classes/{id}/start/` | شروع کلاس (فقط استاد) |
| `POST` | `/api/v1/classes/{id}/end/` | پایان کلاس (فقط استاد) |
| `POST` | `/api/v1/classes/reset/` | ریست کردن سشن‌ها (فقط dev) |

### چت

| Method | URL | Body | توضیح |
|--------|-----|------|--------|
| `POST` | `/api/v1/classes/{id}/messages/` | `{ "content": "سلام!" }` | ارسال پیام |
| `DELETE` | `/api/v1/classes/{id}/messages/{msgId}/` | — | حذف پیام (استاد) |

### دست بلند کردن

| Method | URL | توضیح |
|--------|-----|--------|
| `POST` | `/api/v1/classes/{id}/hand/raise/` | بلند کردن دست |
| `POST` | `/api/v1/classes/{id}/hand/lower/` | پایین آوردن دست |
| `GET` | `/api/v1/classes/{id}/hands/` | لیست دست‌های بلند شده |
| `POST` | `/api/v1/classes/{id}/hands/{userId}/acknowledge/` | تأیید دست (استاد) |

### واکنش‌ها

| Method | URL | Body | توضیح |
|--------|-----|------|--------|
| `POST` | `/api/v1/classes/{id}/reactions/` | `{ "emoji": "👍" }` | ارسال واکنش |

ایموجی‌های مجاز: `👍` `❤️` `👏` `🎉` `🤔` `😮`

### کنترل‌های استاد

| Method | URL | توضیح |
|--------|-----|--------|
| `POST` | `/api/v1/classes/{id}/grant-mic/{userId}/` | اجازه صحبت به دانش‌آموز |
| `POST` | `/api/v1/classes/{id}/revoke-mic/{userId}/` | گرفتن اجازه صحبت |
| `POST` | `/api/v1/classes/{id}/kick/{userId}/` | اخراج از کلاس |
| `POST` | `/api/v1/classes/{id}/spotlight/{userId}/` | برجسته کردن ویدیو |
| `POST` | `/api/v1/classes/{id}/whiteboard/grant/{userId}/` | اجازه تخته‌سفید |
| `POST` | `/api/v1/classes/{id}/whiteboard/revoke/{userId}/` | گرفتن اجازه تخته‌سفید |
| `POST` | `/api/v1/classes/{id}/whiteboard/clear/` | پاک کردن تخته‌سفید |

---

## Centrifugo — رویدادهای بلادرنگ

### نحوه اتصال

```typescript
import { Centrifuge } from 'centrifuge';

// دریافت توکن و URL از join API
const { token, wsUrl } = joinResponse.realtime;

const client = new Centrifuge(wsUrl, { token });

client.on('connected', () => console.log('Connected!'));
client.on('disconnected', (ctx) => console.log('Disconnected:', ctx.reason));

client.connect();
```

### کانال‌ها

| کانال | کی Subscribe می‌شه | چه رویدادهایی دریافت می‌شه |
|--------|---------------------|------------------------------|
| `class:{classId}` | همه | چت، واکنش، دست بلند کردن، ورود/خروج شرکت‌کنندگان |
| `whiteboard:class:{classId}` | همه | رویدادهای تخته‌سفید (stroke.start, stroke.move, stroke.end) |
| `$user:{userId}` | شخصی | اجازه میکروفون، اخراج، spotlight |
| `class:{classId}:control` | فقط استاد | رویدادهای مدیریتی |

### رویدادهای کانال class

هر رویداد با این فرمت دریافت می‌شود:

```typescript
subscription.on('publication', (ctx) => {
  const { event, data } = ctx.data;
  // event = "chat.message" | "reaction.added" | "hand.raised" | ...
  // data = payload مربوطه
});
```

#### chat.message
```json
{
  "event": "chat.message",
  "data": {
    "id": "uuid",
    "sender": { "id": "u1", "firstName": "علی", "lastName": "رضایی", "role": "student" },
    "content": "سلام استاد!",
    "isPrivate": false,
    "isDeleted": false,
    "createdAt": "2026-06-07T10:15:00Z"
  }
}
```

#### chat.deleted
```json
{
  "event": "chat.deleted",
  "data": { "message_id": "uuid" }
}
```

#### reaction.added
```json
{
  "event": "reaction.added",
  "data": {
    "user": { "id": "u1", "firstName": "علی", "lastName": "رضایی", "role": "student" },
    "emoji": "👍",
    "timestamp": "2026-06-07T10:15:30Z"
  }
}
```

#### hand.raised
```json
{
  "event": "hand.raised",
  "data": {
    "id": "uuid",
    "student": { "id": "u1", "firstName": "علی", "lastName": "رضایی", "role": "student" },
    "raisedAt": "2026-06-07T10:16:00Z",
    "isAcknowledged": false
  }
}
```

#### hand.lowered
```json
{
  "event": "hand.lowered",
  "data": { "user_id": "u1" }
}
```

#### hand.acknowledged
```json
{
  "event": "hand.acknowledged",
  "data": { "user_id": "u1", "acknowledged_by": { "id": "t1", "firstName": "استاد", ... } }
}
```

#### participant.joined
```json
{
  "event": "participant.joined",
  "data": {
    "id": "u1",
    "user": { "id": "u1", "firstName": "علی", "lastName": "رضایی", "role": "student" },
    "role": "student",
    "isHandRaised": false,
    "isMuted": true,
    "isVideoOn": false,
    "isScreenSharing": false,
    "isSpotlighted": false,
    "canUnmute": false,
    "canShareVideo": true,
    "canShareScreen": false,
    "canDrawOnWhiteboard": false
  }
}
```

#### participant.left
```json
{
  "event": "participant.left",
  "data": { "user_id": "u1" }
}
```

#### spotlight.changed
```json
{
  "event": "spotlight.changed",
  "data": { "user_id": "u1" }
}
```

### رویدادهای کانال شخصی ($user:{userId})

فقط کاربر مربوطه دریافت می‌کند:

#### mic.granted
```json
{ "event": "mic.granted", "data": { "class_id": "uuid" } }
```
→ دکمه unmute فعال شود، نوتیفیکیشن "اجازه صحبت داده شد" نمایش داده شود

#### mic.revoked
```json
{ "event": "mic.revoked", "data": { "class_id": "uuid" } }
```
→ فوری mute شود، نوتیفیکیشن "اجازه صحبت گرفته شد"

#### kicked
```json
{ "event": "kicked", "data": { "class_id": "uuid", "reason": "..." } }
```
→ از کلاس خارج شود، پیام "شما از کلاس اخراج شدید" نمایش داده شود

#### spotlight.enabled
```json
{ "event": "spotlight.enabled", "data": { "class_id": "uuid" } }
```

#### whiteboard.granted
```json
{ "event": "whiteboard.granted", "data": { "class_id": "uuid" } }
```
→ ابزارهای تخته‌سفید فعال شوند

#### whiteboard.revoked
```json
{ "event": "whiteboard.revoked", "data": { "class_id": "uuid" } }
```
→ ابزارهای تخته‌سفید غیرفعال شوند

---

## تخته‌سفید — نحوه کار بلادرنگ

### مفهوم اصلی

تخته‌سفید از **ارسال مستقیم به Centrifugo** استفاده می‌کند (بدون رفتن به Django). کاربرانی که اجازه نوشتن دارند (استاد + دانش‌آموزانی که اجازه گرفته‌اند) می‌توانند مستقیماً به کانال `whiteboard:class:{classId}` publish کنند.

### فلوی رسم زنده

```
انگشت حرکت می‌کند (60 نقطه در ثانیه)
    │
    ▼ هر 33ms (30 بار در ثانیه):
    │  - نقاط جدید جمع‌آوری شده
    │  - ساده‌سازی (Ramer-Douglas-Peucker)
    │  - ارسال به Centrifugo
    │
    ▼ تمام کاربران دریافت می‌کنند (5-15ms تأخیر)
    │
    ▼ هر کاربر نقاط را به path فعال اضافه می‌کند
    │
    ▼ Canvas با 60fps رندر می‌شود
    │
    ═══ خط به صورت زنده روی همه صفحه‌ها ظاهر می‌شود ═══
```

### رویدادهای تخته‌سفید

Subscribe به `whiteboard:class:{classId}`:

```typescript
const sub = client.newSubscription(`whiteboard:class:${classId}`, {
  token: whiteboardSubscriptionToken  // فقط اگر publish نیاز دارید
});

sub.on('publication', (ctx) => {
  const event = ctx.data;
  // event.type = "stroke.start" | "stroke.move" | "stroke.end" | "undo" | "clear" | "cursor"
});

sub.subscribe();
```

#### stroke.start — شروع رسم
```json
{
  "type": "stroke.start",
  "strokeId": "uuid",
  "userId": "u1",
  "tool": "pen",
  "style": { "color": "#FF0000", "width": 3, "opacity": 1 },
  "point": [150, 200]
}
```
→ یک path جدید ایجاد کنید و اولین نقطه را اضافه کنید

#### stroke.move — ادامه رسم (هر 33ms)
```json
{
  "type": "stroke.move",
  "strokeId": "uuid",
  "points": [[152, 203], [155, 207], [160, 212]]
}
```
→ نقاط را به path موجود اضافه کنید و canvas را redraw کنید. **این رویداد بسیار زیاد ارسال می‌شود** — خط به صورت زنده رشد می‌کند

#### stroke.end — پایان رسم
```json
{
  "type": "stroke.end",
  "strokeId": "uuid"
}
```
→ path را نهایی کنید و به لیست strokes تکمیل‌شده منتقل کنید

#### undo — بازگردانی
```json
{
  "type": "undo",
  "userId": "u1",
  "targetId": "stroke-uuid"
}
```
→ stroke مشخص شده را از canvas حذف کنید

#### clear — پاک کردن (فقط استاد)
```json
{
  "type": "clear",
  "userId": "t1"
}
```
→ تمام strokes پاک شوند

#### cursor — موقعیت مکان‌نما (10 بار در ثانیه)
```json
{
  "type": "cursor",
  "userId": "u1",
  "userName": "علی رضایی",
  "x": 150,
  "y": 200,
  "color": "#FF0000"
}
```
→ مکان‌نمای کاربر دیگر را نمایش دهید (نقطه رنگی + اسم)

### ارسال رویداد تخته‌سفید (publish)

```typescript
// فقط وقتی canDraw = true
subscription.publish({
  type: "stroke.start",
  strokeId: generateUUID(),
  userId: currentUser.id,
  tool: "pen",
  style: { color: "#000000", width: 3, opacity: 1 },
  point: [x, y]
});
```

### ابزارهای تخته‌سفید

| ابزار | توضیح |
|--------|--------|
| `pen` | قلم معمولی |
| `highlighter` | هایلایت (نیمه‌شفاف) |
| `eraser` | پاک‌کن |
| `rectangle` | مستطیل |
| `circle` | دایره |
| `arrow` | فلش |
| `line` | خط صاف |
| `text` | متن |
| `laser` | لیزر (خودکار محو می‌شود بعد 2 ثانیه) |
| `select` | انتخاب |

---

## Mediasoup (WebRTC) — صدا و تصویر

### کتابخانه

```bash
npm install mediasoup-client
# یا
yarn add mediasoup-client
```

برای React Native از `react-native-webrtc` یا `react-native-mediasoup-client` استفاده کنید.

### فلوی اتصال

```typescript
import { Device } from 'mediasoup-client';

// 1. اتصال WebSocket به lunafish-rtc
const ws = new WebSocket(joinResponse.rtc.wsUrl);

// 2. ارسال توکن برای احراز هویت
ws.send(JSON.stringify({ type: 'authenticate', token: joinResponse.rtc.token }));

// 3. دریافت routerRtpCapabilities از سرور
// 4. Load device
const device = new Device();
await device.load({ routerRtpCapabilities });

// 5. ساخت transport‌ها
// - sendTransport (برای ارسال صدا/تصویر)
// - recvTransport (برای دریافت صدا/تصویر)

// 6. Produce صدا/تصویر (اگر اجازه دارید)
const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
const audioProducer = await sendTransport.produce({ track: stream.getAudioTracks()[0] });
const videoProducer = await sendTransport.produce({ track: stream.getVideoTracks()[0] });

// 7. Consume صدا/تصویر دیگران
// وقتی سرور اعلام می‌کند producer جدید اضافه شده
const consumer = await recvTransport.consume({ producerId, rtpCapabilities: device.rtpCapabilities });
// consumer.track را به <Video> component بدهید
```

### Permissions بر اساس نقش

| اجازه | استاد | دانش‌آموز |
|--------|--------|------------|
| `consume` (دیدن/شنیدن) | ✅ | ✅ |
| `produceAudio` (صحبت) | ✅ | ❌ (نیاز به اجازه) |
| `produceVideo` (دوربین) | ✅ | ✅ |
| `produceScreen` (اشتراک صفحه) | ✅ | ❌ |
| `manageRecording` (ضبط) | ✅ | ❌ |

وقتی دانش‌آموز رویداد `mic.granted` دریافت می‌کند، `produceAudio` فعال می‌شود و می‌تواند produce کند.

---

## صفحات و UI/UX

### ۱. صفحه لیست کلاس‌ها

```
┌─────────────────────────────────────┐
│  کلاس‌های من                         │
│                                      │
│  ┌─────────────────────────────┐    │
│  │ 📗 ریاضی ۱۰۱              │    │
│  │    استاد محمدی              │    │
│  │    🟢 فعال  |  ۲۴/۵۰ نفر  │    │
│  │    [   ورود به کلاس   ]    │    │
│  └─────────────────────────────┘    │
│                                      │
│  ┌─────────────────────────────┐    │
│  │ 📘 فیزیک پایه             │    │
│  │    دکتر رضایی              │    │
│  │    ⏰ شروع: فردا ۱۰:۰۰    │    │
│  │    [   برنامه‌ریزی شده  ]   │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### ۲. صفحه انتخاب نقش

```
┌─────────────────────────────────────┐
│                                      │
│         ورود به کلاس                 │
│       نقش خود را انتخاب کنید         │
│                                      │
│   ┌──────────┐   ┌──────────┐       │
│   │  🎓      │   │  👨‍🎓     │       │
│   │  استاد   │   │ دانش‌آموز │       │
│   │ مدیریت   │   │  شرکت   │       │
│   │  کلاس   │   │ در کلاس  │       │
│   └──────────┘   └──────────┘       │
│                                      │
└─────────────────────────────────────┘
```

### ۳. صفحه اصلی کلاس (استاد)

```
┌─────────────────────────────────────────────────────────┐
│                    ویدیوی استاد (بزرگ)                    │
│                                                          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                  │
│  │ علی  │ │ مریم │ │ حسین│ │ زهرا │  ← ویدیوی        │
│  │      │ │      │ │      │ │      │    دانش‌آموزان    │
│  └──────┘ └──────┘ └──────┘ └──────┘                  │
│                                                          │
│  ┌──────────────────────────┐  ┌────────────────────┐  │
│  │     تخته‌سفید             │  │     گفتگو         │  │
│  │  (وقتی فعال باشد)       │  │  پیام ۱           │  │
│  │                          │  │  پیام ۲           │  │
│  │                          │  │  ...               │  │
│  │                          │  │  [ارسال پیام...]   │  │
│  └──────────────────────────┘  └────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 🎤  📷  🖥  │  📋  ✋  😀  │  💬  👥  │  🔴 خروج │ │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### ۴. نوار ابزار پایین

| آیکون | عملکرد | استاد | دانش‌آموز |
|--------|---------|--------|------------|
| 🎤 | میکروفون on/off | ✅ | ❌ (نیاز به اجازه) |
| 📷 | دوربین on/off | ✅ | ✅ |
| 🖥 | اشتراک صفحه | ✅ | ❌ |
| 📋 | تخته‌سفید | ✅ | ✅ (فقط مشاهده تا اجازه) |
| ✋ | دست بلند کردن | ❌ | ✅ |
| 😀 | واکنش‌ها | ✅ | ✅ |
| 💬 | گفتگو | ✅ | ✅ |
| 👥 | لیست شرکت‌کنندگان | ✅ | ✅ |
| 🔴 | خروج/پایان کلاس | خروج+پایان | فقط خروج |

### ۵. تخته‌سفید

```
┌─────────────────────────────────────────────────────────┐
│  [🖊 قلم] [✏️ هایلایت] [⬜ پاک‌کن] [◻️ مستطیل]          │
│  [⭕ دایره] [↗️ فلش] [— خط] [T متن]                    │
│  [🎨 رنگ‌ها: ⚫🔴🔵🟢🟡] [ضخامت: ╌ ─ ━]              │
│  [↩️ بازگردانی] [🗑️ پاک کردن همه (استاد)]              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│           ← فضای رسم (Canvas) →                         │
│                                                          │
│    ● علی (نقطه مکان‌نمای کاربر دیگر)                    │
│                                                          │
│           ~~~~~~ (خطی که در حال رسم است) ~~~~            │
│                                                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### ۶. پنل دست‌های بلند شده (برای استاد)

```
┌──────────────────────────┐
│  ✋ دست‌های بلند شده (3)   │
├──────────────────────────┤
│  #1  علی رضایی          │
│      ۲ دقیقه پیش         │
│      [🎤 اجازه] [✓ تأیید]│
├──────────────────────────┤
│  #2  مریم احمدی          │
│      ۱ دقیقه پیش         │
│      [🎤 اجازه] [✓ تأیید]│
├──────────────────────────┤
│  #3  حسین محمدی          │
│      ۳۰ ثانیه پیش       │
│      [🎤 اجازه] [✓ تأیید]│
└──────────────────────────┘
```

### ۷. لیست شرکت‌کنندگان (با کنترل استاد)

```
┌──────────────────────────────────┐
│  شرکت‌کنندگان (15)               │
├──────────────────────────────────┤
│  استاد                           │
│  ┌────────────────────────────┐  │
│  │ 🎓 استاد محمدی  🎤🟢 📷🟢 │  │
│  └────────────────────────────┘  │
│                                   │
│  دانش‌آموزان (14)                 │
│  ┌────────────────────────────┐  │
│  │ 👨‍🎓 علی رضایی   🎤🔴 📷🟢  │  │
│  │         [🎤][📌][📋][❌]   │  │ ← کنترل‌های استاد (hover)
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │ 👩‍🎓 مریم احمدی  🎤🔴 📷🔴  │  │
│  │         [🎤][📌][📋][❌]   │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘

کنترل‌ها:
  🎤 = اجازه/گرفتن صحبت
  📌 = برجسته کردن ویدیو
  📋 = اجازه تخته‌سفید
  ❌ = اخراج از کلاس
```

### ۸. واکنش‌های پرنده

وقتی کسی واکنش می‌فرستد، ایموجی از پایین صفحه به بالا float می‌کند و بعد 3 ثانیه محو می‌شود:

```
                      👍
                 ❤️        👏
            🎉                  🤔
       😮
  ───────────────────────────────────── (نوار پایین)
```

---

## State Management (Zustand)

### ساختار Store‌ها

```typescript
// ۱. ClassroomStore — اطلاعات کلاس و شرکت‌کنندگان
interface ClassroomState {
  classSession: ClassSession | null;
  currentUser: User | null;
  isTeacher: boolean;
  isConnected: boolean;
  participants: Map<string, Participant>;
  handRaiseQueue: HandRaise[];
  myHandIsRaised: boolean;
  flyingReactions: FlyingReaction[];
  myPermissions: MediaPermissions;
  spotlightedUserId: string | null;
}

// ۲. ChatStore — پیام‌ها
interface ChatState {
  messages: ChatMessage[];
  isOpen: boolean;
  unreadCount: number;
  typingUsers: Map<string, User>;
}

// ۳. MediaStore — صدا و تصویر
interface MediaState {
  isMicOn: boolean;
  isCameraOn: boolean;
  isScreenSharing: boolean;
  localStream: MediaStream | null;
  remoteStreams: Map<string, RemoteStream>;
  activeScreenShare: RemoteStream | null;
}

// ۴. WhiteboardStore — تخته‌سفید
interface WhiteboardState {
  activeTool: WhiteboardTool;
  strokeStyle: StrokeStyle;
  canDraw: boolean;
  isWhiteboardOpen: boolean;
  completedStrokes: CompletedStroke[];
  activeStrokes: Map<string, ActiveStroke>;  // در حال رسم
  remoteCursors: Map<string, RemoteCursor>;
}
```

---

## پکیج‌های React Native مورد نیاز

```json
{
  "dependencies": {
    "centrifuge": "^5.6.0",
    "mediasoup-client": "^3.7.0",
    "react-native-webrtc": "^124.0.0",
    "zustand": "^4.5.0",
    "react-native-canvas": "^0.1.0",
    "react-native-gesture-handler": "^2.x",
    "react-native-reanimated": "^3.x",
    "react-native-svg": "^15.x",
    "perfect-freehand": "^1.2.0"
  }
}
```

### توضیح پکیج‌ها:

| پکیج | استفاده |
|--------|---------|
| `centrifuge` | اتصال به Centrifugo (چت، واکنش، تخته‌سفید) |
| `mediasoup-client` | WebRTC SFU client |
| `react-native-webrtc` | WebRTC native bridge |
| `zustand` | State management |
| `react-native-canvas` یا `@shopify/react-native-skia` | رندر تخته‌سفید |
| `react-native-gesture-handler` | تشخیص حرکات (رسم) |
| `react-native-reanimated` | انیمیشن‌ها (واکنش‌های پرنده) |
| `react-native-svg` | رسم شکل‌ها روی تخته‌سفید |
| `perfect-freehand` | صاف کردن خطوط رسم‌شده |

---

## ساختار فایل‌ها (پیشنهادی)

```
app/
├── screens/
│   ├── ClassListScreen.tsx         # لیست کلاس‌ها
│   ├── RoleSelectScreen.tsx        # انتخاب نقش
│   └── ClassroomScreen.tsx         # صفحه اصلی کلاس
│
├── components/classroom/
│   ├── VideoGrid.tsx               # شبکه ویدیوها
│   ├── VideoTile.tsx               # یک ویدیو
│   ├── BottomToolbar.tsx           # نوار ابزار پایین
│   ├── ChatPanel.tsx               # پنل گفتگو
│   ├── ChatMessage.tsx             # یک پیام
│   ├── HandRaiseQueue.tsx          # صف دست‌ها (استاد)
│   ├── ParticipantsList.tsx        # لیست شرکت‌کنندگان
│   ├── FlyingReactions.tsx         # واکنش‌های پرنده
│   └── ReactionPicker.tsx          # انتخاب ایموجی
│
├── components/whiteboard/
│   ├── WhiteboardCanvas.tsx        # Canvas اصلی
│   ├── WhiteboardToolbar.tsx       # ابزارها
│   ├── RemoteCursors.tsx           # مکان‌نماهای دیگران
│   └── StrokeRenderer.tsx          # رندر یک stroke
│
├── services/
│   ├── centrifugoService.ts        # اتصال و مدیریت Centrifugo
│   ├── mediaService.ts             # مدیریت Mediasoup/WebRTC
│   └── classroomApi.ts             # تمام API calls
│
├── stores/
│   ├── classroomStore.ts           # State کلاس
│   ├── chatStore.ts                # State چت
│   ├── mediaStore.ts               # State صدا/تصویر
│   └── whiteboardStore.ts          # State تخته‌سفید
│
├── hooks/
│   ├── useClassroomEvents.ts       # هندل رویدادهای Centrifugo
│   ├── useWhiteboard.ts            # لاجیک رسم + ارسال
│   └── useMediaControls.ts         # کنترل میکروفون/دوربین
│
└── types/
    └── classroom.ts                # تمام TypeScript types
```

---

## نکات مهم پیاده‌سازی

### ۱. تخته‌سفید — عملکرد

- از `@shopify/react-native-skia` استفاده کنید (بهترین عملکرد برای Canvas در RN)
- نقاط را هر ۳۳ میلی‌ثانیه batch کنید (۳۰ بار در ثانیه)
- قبل از ارسال، نقاط را با الگوریتم Ramer-Douglas-Peucker ساده کنید
- از `perfect-freehand` برای صاف کردن خطوط استفاده کنید
- رندر را با `requestAnimationFrame` یا Skia animation loop انجام دهید

### ۲. تأخیر و بهینه‌سازی

- تأخیر Centrifugo: **5-15ms** (WebSocket)
- تأخیر Mediasoup: **50-150ms** (WebRTC)
- Batch ارسال نقاط: هر **33ms** (۳۰ batch/ثانیه)
- Throttle مکان‌نما: هر **100ms** (۱۰ بار/ثانیه)
- پهنای باند تخته‌سفید: **~1.5 KB/ثانیه** per drawer

### ۳. امنیت

- هر API call باید توکن JWT داشته باشد: `Authorization: Bearer {token}`
- توکن Centrifugo از Django دریافت می‌شود (نه hardcode)
- توکن تخته‌سفید permission مشخص دارد (publish یا فقط subscribe)
- تمام WebSocket‌ها باید `wss://` باشند (production)

### ۴. اتصال مجدد

- Centrifugo: خودکار reconnect + recovery (پیام‌های از دست رفته دریافت می‌شوند)
- Mediasoup: باید دستی reconnect پیاده‌سازی شود
- Django API: retry با exponential backoff

### ۵. RTL

- تمام UI باید RTL باشد (فارسی)
- از فونت Shabnam استفاده شود
- اعداد LTR بمانند (شماره‌ها، ساعت)
- آیکون‌هایی که جهت دارند (فلش، ارسال) باید flip شوند

---

## آدرس‌های production

| سرویس | آدرس |
|--------|-------|
| Django API | `https://smartinhub.ir/api/v1/` |
| Centrifugo WS | `wss://smartinhub.ir/realtime/connection/websocket` |
| Mediasoup WS | `wss://smartinhub.ir/rtc/ws` |

---

## آدرس‌های local dev

| سرویس | آدرس |
|--------|-------|
| Django API | `http://192.168.x.x:8080/api/v1/` |
| Centrifugo WS | `ws://192.168.x.x:8002/connection/websocket` |
| Mediasoup WS | `ws://192.168.x.x:3001/rtc/ws` |

---

## چک‌لیست پیاده‌سازی

### فاز ۱: اتصال پایه
- [ ] صفحه لیست کلاس‌ها
- [ ] صفحه انتخاب نقش
- [ ] اتصال به Django join API
- [ ] اتصال به Centrifugo
- [ ] Subscribe به کانال class
- [ ] نمایش UI اولیه کلاس

### فاز ۲: چت و تعاملات
- [ ] ارسال و دریافت پیام چت
- [ ] دست بلند کردن
- [ ] واکنش‌ها (ایموجی پرنده)
- [ ] لیست شرکت‌کنندگان
- [ ] نوتیفیکیشن‌ها (mic granted, kicked, etc.)

### فاز ۳: تخته‌سفید
- [ ] Canvas با Skia
- [ ] رسم محلی (touch → points)
- [ ] ارسال نقاط به Centrifugo (batch/throttle)
- [ ] دریافت و رندر نقاط دیگران (live)
- [ ] ابزارها (pen, highlighter, eraser)
- [ ] رنگ و ضخامت
- [ ] Undo/Clear
- [ ] مکان‌نمای دیگران

### فاز ۴: صدا و تصویر
- [ ] اتصال به Mediasoup
- [ ] Produce صدا/تصویر
- [ ] Consume صدا/تصویر دیگران
- [ ] Grid ویدیوها
- [ ] اشتراک صفحه
- [ ] Spotlight

### فاز ۵: کنترل‌های استاد
- [ ] اجازه/گرفتن صحبت
- [ ] اخراج
- [ ] برجسته کردن
- [ ] اجازه تخته‌سفید
- [ ] پایان کلاس

### فاز ۶: پیشرفته
- [ ] ضبط کلاس
- [ ] نظرسنجی
- [ ] اتاق‌های جداگانه (breakout rooms)
- [ ] حضور و غیاب
- [ ] آنالیتیکس

---

## تست

### تست محلی

1. Django را اجرا کنید: `venv/bin/python manage.py runserver 0.0.0.0:8080`
2. Centrifugo را اجرا کنید: `centrifugo -c deployment/centrifugo/config.dev.json`
3. اپ را روی دو دستگاه مختلف اجرا کنید
4. یکی teacher و یکی student وارد شوند
5. تست: چت ارسال کنید → هر دو ببینند
6. تست: دست بلند کنید → استاد ببیند
7. تست: روی تخته‌سفید بکشید → هر دو ببینند

### تست با سرور production

- فقط آدرس‌ها را به `smartinhub.ir` تغییر دهید
- توکن واقعی از login API بگیرید

---

## سوالات متداول

**Q: چرا از Centrifugo استفاده می‌کنیم و نه Socket.IO?**
A: Centrifugo بسیار بهینه‌تر است (Go binary, 100k+ concurrent)، history/recovery دارد، و از قبل روی سرور مستقر است.

**Q: چرا تخته‌سفید مستقیم به Centrifugo publish می‌کند؟**
A: برای حداقل تأخیر. اگر هر نقطه از Django رد شود، ۲۰-۵۰ms اضافه تأخیر دارد که رسم را غیرطبیعی می‌کند.

**Q: اگر کاربر وسط رسم disconnect شد چه؟**
A: Centrifugo history recovery. وقتی reconnect می‌شود، رویدادهای از دست رفته را دریافت می‌کند.

**Q: محدودیت تعداد دانش‌آموز؟**
A: Centrifugo: 100k+. Mediasoup: 500-1000 (video). عملاً محدودیت از سمت ویدیو است.

**Q: آیا پیام‌ها ذخیره می‌شوند؟**
A: بله، Django هر پیام را در DB ذخیره می‌کند و همزمان به Centrifugo publish می‌کند.
