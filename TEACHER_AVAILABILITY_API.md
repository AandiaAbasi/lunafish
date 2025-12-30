# 🕐 Teacher Availability Management API

معلم - مدیریت شکاف‌های زمانی

---

## خلاصه

معلمان می‌توانند زمان‌های دسترسی (شکاف‌های زمانی) خود را برای تدریس تعریف کنند. هر شکاف شامل:
- **تاریخ** (میلادی)
- **ساعت شروع و پایان** 
- **قیمت** برای آن بازه
- **وضعیت** (موجود یا رزرو شده)

---

## Model Fields

### TeacherAvailability

| فیلد | نوع | توضیح |
|------|------|-------|
| `id` | Integer | شناسه |
| `teacher` | ForeignKey(User) | معلم مالک |
| `date` | Date | تاریخ (میلادی) |
| `start_time` | Time | شروع (HH:MM) |
| `end_time` | Time | پایان (HH:MM) |
| `price` | Decimal | قیمت جلسه |
| `discount_price` | Decimal | قیمت تخفیف شده |
| `is_available` | Boolean | برای رزرو موجود؟ |
| `is_booked` | Boolean | رزرو شده؟ |
| `notes` | Text | یادداشت |
| `created_at` | DateTime | زمان ایجاد |
| `updated_at` | DateTime | زمان ویرایش |

**Unique:** `(teacher, date, start_time, end_time)`

---

## Endpoints

### 1️⃣ دریافت لیست

```http
GET /api/teacher/availability/
```

**پارامترهای Query:**

| نام | توضیح | مثال |
|-----|-------|------|
| `teacher_id` | فیلتر بر حسب معلم | `?teacher_id=1` |
| `date` | تاریخ مشخص | `?date=1403/01/15` |
| `start_date` | از این تاریخ | `?start_date=1403/01/01` |
| `end_date` | تا این تاریخ | `?end_date=1403/01/31` |
| `is_available` | فقط موجود | `?is_available=true` |
| `is_booked` | فقط رزرو شده | `?is_booked=false` |
| `page_size` | تعداد در صفحه | `?page_size=20` |

**درخواست:**
```bash
curl 'http://localhost:8000/api/teacher/availability/?date=1403/01/15' \
  -H 'Authorization: Bearer TOKEN'
```

**پاسخ 200:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "teacher": 1,
      "teacher_name": "علی محمدی",
      "date": "1403/01/15",
      "start_time": "09:00:00",
      "end_time": "10:00:00",
      "price": "100000.00",
      "discount_price": null,
      "is_available": true,
      "is_booked": false,
      "notes": "کلاس آنلاین",
      "created_at": "2025-01-01T10:30:00Z",
      "updated_at": "2025-01-15T14:20:00Z"
    }
  ]
}
```

**Errors:**
- `401` - معتبر نشده
- `400` - تاریخ نادرست

---

### 2️⃣ ایجاد بازه تکی

```http
POST /api/teacher/availability/create/
```

**بدنه:**
```json
{
  "date": "1403/01/15",
  "start_time": "09:00",
  "end_time": "10:00",
  "price": 100000,
  "discount_price": null,
  "notes": "کلاس آنلاین"
}
```

**پاسخ 201:**
```json
{
  "id": 5,
  "teacher": 1,
  "teacher_name": "علی محمدی",
  "date": "1403/01/15",
  "start_time": "09:00:00",
  "end_time": "10:00:00",
  "price": "100000.00",
  "discount_price": null,
  "is_available": true,
  "is_booked": false,
  "notes": "کلاس آنلاین",
  "created_at": "2025-01-15T15:30:00Z"
}
```

---

### 3️⃣ ایجاد گروهی (محدوده تاریخی)

```http
POST /api/teacher/availability/bulk-create/
```

**بدنه:**
```json
{
  "start_date": "1403/01/01",
  "end_date": "1403/01/31",
  "daily_start_time": "09:00",
  "daily_end_time": "17:00",
  "session_duration": 30,
  "break_duration": 10,
  "price": 50000,
  "notes": "کلاس‌های آنلاین"
}
```

**شرح پارامترها:**

| پارامتر | توضیح | مثال |
|---------|-------|------|
| `start_date` | تاریخ شروع (YYYY/MM/DD) | "1403/01/01" |
| `end_date` | تاریخ پایان | "1403/01/31" |
| `daily_start_time` | شروع روزانه (HH:MM) | "09:00" |
| `daily_end_time` | پایان روزانه | "17:00" |
| `session_duration` | مدت جلسه (دقیقه) | 30 |
| `break_duration` | استراحت بین جلسات | 10 |
| `price` | قیمت | 50000 |
| `notes` | یادداشت | "کلاس" |

**مثال:**
```bash
curl -X POST 'http://localhost:8000/api/teacher/availability/bulk-create/' \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "start_date": "1403/01/01",
    "end_date": "1403/01/31",
    "daily_start_time": "09:00",
    "daily_end_time": "17:00",
    "session_duration": 30,
    "break_duration": 10,
    "price": 50000
  }'
