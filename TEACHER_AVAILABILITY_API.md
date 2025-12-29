# معلم - مدیریت شکاف‌های زمانی
# Teacher Availability Management

## خلاصه

معلمان می‌توانند ساعات کاری خود (شکاف‌های زمانی) را برای دریافت درس تعریف کنند. دانش‌آموزان می‌توانند این شکاف‌ها را ببینند و درس را رزرو کنند.

---

## نقاط پایانی (Endpoints)

### 1. لیست شکاف‌های زمانی معلم

```
GET /api/teacher/availability/
```

#### توضیح
- دریافت تمام شکاف‌های زمانی فعلی معلم
- معلم فقط شکاف‌های خود را می‌بیند
- دانش‌آموزان فقط شکاف‌های منتشر شده را می‌بینند

#### مجوز
```
Authorization: Bearer YOUR_TOKEN
```

#### پارامترهای کوئری (اختیاری)

| پارامتر | نوع | توضیح | مثال |
|---------|------|-------|------|
| `date` | string | تاریخ خاص (YYYY-MM-DD) | `2025-01-15` |
| `day_of_week` | integer | روز هفته (0=شنبه، 6=جمعه) | `1` |
| `is_active` | boolean | فقط شکاف‌های فعال | `true` |
| `page` | integer | شماره صفحه | `1` |

#### مثال درخواست

```bash
curl -X GET 'http://localhost:8000/api/teacher/availability/?day_of_week=1&is_active=true' \
  -H 'Authorization: Bearer TOKEN'
```

#### پاسخ موفق (200)

```json
{
  "count": 5,
  "next": "http://localhost:8000/api/teacher/availability/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "teacher": 1,
      "teacher_name": "علی محمدی",
      "day_of_week": 1,
      "day_of_week_display": "دوشنبه",
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "capacity": 2,
      "booked": 1,
      "available_slots": 1,
      "hourly_rate": 100000,
      "is_active": true,
      "created_at": "2025-01-01T10:30:00Z",
      "updated_at": "2025-01-15T14:20:00Z"
    },
    {
      "id": 2,
      "teacher": 1,
      "teacher_name": "علی محمدی",
      "day_of_week": 2,
      "day_of_week_display": "سه‌شنبه",
      "start_time": "10:00:00",
      "end_time": "11:00:00",
      "capacity": 3,
      "booked": 2,
      "available_slots": 1,
      "hourly_rate": 100000,
      "is_active": true,
      "created_at": "2025-01-01T10:30:00Z",
      "updated_at": "2025-01-15T14:20:00Z"
    }
  ]
}
```

#### کدهای خطا

| کد | معنی |
|------|------|
| 200 | موفق |
| 401 | عدم احراز هویت (توکن مورد نیاز) |
| 403 | دسترسی ممنوع (نه معلم) |

---

### 2. ایجاد شکاف زمانی

```
POST /api/teacher/availability/create/
```

#### توضیح
- ایجاد یک شکاف زمانی جدید
- فقط معلمان می‌توانند اینکار کنند
- یک شکاف برای یک روز خاص در هفته

#### مجوز
```
Authorization: Bearer TEACHER_TOKEN
```

#### جسم درخواست (JSON)

**مورد اجباری:**

| فیلد | نوع | توضیح | مثال |
|------|------|-------|------|
| `day_of_week` | integer | روز هفته (0=شنبه، 6=جمعه) | `1` |
| `start_time` | string | ساعت شروع (HH:MM:SS) | `"09:00:00"` |
| `end_time` | string | ساعت پایان (HH:MM:SS) | `"10:00:00"` |
| `capacity` | integer | ظرفیت (تعداد دانش‌آموز) | `2` |

**اختیاری:**

| فیلد | نوع | پیش‌فرض | توضیح |
|------|------|----------|-------|
| `hourly_rate` | integer | 100000 | قیمت ساعتی |
| `is_active` | boolean | true | فعال بودن |
| `description` | string | "" | توضیح شکاف |

#### مثال درخواست

