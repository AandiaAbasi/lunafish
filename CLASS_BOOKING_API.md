# کلاس خریداری (Class Booking) - API Documentation

## خلاصه سیستم

این سیستم دانش‌آموزان را قادر می‌سازد تا کلاس‌های معلمان را خریداری کنند و معلمان می‌توانند درخواست‌های رزرو را مدیریت کنند.

---

## مراحل فرایند خریدن کلاس

### 1️⃣ دانش‌آموز لیست بازه‌های زمانی معلم را مشاهده می‌کند
- درخواست: `GET /api/teacher/availability/`
- فیلتر نتایج برای معلم مورد نظر
- مشاهده قیمت و ساعات موجود

### 2️⃣ دانش‌آموز جزئیات بازه زمانی را مشاهده می‌کند (اختیاری)
- درخواست: `GET /api/teacher/availability/{id}/`
- مشاهده تمام جزئیات شامل قیمت، نوع درس، یادداشت‌ها

### 3️⃣ دانش‌آموز کلاس را خریداری می‌کند
- درخواست: `POST /api/class-booking/create/`
- انتخاب بازه زمانی و درس
- ایجاد رزرو (Booking)

### 4️⃣ دانش‌آموز لیست رزروهای خود را مشاهده می‌کند
- درخواست: `GET /api/my-bookings/`
- مشاهده تمام کلاس‌های خریداری شده

### 5️⃣ معلم لیست رزروهای دانش‌آموزانش را مشاهده می‌کند
- درخواست: `GET /api/teacher/bookings/`
- مشاهده اینکه کی برای چه زمانی رزرو کردند

### 6️⃣ معلم وضعیت را به "تکمیل شده" تغییر می‌دهد
- درخواست: `PATCH /api/class-booking/{id}/status/`
- تغییر وضعیت برای فصل‌بندی و درآمد

### 7️⃣ دانش‌آموز می‌تواند رزرو را لغو کند (قبل از کلاس)
- درخواست: `POST /api/class-booking/{id}/cancel/`
- لغو رزرو بازگشت بازه زمانی به دسترس

---

## 🔑 API Endpoints

### 1. خریدن کلاس
**POST** `/api/class-booking/create/`

#### احتیاجات:
- تایید: دانش‌آموز
- Body: JSON

#### Request Body:
```json
{
  "availability": 1,
  "subject": 5,
  "discount_code": "DISCOUNT2024"
}
```

#### پارامترها:
| پارامتر | نوع | توضیح |
|--------|-----|-------|
| `availability` | int | ID بازه زمانی |
| `subject` | int | ID درس (موضوع تدریس) |
| `discount_code` | string | (اختیاری) کد تخفیف |

#### پاسخ موفق (201):
```json
{
  "data": {
    "id": 1,
    "availability": 1,
    "availability_date": "1403/10/15",
    "availability_time": "14:00 - 15:00",
    "teacher": 5,
    "teacher_name": "علی احمدی",
    "student": 10,
    "student_name": "فاطمه محمدی",
    "subject": 5,
    "subject_title": "انگلیسی مبتدی",
    "status": "reserved",
    "status_display": "رزرو شده",
    "price": 150000,
    "discount_amount": 0,
    "final_price": 150000,
    "created_at": "2025-01-01T10:30:00Z",
    "updated_at": "2025-01-01T10:30:00Z"
  },
  "message": "کلاس با موفقیت خریداری شد"
}
```

#### اخطارها:
```json
// 400 - بازه زمانی دسترس پذیر نیست
{
  "error": "این زمان‌بندی دیگر در دسترس نیست"
}

// 403 - فقط دانش‌آموزان می‌توانند خریداری کنند
{
  "error": "تنها دانش‌آموزان می‌توانند کلاس خریداری کنند"
}

// 404 - بازه زمانی یا درس یافت نشد
{
  "error": "بازه زمانی یا درس یافت نشد"
}
```

---

### 2. لیست رزروهای دانش‌آموز
**GET** `/api/my-bookings/`

#### احتیاجات:
- تایید: دانش‌آموز

#### Query Parameters:
| پارامتر | نوع | توضیح |
|--------|-----|-------|
| `status` | string | فیلتر بر اساس وضعیت (reserved, completed, cancelled, no_show) |
| `teacher` | int | فیلتر بر اساس معلم |
| `page` | int | شماره صفحه (پیش‌فرض: 1) |
| `page_size` | int | تعداد نتایج در صفحه (پیش‌فرض: 20) |

#### مثال:
```
GET /api/my-bookings/?status=completed&teacher=5&page=1&page_size=10
```