```

**پاسخ 201:**
```json
{
  "count": 62,
  "message": "بازه‌های زمانی با موفقیت ایجاد شدند"
}
```

**محاسبه:** 31 روز × (8 ساعت ÷ (30 + 10 دقیقه)) = ۶۲ جلسه

---

### 4️⃣ ویرایش بازه

```http
PATCH /api/teacher/availability/{id}/update/
```

**بدنه:**
```json
{
  "price": 120000,
  "discount_price": 100000,
  "is_available": true,
  "notes": "قیمت افزایش یافت"
}
```

**پاسخ 200:**
```json
{
  "id": 1,
  "teacher": 1,
  "date": "1403/01/15",
  "start_time": "09:00:00",
  "end_time": "10:00:00",
  "price": "120000.00",
  "discount_price": "100000.00",
  "is_available": true,
  "is_booked": false,
  "notes": "قیمت افزایش یافت",
  "message": "بازه زمانی با موفقیت ویرایش شد"
}
```

⚠️ **محدودیت:** نمی‌توان بازه رزرو شده را تغییر داد

---

### 5️⃣ حذف بازه

```http
DELETE /api/teacher/availability/{id}/delete/
```

**درخواست:**
```bash
curl -X DELETE 'http://localhost:8000/api/teacher/availability/1/delete/' \
  -H 'Authorization: Bearer TOKEN'
```

**پاسخ 204** (بدون محتوا)

⚠️ **محدودیت:** نمی‌توان بازه رزرو شده را حذف کرد

---

## Model Methods

```python
# رزرو کردن بازه
availability.reserve()  # is_booked = True

# آزاد کردن بازه (لغو رزرو)
availability.release()  # is_booked = False

# تاریخ شمسی
print(availability.get_jalali_date())  # "1403/01/15"
```

---

## Database Indexes

```python
indexes = [
    models.Index(fields=['teacher', 'date']),
    models.Index(fields=['teacher', 'is_available']),
    models.Index(fields=['date', 'is_available']),
]
```

**فائده:** جستجو سریع‌تر برای:
- فیلتر بر حسب معلم و تاریخ
- فیلتر بر حسب دسترسی‌پذیری

---

## Unique Constraints

```
unique_together = ('teacher', 'date', 'start_time', 'end_time')
```

🔒 **معنی:** یک معلم نمی‌تواند در یک تاریخ و ساعت خاص بیش از یک بازه زمانی داشته باشد.

---

## کد نمونه (Python/Django)

### دریافت بازه‌های یک معلم

```python
from classroom.models import TeacherAvailability
from datetime import date

# تمام بازه‌های معلم شماره 1
slots = TeacherAvailability.objects.filter(teacher_id=1)

# فقط برای امروز
today = date.today()
today_slots = TeacherAvailability.objects.filter(
    teacher_id=1,
    date=today
)

