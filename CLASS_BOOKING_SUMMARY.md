# خریدن کلاس - خلاصه سریع

## 🎯 پنج API اصلی

### 1️⃣ دانش‌آموز کلاس خریداری می‌کند
```bash
POST /api/class-booking/create/
```
```json
{
  "availability": 1,
  "subject": 5
}
```

### 2️⃣ دانش‌آموز رزروهای خود را می‌بیند
```bash
GET /api/my-bookings/?status=completed
```

### 3️⃣ معلم رزروهای دانش‌آموزانش را می‌بیند
```bash
GET /api/teacher/bookings/?status=reserved
```

### 4️⃣ معلم کلاس را تکمیل علامت می‌زند
```bash
PATCH /api/class-booking/1/status/
```
```json
{
  "status": "completed"
}
```

### 5️⃣ دانش‌آموز رزرو را لغو می‌کند
```bash
POST /api/class-booking/1/cancel/
```

---

## 📋 وضعیت‌های رزرو

| Status | معنی | توسط چه کسی |
|--------|------|-----------|
| `reserved` | رزرو شده | سیستم خودکار |
| `completed` | تکمیل شده | معلم |
| `cancelled` | لغو شده | دانش‌آموز یا معلم |
| `no_show` | حاضر نشد | معلم |

---

## 📂 فایل‌های تغییر یافته

1. **api/classroom_serializers.py** - اضافه کردن CreateClassBookingSerializer
2. **api/views.py** - اضافه کردن 5 APIView برای خریدن و مدیریت کلاس‌ها
3. **api/urls.py** - اضافه کردن 5 route جدید
4. **CLASS_BOOKING_API.md** - documentation مفصل

---

## 🔑 دسترسی‌های مختلف

### دانش‌آموز:
- ✅ خریدن کلاس
- ✅ دیدن رزروهای خود
- ✅ لغو رزرو
- ❌ تغییر وضعیت

### معلم:
- ❌ خریدن کلاس
- ✅ دیدن رزروهای دانش‌آموزان
- ✅ تغییر وضعیت
- ❌ لغو رزرو دانش‌آموز

---

## 💡 نکات مهم

✅ تمام validation‌ها اضافه شده  
✅ بازه‌های منقضی را فیلتر می‌کند  
✅ فقط یک دانش‌آموز می‌تواند هر بازه را رزرو کند  
✅ قیمت اتوماتیک تعیین می‌شود  

---

## 📖 مستندات کامل
👉 ببینید: `CLASS_BOOKING_API.md`