#### پاسخ موفق (200):
```json
{
  "count": 15,
  "next": "http://api.example.com/my-bookings/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "availability": 1,
      "availability_date": "1403/10/15",
      "availability_time": "14:00 - 15:00",
      "teacher": 5,
      "teacher_name": "علی احمدی",
      "student": 10,
      "student_name": "فاطمه محمدی",
      "subject": 5,
      "subject_title": "انگلیسی مبتدی",
      "status": "completed",
      "status_display": "تکمیل شده",
      "price": 150000,
      "discount_amount": 0,
      "final_price": 150000,
      "created_at": "2025-01-01T10:30:00Z",
      "updated_at": "2025-01-02T15:45:00Z"
    }
  ]
}
```

---

### 3. لیست رزروهای معلم
**GET** `/api/teacher/bookings/`

#### احتیاجات:
- تایید: معلم

#### Query Parameters:
| پارامتر | نوع | توضیح |
|--------|-----|-------|
| `status` | string | فیلتر بر اساس وضعیت |
| `subject` | int | فیلتر بر اساس درس |
| `page` | int | شماره صفحه |
| `page_size` | int | تعداد نتایج در صفحه |

#### مثال:
```
GET /api/teacher/bookings/?status=reserved&page=1
```

#### پاسخ موفق (200):
```json
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "availability": 2,
      "availability_date": "1403/10/16",
      "availability_time": "15:30 - 16:30",
      "teacher": 5,
      "teacher_name": "علی احمدی",
      "student": 11,
      "student_name": "محمد علیزاده",
      "subject": 5,
      "subject_title": "انگلیسی مبتدی",
      "status": "reserved",
      "status_display": "رزرو شده",
      "price": 150000,
      "discount_amount": 0,
      "final_price": 150000,
      "created_at": "2025-01-01T11:00:00Z",
      "updated_at": "2025-01-01T11:00:00Z"
    }
  ]
}
```

---

### 4. تغییر وضعیت رزرو
**PATCH** `/api/class-booking/{id}/status/`

#### احتیاجات:
- تایید: معلم (صاحب کلاس)
- ID: شناسه رزرو

#### Request Body:
```json
{
  "status": "completed"
}
```

#### وضعیت‌های معتبر:
- `reserved` - رزرو شده (پیش‌فرض)
- `completed` - تکمیل شده (معلم درس را تمام کرده)
- `cancelled` - لغو شده (توسط معلم)
- `no_show` - دانش‌آموز حاضر نشد

#### پاسخ موفق (200):
```json
{
  "data": {
    "id": 1,
    "status": "completed",
    "status_display": "تکمیل شده",
    "updated_at": "2025-01-02T15:45:00Z"
  },
  "message": "وضعیت رزرو با موفقیت به‌روزرسانی شد"
}
```

#### اخطارها:
```json
// 403 - صرفاً معلم می‌تواند تغییر دهد
{
  "error": "شما دسترسی ندارید"
}

// 400 - وضعیت نامعتبر
{
  "error": "وضعیت نامعتبر است"
}
```

---

### 5. لغو رزرو (توسط دانش‌آموز)
**POST** `/api/class-booking/{id}/cancel/`

#### احتیاجات:
- تایید: دانش‌آموز (صاحب رزرو)
- ID: شناسه رزرو

#### Request Body:
```json
{}
```

#### شرایط:
- فقط رزروهای با وضعیت `reserved` می‌توانند لغو شوند
- بازه زمانی دوباره دسترس پذیر می‌شود

#### پاسخ موفق (200):
```json
{
  "data": {
    "id": 1,
    "status": "cancelled",
    "status_display": "لغو شده",
    "updated_at": "2025-01-02T14:30:00Z"
  },
  "message": "رزرو با موفقیت لغو شد"
}
```

#### اخطارها:
```json
// 403 - فقط صاحب رزرو می‌تواند لغو کند
{
  "error": "شما دسترسی ندارید"
}

// 403 - نمی‌توان لغو کرد (کلاس تکمیل شده)
{
  "error": "این رزرو نمی‌تواند لغو شود"
}
```

---

## 📊 وضعیت‌های Booking

| وضعیت | توضیح | کیا می‌تواند لغو کند | نتیجه مالی |
|------|-------|-------------------|-----------|
| `reserved` | رزرو شده، در انتظار برگزاری | بله (دانش‌آموز) | معلق |
| `completed` | کلاس برگزار شد | خیر | درآمد برای معلم |
| `cancelled` | رزرو لغو شد | N/A | بازگشت پول |
| `no_show` | دانش‌آموز حاضر نشد | خیر | درآمد برای معلم |

---

## 💰 قیمت‌گذاری

