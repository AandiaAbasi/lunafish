# 🚀 راهنمای کامل استفاده از Skyroom API - گام به گام

> این فایل توضیح می‌دهد چگونه Skyroom API را استفاده کنید و چه ترتیبی باید API ها را فراخوانی کنید.

## 📌 فهرست مطالب
1. [مقدمه](#مقدمه)
2. [احراز هویت](#احراز-هویت)
3. [ترتیب صحیح اجرای API ها](#ترتیب-صحیح-اجرای-api-ها)
4. [هر API به تفصیل](#هر-api-به-تفصیل)
5. [سناریوهای واقعی](#سناریوهای-واقعی)
6. [نکات مهم](#نکات-مهم)

---

## مقدمه

Skyroom API برای مدیریت **سرویس‌ها**، **اتاق‌های مجازی**، **کاربران** و **لینک‌های ورود سریع** طراحی شده است.

### مثال: یک دوره آنلاین ایجاد کنید
```
1. سرویس ایجاد کنید (حد کاربران و ویدیو را مشخص کنید)
   ↓
2. اتاق ایجاد کنید (برای هر درس یک اتاق)
   ↓
3. کاربر‌های استاد و دانشجو ایجاد کنید
   ↓
4. کاربران را به اتاق‌ها اضافه کنید
   ↓
5. لینک‌های ورود سریع تولید کنید (برای میهمان‌ها)
```

---

## احراز هویت

تمام درخواست‌ها به API Key نیاز دارند:

```bash
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  https://fofofish.app/api/skyroom/services/
```

---

## ترتیب صحیح اجرای API ها

### 📊 نمودار جریان

```
┌─────────────────────────────────────────────────────┐
│          1️⃣ سرویس ایجاد کنید                        │
│   (Create Service - مانند بسته آموزشی)             │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│     2️⃣ اتاق‌های مجازی ایجاد کنید                    │
│   (Create Rooms - یک اتاق برای هر کلاس)            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│          3️⃣ کاربران ایجاد کنید                      │
│   (Create Users - استادها و دانشجوها)             │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│      4️⃣ کاربران را به اتاق‌ها اضافه کنید           │
│   (Add Users to Rooms - تخصیص نقش‌ها)            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│       5️⃣ لینک‌های ورود سریع تولید کنید             │
│   (Generate Login URLs - برای دسترسی فوری)       │
└─────────────────────────────────────────────────────┘
```

---

## هر API به تفصیل

### 1️⃣ سرویس (Service)

#### 📝 توضیح
سرویس مانند **بسته‌های آموزشی** است. هر سرویس:
- حد تعداد کاربران
- حد تعداد ویدیو
- مدت زمان استفاده

#### 🎯 برای چه کاری
- تعریف اشتراک‌های مختلف (عادی، پریمیوم، حرفه‌ای)
- کنترل منابع (چند نفر می‌تونن همزمان وصل شوند)

#### 🔧 ایجاد سرویس

```bash
curl -X POST "https://fofofish.app/api/skyroom/services/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 1,
    "title": "بسته استاندارد",
    "status": 1,
    "user_limit": 100,
    "video_limit": 8,
    "time_limit": 1000000,
    "start_time": 1609459200,
    "stop_time": 1640995200
  }'
```

**پاسخ:**
```json
{
  "id": 1,
  "skyroom_id": 1,
  "title": "بسته استاندارد",
  "status": 1,
  "user_limit": 100,
  "video_limit": 8
}
```

#### 🔍 دریافت تمام سرویس‌ها

```bash
curl -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  "https://fofofish.app/api/skyroom/services/"
```

#### 📋 تمام API های سرویس

| عملیات | روش | مسیر | توضیح |
|--------|------|------|--------|
| دریافت تمام | GET | `/skyroom/services/` | لیست تمام سرویس‌ها |
| دریافت یکی | GET | `/skyroom/services/1/` | جزئیات سرویس شماره 1 |
| ایجاد | POST | `/skyroom/services/` | سرویس جدید |
| ویرایش | PUT | `/skyroom/services/1/` | ویرایش سرویس 1 |
| حذف | DELETE | `/skyroom/services/1/` | حذف سرویس 1 |

---

### 2️⃣ اتاق (Room)

#### 📝 توضیح
اتاق **کلاس یا جلسه‌ی مجازی** است. هر اتاق:
- به یک سرویس تعلق دارد
- نام لاتینی و عنوان فارسی دارد
- تنظیمات مهمان‌ها و کاربران را دارد

#### 🎯 برای چه کاری
- ایجاد کلاس‌های متفاوت برای دروس مختلف
- کنترل دسترسی (مهمان‌ها می‌تونند وارد شوند یا نه)
- محدود کردن حداکثر شرکت‌کنندگان

#### 🔧 ایجاد اتاق

```bash
curl -X POST "https://fofofish.app/api/skyroom/rooms/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 1,
    "service": 1,
    "name": "python-lesson-1",
    "title": "درس Python - بخش اول",
    "description": "آموزش مقدمات Python",
    "status": 1,
    "guest_login": true,
    "guest_limit": 50,
    "op_login_first": true,
    "max_users": 100,
    "session_duration": 3600
  }'
```

**نکات مهم:**
- `name`: نام انگلیسی (بدون فاصله)
- `title`: عنوان فارسی
- `guest_login`: آیا مهمان‌ها می‌توانند بدون کاربر وارد شوند
- `op_login_first`: اپراتور باید اول وارد شود

#### 📋 تمام API های اتاق

| عملیات | روش | مسیر | توضیح |
|--------|------|------|--------|
| دریافت تمام | GET | `/skyroom/rooms/` | لیست تمام اتاق‌ها |
| دریافت یکی | GET | `/skyroom/rooms/1/` | جزئیات اتاق 1 |
| ایجاد | POST | `/skyroom/rooms/` | اتاق جدید |
| ویرایش | PUT | `/skyroom/rooms/1/` | ویرایش اتاق 1 |
| حذف | DELETE | `/skyroom/rooms/1/` | حذف اتاق 1 |
| دریافت کاربران | GET | `/skyroom/rooms/1/users/` | کاربران اتاق 1 |
| اضافه کردن کاربران | POST | `/skyroom/rooms/1/add_users/` | اضافه کردن کاربر |
| حذف کاربران | POST | `/skyroom/rooms/1/remove_users/` | حذف کاربر از اتاق |

---

### 3️⃣ کاربر (User)

#### 📝 توضیح
کاربر **استاد یا دانشجو** است. هر کاربر:
- نام کاربری و رمز عبور دارد
- ایمیل و اطلاعات شخصی دارد
- می‌تواند به چند اتاق دسترسی داشته باشد

#### 🎯 برای چه کاری
- ثبت‌نام استادها و دانشجوها
- کنترل سطح دسترسی (عادی، ارایه‌کننده، اپراتور)
- ردیابی استفاده از سیستم

#### 🔧 ایجاد کاربر

```bash
curl -X POST "https://fofofish.app/api/skyroom/users/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 1,
    "username": "ali_teacher",
    "nickname": "علی معلم",
    "password": "secure_password_123",
    "email": "ali@example.com",
    "fname": "علی",
    "lname": "موسوی",
    "gender": 1,
    "status": 1,
    "is_public": false
  }'
```

**نکات مهم:**
- `username`: نام کاربری انگلیسی (بدون فاصله)
- `password`: رمز عبور (حداکثر 24 کاراکتر)
- `gender`: 0=نامعلوم، 1=مرد، 2=زن
- `is_public`: برای حسابهای عمومی (مهمان‌ها)

#### 📋 تمام API های کاربر

| عملیات | روش | مسیر | توضیح |
|--------|------|------|--------|
| دریافت تمام | GET | `/skyroom/users/` | لیست تمام کاربران |
| دریافت یکی | GET | `/skyroom/users/1/` | جزئیات کاربر 1 |
| ایجاد | POST | `/skyroom/users/` | کاربر جدید |
| ویرایش | PUT | `/skyroom/users/1/` | ویرایش کاربر 1 |
| حذف | DELETE | `/skyroom/users/1/` | حذف کاربر 1 |
| دریافت اتاق‌ها | GET | `/skyroom/users/1/rooms/` | اتاق‌های کاربر 1 |
| اضافه کردن به اتاق | POST | `/skyroom/users/1/add_rooms/` | اضافه کردن به اتاق |
| حذف از اتاق | POST | `/skyroom/users/1/remove_rooms/` | حذف از اتاق |

---

### 4️⃣ دسترسی اتاق (Room User Access)

#### 📝 توضیح
نوع دسترسی کاربر به اتاق **سطح نقش** را مشخص می‌کند:
- `1`: کاربر عادی (مشاهده‌کننده)
- `2`: ارایه‌کننده (می‌تواند صفحه نمایش را اشتراک گذاری کند)
- `3`: اپراتور (کنترل کامل)

#### 🎯 برای چه کاری
- تعیین سطح دسترسی هر کاربر در هر اتاق
- تغییر نقش کاربران (مثلاً ارتقا از دانشجو به معلم)

#### 🔧 اضافه کردن کاربر به اتاق (روش 1)

```bash
curl -X POST "https://fofofish.app/api/skyroom/rooms/1/add_users/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {"user_id": 1, "access": 3},
      {"user_id": 2, "access": 1},
      {"user_id": 3, "access": 2}
    ]
  }'
```

**نکات:**
- `user_id`: شماره کاربر
- `access`: 1=عادی، 2=ارایه‌کننده، 3=اپراتور

#### 🔧 اضافه کردن اتاق به کاربر (روش 2)

```bash
curl -X POST "https://fofofish.app/api/skyroom/users/1/add_rooms/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "rooms": [
      {"room_id": 1, "access": 3},
      {"room_id": 2, "access": 1}
    ]
  }'
```

#### 📋 تمام API های دسترسی

| عملیات | روش | مسیر | توضیح |
|--------|------|------|--------|
| دریافت تمام | GET | `/skyroom/access/` | لیست تمام دسترسی‌ها |
| دریافت یکی | GET | `/skyroom/access/1/` | جزئیات دسترسی 1 |
| ایجاد | POST | `/skyroom/access/` | دسترسی جدید |
| ویرایش | PUT | `/skyroom/access/1/` | تغییر سطح دسترسی |
| حذف | DELETE | `/skyroom/access/1/` | حذف دسترسی |

---

### 5️⃣ لینک ورود سریع (Login URL)

#### 📝 توضیح
لینک ورود سریع بدون نیاز به **نام کاربری و رمز عبور**، کاربر را مستقیم به اتاق ببرد.

#### 🎯 برای چه کاری
- ارسال لینک به مهمان‌ها
- دسترسی یک‌بار مصرف
- کنترل مدت زمان اعتبار لینک

#### 🔧 تولید لینک ورود سریع

```bash
curl -X POST "https://fofofish.app/api/skyroom/login-urls/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "room": 1,
    "user": 1,
    "nickname": "مهمان",
    "access": 1,
    "concurrent": 1,
    "ttl": 3600
  }'
```

**نکات:**
- `room`: شماره اتاق
- `user`: شماره کاربر
- `nickname`: اسم نمایش داده شده
- `access`: سطح دسترسی
- `ttl`: مدت زمان اعتبار (به ثانیه) - 3600 = 1 ساعت

**پاسخ:**
```json
{
  "id": 1,
  "room": 1,
  "url": "https://www.skyroom.online/ch/sample/room/t/eyJ0eXAi...",
  "expires_at": "2024-01-15T11:30:00Z"
}
```

#### 📋 تمام API های لینک ورود

| عملیات | روش | مسیر | توضیح |
|--------|------|------|--------|
| دریافت تمام | GET | `/skyroom/login-urls/` | لیست تمام لینک‌ها |
| دریافت یکی | GET | `/skyroom/login-urls/1/` | جزئیات لینک 1 |
| ایجاد | POST | `/skyroom/login-urls/` | لینک جدید |
| حذف | DELETE | `/skyroom/login-urls/1/` | حذف لینک |
| فعال‌ها | GET | `/skyroom/login-urls/active/` | لینک‌های معتبر |
| منقضی‌ها | GET | `/skyroom/login-urls/expired/` | لینک‌های منقضی |
| لغو | POST | `/skyroom/login-urls/1/revoke/` | لغو فوری لینک |

---

## سناریوهای واقعی

### سناریو 1: ایجاد یک دوره آنلاین

**مرحله 1: سرویس ایجاد کنید**
```bash
# برای دوره‌ی برنامه‌نویسی Python
curl -X POST "https://fofofish.app/api/skyroom/services/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 1,
    "title": "دوره برنامه‌نویسی Python",
    "status": 1,
    "user_limit": 100,
    "video_limit": 8,
    "start_time": 1609459200,
    "stop_time": 1640995200
  }'
```

**مرحله 2: اتاق‌ها ایجاد کنید (برای هر هفته‌ی دوره)**
```bash
# درس اول
curl -X POST "https://fofofish.app/api/skyroom/rooms/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 101,
    "service": 1,
    "name": "python-lesson-week-1",
    "title": "درس ۱: مقدمات Python",
    "status": 1,
    "guest_login": false,
    "max_users": 100
  }'

# درس دوم
curl -X POST "https://fofofish.app/api/skyroom/rooms/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 102,
    "service": 1,
    "name": "python-lesson-week-2",
    "title": "درس ۲: متغیرها و انواع داده",
    "status": 1,
    "guest_login": false,
    "max_users": 100
  }'
```

**مرحله 3: کاربران ایجاد کنید**
```bash
# کاربر استاد
curl -X POST "https://fofofish.app/api/skyroom/users/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 1000,
    "username": "dr_ali",
    "nickname": "دکتر علی",
    "password": "secure123",
    "email": "ali@university.com",
    "fname": "علی",
    "lname": "احمدی",
    "gender": 1,
    "status": 1
  }'

# کاربران دانشجو
curl -X POST "https://fofofish.app/api/skyroom/users/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "skyroom_id": 1001,
    "username": "student_fateme",
    "nickname": "فاطمه",
    "password": "secure123",
    "email": "fateme@student.com",
    "fname": "فاطمه",
    "lname": "حسینی",
    "gender": 2,
    "status": 1
  }'
```

**مرحله 4: کاربران را به اتاق‌ها اضافه کنید**
```bash
# استاد را به درس‌ها اضافه کنید (به‌عنوان اپراتور)
curl -X POST "https://fofofish.app/api/skyroom/rooms/1/add_users/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {"user_id": 1, "access": 3}
    ]
  }'

# دانشجوها را به درس اول اضافه کنید
curl -X POST "https://fofofish.app/api/skyroom/rooms/1/add_users/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {"user_id": 2, "access": 1}
    ]
  }'
```

**مرحله 5: لینک ورود سریع تولید کنید (برای مهمان‌ها)**
```bash
# لینک برای یک مهمان
curl -X POST "https://fofofish.app/api/skyroom/login-urls/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9920d04583008" \
  -H "Content-Type: application/json" \
  -d '{
    "room": 1,
    "user": 2,
    "nickname": "مهمان",
    "access": 1,
    "ttl": 86400
  }'
```

---

### سناریو 2: مدیریت یک جلسه شرکتی

**مرحله 1-2: سرویس و اتاق ایجاد کنید**
```bash
# سرویس
curl -X POST "https://fofofish.app/api/skyroom/services/" \
  -d '{"skyroom_id": 2, "title": "سرویس شرکتی", ...}'

# اتاق
curl -X POST "https://fofofish.app/api/skyroom/rooms/" \
  -d '{
    "skyroom_id": 201,
    "service": 2,
    "name": "board-meeting",
    "title": "جلسه هیات مدیره",
    "guest_login": false,
    "op_login_first": true,
    ...
  }'
```

**مرحله 3-4: مدیران و شرکت‌کنندگان**
```bash
# مدیر (اپراتور)
curl -X POST "https://fofofish.app/api/skyroom/users/" \
  -d '{
    "username": "manager_hassan",
    "nickname": "حسن مدیر",
    ...
  }'

# شرکت‌کنندگان (کاربران عادی)
curl -X POST "https://fofofish.app/api/skyroom/users/" \
  -d '{"username": "employee_1", ...}'
```

**مرحله 5: لینک‌های ورود برای شرکت‌کنندگان**
```bash
curl -X POST "https://fofofish.app/api/skyroom/login-urls/" \
  -d '{
    "room": 2,
    "user": 1001,
    "nickname": "کارمند ۱",
    "access": 1,
    "ttl": 3600
  }'
```

---

## نکات مهم

### ⚠️ ترتیب الزامی
```
سرویس → اتاق → کاربر → دسترسی → لینک ورود
```
**شما نمی‌توانید اتاق بسازید بدون سرویس!**

### 🔐 سطح‌های دسترسی

| سطح | کد | توانایی‌ها |
|------|-----|---------|
| کاربر عادی | 1 | مشاهده، گفتگو |
| ارایه‌کننده | 2 | + اشتراک‌گذاری صفحه |
| اپراتور | 3 | + کنترل اتاق، مدیریت کاربران |

### 🔗 لینک ورود سریع

- **TTL**: مدت اعتبار لینک (به ثانیه)
  - 3600 = 1 ساعت
  - 86400 = 1 روز
  - 604800 = 1 هفته

- **Concurrent**: چند نفر می‌تونند از یک لینک استفاده کنند
  - 1 = فقط یک نفر
  - 0 = بی‌محدود

### 📱 فیلترینگ و جستجو

```bash
# جستجوی کاربران به نام
https://fofofish.app/api/skyroom/users/?search=ali

# فیلتر اتاق‌های فعال
https://fofofish.app/api/skyroom/rooms/?status=1

# جستجوی اتاق‌های خاص
https://fofofish.app/api/skyroom/rooms/?search=python

# لینک‌های معتبر
https://fofofish.app/api/skyroom/login-urls/active/
```

### 🔍 حذف و ویرایش

```bash
# ویرایش کاربر
curl -X PUT "https://fofofish.app/api/skyroom/users/1/" \
  -d '{"nickname": "علی نام جدید", ...}'

# حذف اتاق
curl -X DELETE "https://fofofish.app/api/skyroom/rooms/1/" \
  -H "X-API-Key: apikey-39974696-1-e570445f94a95d2573d9922d04583008"
```

### 💡 نکات عملی

1. **نام‌گذاری**: نام‌های انگلیسی برای `name` و `username` استفاده کنید
2. **ID یکتا**: هر `skyroom_id` باید منحصر به فرد باشد
3. **رمز عبور**: رمز قوی استفاده کنید
4. **تاریخ**: از Unix timestamp استفاده کنید

---

## خلاصه

| مرحله | API | مثال |
|--------|-----|--------|
| 1️⃣ | سرویس | `POST /skyroom/services/` |
| 2️⃣ | اتاق | `POST /skyroom/rooms/` |
| 3️⃣ | کاربر | `POST /skyroom/users/` |
| 4️⃣ | دسترسی | `POST /skyroom/rooms/{id}/add_users/` |
| 5️⃣ | لینک | `POST /skyroom/login-urls/` |

**برای اطلاعات بیشتر:**
- 📖 [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - مستندات کامل
- 🌐 https://fofofish.app/api/docs/swagger/ - تست زنده