# فقط موجود (رزرو نشده)
available_slots = TeacherAvailability.objects.filter(
    teacher_id=1,
    is_available=True,
    is_booked=False
)

# محدوده تاریخی
from datetime import date
start = date(1403, 1, 1)
end = date(1403, 1, 31)

monthly_slots = TeacherAvailability.objects.filter(
    teacher_id=1,
    date__gte=start,
    date__lte=end
)
```

### ایجاد بازه‌های گروهی

```python
from classroom.models import TeacherAvailability
from datetime import datetime, timedelta
from decimal import Decimal
import jdatetime

# تاریخ‌های شمسی را به میلادی تبدیل کنید
start_date = jdatetime.datetime.strptime('1403/01/01', '%Y/%m/%d').togregorian().date()
end_date = jdatetime.datetime.strptime('1403/01/31', '%Y/%m/%d').togregorian().date()

# زمان‌ها
daily_start = datetime.strptime('09:00', '%H:%M').time()
daily_end = datetime.strptime('17:00', '%H:%M').time()

# جلسات ۳۰ دقیقه‌ای با ۱۰ دقیقه استراحت
session_duration = 30
break_duration = 10
price = Decimal('50000')

# ایجاد جلسات
cur_date = start_date
while cur_date <= end_date:
    cursor = datetime.combine(cur_date, daily_start)
    day_end = datetime.combine(cur_date, daily_end)
    
    while cursor + timedelta(minutes=session_duration) <= day_end:
        slot_start = cursor.time()
        slot_end = (cursor + timedelta(minutes=session_duration)).time()
        
        # بررسی تکراری نبودن
        if not TeacherAvailability.objects.filter(
            teacher_id=1,
            date=cur_date,
            start_time=slot_start,
            end_time=slot_end
        ).exists():
            TeacherAvailability.objects.create(
                teacher_id=1,
                date=cur_date,
                start_time=slot_start,
                end_time=slot_end,
                price=price,
                is_available=True,
                notes='کلاس آنلاین'
            )
        
        cursor += timedelta(minutes=session_duration + break_duration)
    
    cur_date += timedelta(days=1)
```

### رزرو و لغو رزرو

```python
# رزرو کردن بازه
slot = TeacherAvailability.objects.get(id=5)
slot.reserve()  # is_booked = True

# لغو رزرو
slot.release()  # is_booked = False
```

### ویرایش قیمت

```python
from decimal import Decimal

# تغییر قیمت یک بازه
slot = TeacherAvailability.objects.get(id=5)
slot.price = Decimal('120000')
slot.discount_price = Decimal('100000')
slot.save()

# تغییر قیمت تمام بازه‌های یک معلم
TeacherAvailability.objects.filter(teacher_id=1).update(
    price=Decimal('150000')
)
```

---

## کد نمونه (React Native)

### دریافت بازه‌ها

```javascript
const fetchAvailability = async (teacherId, date) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/teacher/availability/?teacher_id=${teacherId}&date=${date}`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const data = await response.json();
    setSlots(data.results);
    return data.results;
  } catch (error) {
    console.error('Error:', error);
    showError('خطا در دریافت بازه‌ها');
  }
};
```

### ایجاد بازه‌های گروهی

```javascript
const createBulkSlots = async (startDate, endDate, startTime, endTime) => {
  try {
    const response = await fetch(
      'http://localhost:8000/api/teacher/availability/bulk-create/',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          start_date: startDate,  // "1403/01/01"
          end_date: endDate,      // "1403/01/31"
          daily_start_time: startTime,  // "09:00"
          daily_end_time: endTime,      // "17:00"
          session_duration: 30,
          break_duration: 10,
          price: 50000,
          notes: 'کلاس آنلاین'
        })
      }
    );
    
    const result = await response.json();
    showSuccess(`${result.count} جلسه ایجاد شد`);
    return result;
  } catch (error) {
    console.error('Error:', error);
    showError('خطا در ایجاد بازه‌ها');
  }
};
```

