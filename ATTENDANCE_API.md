# Attendance API - API حضور و غیاب

## خلاصه

دو API برای مدیریت حضور و غیاب دانش‌آموزان در کلاس‌ها:

1. **Mark Attendance** - ثبت یا بروزرسانی حضور/غیاب
2. **Get Attendance List** - دریافت لیست حضور/غیاب یک جلسه

---

## API 1: Mark Attendance

**درخواست:**
```
POST /api/attendance/{booking_id}/
```

**پارامترهای مسیر:**
- `booking_id`: شناسه جلسه کلاس

**بدنه درخواست:**
```json
{
  "student_id": 5,
  "status": "present"
}
```

**پاسخ موفق (200):**
```json
{
  "student_id": 5,
  "booking_id": 12,
  "status": "present",
  "created": true
}
```

**نکات:**
- `status`: فقط `"present"` (حاضر) یا `"absent"` (غایب)
- `created`: 
  - `true` = رکورد جدید ایجاد شد
  - `false` = رکورد قدیمی به‌روزرسانی شد
- اگر دوباره همین جلسه و دانش‌آموز را فرستادید، رکورد قدیمی تغییر می‌کند

**خطاها:**
- `400`: پارامترهای گمشده یا غلط
- `404`: جلسه پیدا نشد

---

## API 2: Get Attendance List

**درخواست:**
```
GET /api/attendance/{booking_id}/list/
```

**پارامترهای مسیر:**
- `booking_id`: شناسه جلسه کلاس

**پاسخ موفق (200):**
```json
{
  "results": [
    {
      "student_id": 5,
      "student_name": "علی احمدی",
      "status": "present"
    },
    {
      "student_id": 6,
      "student_name": "فاطمه علیزاده",
      "status": "absent"
    }
  ],
  "total": 2,
  "present_count": 1,
  "absent_count": 1
}
```

**توضیح:**
- `results`: لیست حضور و غیاب
- `total`: تعداد کل دانش‌آموزان
- `present_count`: تعداد دانش‌آموزان حاضر
- `absent_count`: تعداد دانش‌آموزان غایب

**خطاها:**
- `404`: جلسه پیدا نشد

---

## نمونه‌های استفاده

### ثبت حضور
```
POST /api/attendance/12/
{
  "student_id": 5,
  "status": "present"
}
```

### ثبت غیاب
```
POST /api/attendance/12/
{
  "student_id": 5,
  "status": "absent"
}
```

### دریافت لیست حضور/غیاب
```
GET /api/attendance/12/list/
```

---

## توضیحات مهم

**Status Options:**
- `"present"` = حاضر
- `"absent"` = غایب

**Booking ID:**
- شناسه جلسه کلاس (هر کلاس برای هر معلم یک booking است)

**Authentication:**
- نیاز به JWT Token

**Rate Limit:**
- بدون محدودیت