### منطق قیمت:
1. **قیمت اصلی**: از بازه زمانی (`TeacherAvailability.price`)
2. **قیمت تخفیف**: از بازه زمانی اگر وجود داشتند (`TeacherAvailability.discount_price`)
3. **قیمت نهایی**: هنگام خریدن استفاده می‌شود

### مثال:
```json
{
  "price": 150000,
  "discount_price": 120000,
  "discount_amount": 30000,
  "final_price": 120000
}
```

---

## 🔐 دسترسی و احتیاجات

### دانش‌آموز:
- ✅ می‌تواند کلاس خریداری کند
- ✅ می‌تواند لیست رزروهای خود را ببیند
- ✅ می‌تواند رزرو را لغو کند
- ❌ نمی‌تواند وضعیت را تغییر دهد

### معلم:
- ❌ نمی‌تواند کلاس خریداری کند
- ✅ می‌تواند لیست رزروهای دانش‌آموزانش را ببیند
- ✅ می‌تواند وضعیت را به "تکمیل شده" تغییر دهد
- ❌ نمی‌تواند رزرو دانش‌آموز را لغو کند

### مدیر:
- ✅ دسترسی کامل به همه رزروها

---

## 📝 نمونه درخواست‌های کامل

### نمونه 1: خریدن کلاس انگلیسی
```bash
curl -X POST https://api.example.com/api/class-booking/create/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "availability": 1,
    "subject": 5
  }'
```

### نمونه 2: دیدن تمام رزروهای تکمیل شده
```bash
curl -X GET https://api.example.com/api/my-bookings/?status=completed \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### نمونه 3: معلم تکمیل درس را علامت می‌زند
```bash
curl -X PATCH https://api.example.com/api/class-booking/1/status/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

### نمونه 4: دانش‌آموز رزرو را لغو می‌کند
```bash
curl -X POST https://api.example.com/api/class-booking/1/cancel/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ⚠️ خطاهای رایج و حل‌ها

### خطا: "این زمان‌بندی دیگر در دسترس نیست"
**علت**: بازه زمانی قبلاً رزرو شده یا منقضی شده است
**حل**: بازه زمانی دیگری انتخاب کنید

### خطا: "درس باید متعلق به همان معلم باشد"
**علت**: درس انتخاب شده متعلق به معلم بازه زمانی نیست
**حل**: درس صحیح را انتخاب کنید

### خطا: "تنها دانش‌آموزان می‌توانند کلاس خریداری کنند"
**علت**: حساب کاربری معلم یا ادمین است
**حل**: با حساب دانش‌آموز وارد شوید

### خطا: "این رزرو نمی‌تواند لغو شود"
**علت**: کلاس قبلاً تکمیل شده یا لغو شده است
**حل**: تنها رزروهای "رزرو شده" می‌توانند لغو شوند

---

## 🔄 جریان درآمد

```
┌─────────────────────────────┐
│ دانش‌آموز کلاس خریداری می‌کند  │
└──────────────┬──────────────┘
               │
        ✓ Booking Created
        Status: reserved
               │
               ▼
┌─────────────────────────────┐
│   معلم درس را برگزار می‌کند   │
└──────────────┬──────────────┘
               │
        معلم وضعیت را تغییر می‌دهد
        Status: completed
               │
               ▼
┌─────────────────────────────┐
│  ClassRevenue ایجاد شد      │
│  درآمد برای معلم محاسبه شد  │
└─────────────────────────────┘
```

---

## 📚 مدل‌های مرتبط

### ClassBooking Model:
```python
class ClassBooking(BaseModel):
    availability = ForeignKey(TeacherAvailability)
    teacher = ForeignKey(User)
    student = ForeignKey(User)
    subject = ForeignKey(TeachingSubject)
    status = CharField(choices=[
        'reserved',    # رزرو شده
        'completed',   # تکمیل شده
        'cancelled',   # لغو شده
        'no_show'      # حاضر نشد
    ])
    price = DecimalField()
    discount_amount = DecimalField()
    final_price = DecimalField()
```

---

## 🎯 نکات مهم

1. **فقط بازه‌های دسترس‌پذیر**: نمی‌توانید بازه‌های غیرفعال یا منقضی‌شده را خریداری کنید

2. **یک‌بار رزرو**: هر بازه زمانی تنها برای یک دانش‌آموز می‌تواند رزرو شود

3. **لغو محدود**: فقط رزروهای "رزرو شده" می‌توانند لغو شوند

4. **بازگشت بازه**: وقتی رزرو لغو شود، بازه زمانی دوباره برای رزرو دیگران دسترس‌پذیر می‌شود

5. **درآمد**: درآمد تنها وقتی وضعیت به "تکمیل شده" تغییر یابد، ثبت می‌شود