```bash
curl -X POST 'http://localhost:8000/api/teacher/availability/create/' \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "capacity": 2,
    "hourly_rate": 100000,
    "is_active": true,
    "description": "کلاس انگلیسی"
  }'
```

#### پاسخ موفق (201)

```json
{
  "id": 3,
  "teacher": 1,
  "teacher_name": "علی محمدی",
  "day_of_week": 1,
  "day_of_week_display": "دوشنبه",
  "start_time": "09:00:00",
  "end_time": "10:00:00",
  "capacity": 2,
  "booked": 0,
  "available_slots": 2,
  "hourly_rate": 100000,
  "is_active": true,
  "description": "کلاس انگلیسی",
  "created_at": "2025-01-29T15:30:00Z",
  "updated_at": "2025-01-29T15:30:00Z"
}
```

#### کدهای خطا

| کد | معنی |
|------|------|
| 201 | ایجاد شده |
| 400 | داده نامعتبر (مثلاً end_time < start_time) |
| 401 | عدم احراز هویت |
| 403 | دسترسی ممنوع (نه معلم) |

---

### 3. ایجاد گروهی شکاف‌های زمانی

```
POST /api/teacher/availability/bulk-create/
```

#### توضیح
- ایجاد چندین شکاف زمانی به یک‌باره
- مفید برای تعریف ساعات هفتگی
- تمام شکاف‌ها یک ساعت است

#### مجوز
```
Authorization: Bearer TEACHER_TOKEN
```

#### جسم درخواست (JSON)

```json
{
  "availabilities": [
    {
      "day_of_week": 0,
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "capacity": 2,
      "hourly_rate": 100000
    },
    {
      "day_of_week": 1,
      "start_time": "10:00:00",
      "end_time": "11:00:00",
      "capacity": 2,
      "hourly_rate": 100000
    },
    {
      "day_of_week": 2,
      "start_time": "15:00:00",
      "end_time": "16:00:00",
      "capacity": 3,
      "hourly_rate": 120000
    }
  ]
}
```

#### مثال درخواست (cURL)

```bash
curl -X POST 'http://localhost:8000/api/teacher/availability/bulk-create/' \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "availabilities": [
      {
        "day_of_week": 1,
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "capacity": 2,
        "hourly_rate": 100000
      },
      {
        "day_of_week": 2,
        "start_time": "10:00:00",
        "end_time": "11:00:00",
        "capacity": 2,
        "hourly_rate": 100000
      }
    ]
  }'
```

#### مثال درخواست (Python)

```python
import requests

url = 'http://localhost:8000/api/teacher/availability/bulk-create/'
headers = {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
}

data = {
    'availabilities': [
        {
            'day_of_week': 1,
            'start_time': '09:00:00',
            'end_time': '10:00:00',
            'capacity': 2,
            'hourly_rate': 100000
        },
        {
            'day_of_week': 2,
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'capacity': 2,
            'hourly_rate': 100000
        }
    ]
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

#### پاسخ موفق (201)

```json
{
  "created_count": 2,
  "results": [
    {
      "id": 4,
      "day_of_week": 1,
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "capacity": 2,
      "hourly_rate": 100000,
      "is_active": true
    },
    {
      "id": 5,
      "day_of_week": 2,
      "start_time": "10:00:00",
      "end_time": "11:00:00",
      "capacity": 2,
      "hourly_rate": 100000,
      "is_active": true
    }
  ]
}
```

#### کدهای خطا

| کد | معنی |
|------|------|
| 201 | ایجاد شده |
| 400 | داده نامعتبر |
| 401 | عدم احراز هویت |
| 403 | دسترسی ممنوع |

---

### 4. بروزرسانی شکاف زمانی

```
POST /api/teacher/availability/{id}/update/
```

#### توضیح
- تغییر شکاف زمانی موجود
- فقط معلم مالک می‌تواند تغییر دهد
- می‌توان تا حدودی تغییر داد

#### مجوز
```
Authorization: Bearer TEACHER_TOKEN
```

#### پارامترهای مسیر

| پارامتر | نوع | توضیح |
|---------|------|-------|
| `id` | integer | شناسه شکاف زمانی |

#### جسم درخواست (JSON)

**فیلدهایی که می‌توان تغییر داد:**

| فیلد | نوع | توضیح |
|------|------|-------|
| `capacity` | integer | تغییر ظرفیت |
| `hourly_rate` | integer | تغییر قیمت |
| `is_active` | boolean | فعال/غیرفعال کردن |
| `description` | string | تغییر توضیح |
| `start_time` | string | تغییر ساعت شروع |
| `end_time` | string | تغییر ساعت پایان |

#### مثال درخواست

```bash
curl -X POST 'http://localhost:8000/api/teacher/availability/1/update/' \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "capacity": 3,
    "hourly_rate": 120000,
    "is_active": true
  }'