### ویرایش قیمت

```javascript
const updatePrice = async (slotId, newPrice) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/teacher/availability/${slotId}/update/`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          price: newPrice
        })
      }
    );
    
    const result = await response.json();
    showSuccess('قیمت تغییر کرد');
    return result;
  } catch (error) {
    console.error('Error:', error);
    showError('خطا در تغییر قیمت');
  }
};
```

### حذف بازه

```javascript
const deleteSlot = async (slotId) => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/teacher/availability/${slotId}/delete/`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      }
    );
    
    if (response.status === 204) {
      showSuccess('بازه حذف شد');
      // رفرش لیست
      fetchAvailability();
    }
  } catch (error) {
    console.error('Error:', error);
    showError('خطا در حذف بازه');
  }
};
```

---

---

## خطاهای معمول و حل‌ها

### ❌ خطا: 400 Bad Request - Invalid date format

```
Error: فرمت تاریخ نادرست است. لطفاً از فرمت YYYY/MM/DD استفاده کنید
```

**علت:** تاریخ بدون "/" فرستاده شده

**درخواست اشتباه:**
```bash
curl -X POST /api/teacher/availability/bulk-create/ \
  -d '{"start_date": "14030101", ...}'  # ❌ غلط
```

**درخواست درست:**
```bash
curl -X POST /api/teacher/availability/bulk-create/ \
  -d '{"start_date": "1403/01/01", ...}'  # ✅ درست
```

---

### ❌ خطا: 400 Bad Request - Cannot update booked slot

```
Error: این بازه زمانی رزرو شده است و نمی‌تواند تغییر کند
```

**علت:** تلاش برای تغییر بازه رزرو شده

**راه حل:**
1. اگر غیر ضروری است، بازه را حذف کنید (اگر ممکن باشد)
2. بازه جدید ایجاد کنید
3. رزرو را لغو کنید (اگر مالک رزرو باشید)

```python
# تا زمانی که رزرو شده است، نمی‌توان تغییر داد
slot = TeacherAvailability.objects.get(id=5)
if slot.is_booked:
    slot.release()  # لغو رزرو
    slot.price = 120000  # سپس تغییر دهید
    slot.save()
```

---

### ❌ خطا: 403 Forbidden - Not slot owner

```
Error: شما دسترسی به این بازه زمانی ندارید
```

**علت:** تلاش برای تغییر/حذف بازه معلم دیگری

**راه حل:**
- تنها بازه‌های خود را تغییر دهید
- اگر معلم دیگری هستید، نمی‌توانید ویرایش کنید

```python
# بررسی مالکیت
slot = TeacherAvailability.objects.get(id=5)
if slot.teacher_id == current_user.id:
    # می‌توانید تغییر دهید
    slot.price = 120000
    slot.save()
else:
    # خطا: شما مالک نیستید
    print("You are not the owner")
```

---

### ❌ خطا: 404 Not Found

```
Error: بازه زمانی یافت نشد
```

**علت:** شناسه نادرست یا بازه حذف شده

**راه حل:**
```bash
# ابتدا لیست بازه‌ها را ببینید
GET /api/teacher/availability/

# سپس شناسه درست را استفاده کنید
PATCH /api/teacher/availability/5/update/
```

---

### ❌ خطا: 401 Unauthorized

```
Error: Token required / توکن مورد نیاز است
```

**علت:** توکن فرستاده نشده یا منقضی شده

**راه حل:**
```bash
# توکن را دوباره دریافت کنید
POST /api/verify-otp/
{
  "identifier": "09121234567",
  "code": "123456"
}

# سپس با توکن جدید درخواست بفرستید
curl -H "Authorization: Bearer NEW_TOKEN" \
  http://localhost:8000/api/teacher/availability/
```

---

## بهترین شیوه‌ها