```

#### پاسخ موفق (200)

```json
{
  "id": 1,
  "teacher": 1,
  "teacher_name": "علی محمدی",
  "day_of_week": 1,
  "day_of_week_display": "دوشنبه",
  "start_time": "09:00:00",
  "end_time": "10:00:00",
  "capacity": 3,
  "booked": 1,
  "available_slots": 2,
  "hourly_rate": 120000,
  "is_active": true,
  "updated_at": "2025-01-29T16:45:00Z"
}
```

#### کدهای خطا

| کد | معنی |
|------|------|
| 200 | موفق |
| 400 | داده نامعتبر |
| 401 | عدم احراز هویت |
| 403 | دسترسی ممنوع (نه مالک) |
| 404 | شکاف یافت نشد |

---

### 5. حذف شکاف زمانی

```
POST /api/teacher/availability/{id}/delete/
```

#### توضیح
- حذف شکاف زمانی
- فقط معلم مالک می‌تواند حذف کند
- اگر رزرو داشت حذف نمی‌شود

#### مجوز
```
Authorization: Bearer TEACHER_TOKEN
```

#### پارامترهای مسیر

| پارامتر | نوع | توضیح |
|---------|------|-------|
| `id` | integer | شناسه شکاف زمانی |

#### مثال درخواست

```bash
curl -X POST 'http://localhost:8000/api/teacher/availability/1/delete/' \
  -H 'Authorization: Bearer TOKEN'
```

#### پاسخ موفق (204)

```json
{
  "message": "شکاف زمانی حذف شد"
}
```

#### کدهای خطا

| کد | معنی |
|------|------|
| 204 | حذف شده |
| 400 | نمی‌توان حذف کرد (دارای رزرو) |
| 401 | عدم احراز هویت |
| 403 | دسترسی ممنوع (نه مالک) |
| 404 | شکاف یافت نشد |

---

## مثال‌های عملی

### سناریو 1: معلم جدید - تعریف ساعات هفتگی

**مرحله 1:** وارد شوید و توکن بگیرید
```bash
POST /api/teacher/login-password/
```

**مرحله 2:** ساعات خود را تعریف کنید
```bash
POST /api/teacher/availability/bulk-create/

جسم:
{
  "availabilities": [
    {"day_of_week": 1, "start_time": "09:00", "end_time": "10:00", "capacity": 2},
    {"day_of_week": 1, "start_time": "16:00", "end_time": "17:00", "capacity": 2},
    {"day_of_week": 2, "start_time": "10:00", "end_time": "11:00", "capacity": 3},
    {"day_of_week": 3, "start_time": "15:00", "end_time": "16:00", "capacity": 2},
    {"day_of_week": 5, "start_time": "18:00", "end_time": "19:00", "capacity": 2}
  ]
}
```

**مرحله 3:** ببینید چه شکاف‌هایی ایجاد شد
```bash
GET /api/teacher/availability/
```

---

### سناریو 2: معلم - تغییر قیمت

**قیمت را برای شکاف 1 تغییر دهید:**
```bash
POST /api/teacher/availability/1/update/