✅ **نکات مثبت:**
1. **محاسبه صحیح:** session_duration و break_duration را درست تنظیم کنید
2. **قیمت معقول:** قیمت‌های رقابتی قرار دهید
3. **یادداشت واضح:** مشخص کنید چه نوع کلاسی است
4. **تحدیث منظم:** ساعات خود را بروز نگاه دارید
5. **محدوده کافی:** حداقل یک ماه قبل از وقت تعریف کنید

❌ **اشتباع‌های معمول:**
1. ❌ فراموش کردن break_duration → جلسات متداخل
2. ❌ قیمت خیلی کم → کیفیت کمتر
3. ❌ بدون یادداشت → دانش‌آموزان نمی‌فهمند
4. ❌ ساعات غیرمنطقی → دانش‌آموزان نمی‌توانند رزرو کنند
5. ❌ فراموش کردن اپدیت → بازه‌های قدیمی باقی می‌ماند

---

## محاسبه‌های مثال

### مثال 1: جلسات ۳۰ دقیقه‌ای

```
start_date: 1403/01/01
end_date: 1403/01/31
daily_start_time: 09:00
daily_end_time: 17:00
session_duration: 30 دقیقه
break_duration: 10 دقیقه

محاسبه:
- هر روز: 8 ساعت = 480 دقیقه
- هر چرخه: 30 + 10 = 40 دقیقه
- تعداد جلسات در روز: 480 ÷ 40 = 12 جلسه
- تعداد کل: 31 روز × 12 جلسه = 372 جلسه

جلسات:
09:00-09:30, 09:40-10:10, 10:20-10:50, 11:00-11:30,
11:40-12:10, 12:20-12:50, 13:00-13:30, 13:40-14:10,
14:20-14:50, 15:00-15:30, 15:40-16:10, 16:20-16:50
```

### مثال 2: جلسات ۴۵ دقیقه‌ای

```
session_duration: 45 دقیقه
break_duration: 15 دقیقه

محاسبه:
- هر چرخه: 45 + 15 = 60 دقیقه = 1 ساعت
- تعداد جلسات در روز: 480 ÷ 60 = 8 جلسه
- تعداد کل: 31 روز × 8 جلسه = 248 جلسه

جلسات:
09:00-09:45, 10:00-10:45, 11:00-11:45, 12:00-12:45,
13:00-13:45, 14:00-14:45, 15:00-15:45, 16:00-16:45
```

### مثال 3: جلسات ۶۰ دقیقه‌ای (یک ساعت)

```
session_duration: 60 دقیقه
break_duration: 20 دقیقه

محاسبه:
- هر چرخه: 60 + 20 = 80 دقیقه
- تعداد جلسات در روز: 480 ÷ 80 = 6 جلسه
- تعداد کل: 31 روز × 6 جلسه = 186 جلسه

جلسات:
09:00-10:00, 10:20-11:20, 11:40-12:40, 13:00-14:00,
14:20-15:20, 15:40-16:40
```

---

## Swagger/OpenAPI

تمام endpoints در Swagger قابل دسترس هستند:

```
http://localhost:8000/api/swagger/
```

یا ReDoc:

```
http://localhost:8000/api/redoc/
```

---

## مراجع و لینک‌ها

### کد منبع
- **Model:** [classroom/models.py](classroom/models.py#L14)
- **Views:** [api/views.py](api/views.py#L2161)
- **Serializer:** [api/classroom_serializers.py](api/classroom_serializers.py#L36)
- **URLs:** [api/urls.py](api/urls.py#L65)

### الگوهای مرتبط
- [Teaching Subject Management](TEACHING_SUBJECT_API.md)
- [Exercise API](MOBILE_APP_API_INTEGRATION.md)

---

## پشتیبانی

برای سوال‌ها و مشکلات:
- 📧 **Email:** support@fofofish.com
- 💬 **Chat:** در اپلیکیشن
- 📞 **Phone:** +98-21-XXXX-XXXX
- 📖 **Documentation:** https://docs.fofofish.com

---

**آخرین به‌روز رسانی:** December 30, 2025