جسم:
{
  "hourly_rate": 150000
}
```

---

### سناریو 3: معلم - حذف شکاف

**حذف شکاف 5 (اگر نرزرو شده باشد):**
```bash
POST /api/teacher/availability/5/delete/
```

---

### سناریو 4: دانش‌آموز - جستجو شکاف‌های موجود

**شکاف‌های دوشنبه را ببینید:**
```bash
GET /api/teacher/availability/?day_of_week=1

نتیجه: تمام شکاف‌های فعال دوشنبه
```

---

## روزهای هفته

| عدد | نام فارسی | نام انگلیسی |
|------|----------|----------|
| 0 | شنبه | Saturday |
| 1 | دوشنبه | Monday |
| 2 | سه‌شنبه | Tuesday |
| 3 | چهارشنبه | Wednesday |
| 4 | پنج‌شنبه | Thursday |
| 5 | جمعه | Friday |

---

## نکات مهم

### ✅ بهترین شیوه‌ها

1. **ظرفیت واقعی**: ظرفیت را بیش از توان خود نکنید
2. **قیمت منطقی**: قیمت‌های رقابتی قرار دهید
3. **تحدیث منظم**: ساعات خود را به‌روز نگاه دارید
4. **توضیح واضح**: توضیح شکاف را خوب نوشتید
5. **زمان‌بندی**: بین کلاس‌ها وقت استراحت قرار دهید

### ❌ اشتباع‌های رایج

1. ❌ شکاف‌هایی بدون توضیح
2. ❌ ظرفیت بیش از حد
3. ❌ قیمت غیرمعقول
4. ❌ شکاف‌های متداخل
5. ❌ فراموش کردن فعال کردن شکاف

---

## خطاهای رایج

### خطا: 400 Bad Request

**مسئله:** ساعت پایان قبل از ساعت شروع است
```
start_time: "10:00:00"
end_time: "09:00:00"  # ❌ غلط
```
**حل:**
```
end_time: "11:00:00"  # ✅ درست
```

---

### خطا: 403 Forbidden

**مسئله:** می‌خواهید شکاف معلم دیگر را تغییر دهید
```
❌ نمی‌توانید
```
**حل:**
```
✅ فقط شکاف‌های خود را تغییر دهید
```

---

### خطا: 404 Not Found

**مسئله:** شناسه شکاف اشتباه است
```
/api/teacher/availability/999/update/  # ❌ وجود ندارد
```
**حل:**
```
# ابتدا تمام شکاف‌ها را ببینید
GET /api/teacher/availability/
# سپس شناسه صحیح را استفاده کنید
```

---

## پاسخ‌های معمول

### 200 - موفق
```json
{"message": "شکاف زمانی بروز شد"}
```

### 201 - ایجاد شده
```json
{"id": 5, "message": "شکاف زمانی ایجاد شد"}
```

### 204 - بدون محتوا
```
(بدون جسم)
```

### 400 - درخواست نامعتبر
```json
{
  "field_name": ["خطا: توضیح خطا"]
}
```

### 401 - عدم احراز هویت
```json
{"detail": "توکن مورد نیاز است"}
```

### 403 - دسترسی ممنوع
```json
{"detail": "شما مجاز نیستید"}
```

### 404 - یافت نشد
```json
{"detail": "شکاف یافت نشد"}
```

---

## محدودیت‌ها

| محدودیت | مقدار |
|---------|-------|
| حداکثر شکاف‌ها | بدون حد |
| حداقل ساعت | 30 دقیقه |
| حداکثر ساعت | 8 ساعت |
| حداقل ظرفیت | 1 نفر |
| حداکثر ظرفیت | 10 نفر |
| حداقل قیمت | 10,000 تومان |

---

## نکات امنیتی

1. **توکن محافظت‌شده**: توکن را ایمن نگاه دارید
2. **HTTPS**: همیشه HTTPS استفاده کنید
3. **تأیید مالکیت**: فقط شکاف‌های خود را مدیریت کنید
4. **مجوزها**: سیستم خودکار مجوزها را بررسی می‌کند

---

## پشتیبانی

برای مشکلات:
- Email: support@fofofish.com
- Chat: در اپلیکیشن
- Phone: +98-21-XXXX-XXXX
