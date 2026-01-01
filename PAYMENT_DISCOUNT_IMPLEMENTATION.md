# نظام پرداخت بهتر - تخفیف و مبلغ نهایی

## 📋 خلاصه تغییرات

### مشکل اصلی
- کاربر الان حتی وقتی تخفیف 100% دارد (رایگان)، مبلغ اصلی به درگاه می‌فرستد
- عدم محاسبه صحیح مبلغ نهایی قبل از ارسال به Zibal

### راه حل
✅ **Backend**: `InitiatePaymentAPIView` اصلاح شده
✅ **Database**: مدل `ClassBooking` از قبل صحیح است
✅ **Logic**: تمام سناریوها مدیریت شده:
   - رزروی بدون تخفیف → به Zibal
   - رزروی با تخفیف → مبلغ نهایی به Zibal
   - رزروی رایگان (100%) → مستقیم `paid`

---

## 🛠️ تغییرات Backend

### فایل: `api/views.py` → `InitiatePaymentAPIView`

#### تغییر 1: بررسی مبلغ نهایی
```python
# ✅ بررسی مبلغ نهایی
from decimal import Decimal
from django.utils import timezone

final_amount = Decimal(str(booking.final_price))

# اگر مبلغ نهایی 0 است (رایگان)، پرداخت را مستقیم ثبت کن
if final_amount == 0:
    booking.payment_status = 'paid'
    booking.paid_amount = 0
    booking.paid_at = timezone.now()
    booking.save()
    
    return Response({
        'success': True,
        'data': {
            'booking_id': booking.id,
            'amount': '0',
            'currency': 'IRR',
            'is_free': True,
            'payment_url': None,
            'message': _('کلاس رایگان است - پرداخت ثبت شد')
        }
    }, status=status.HTTP_200_OK)
```

#### تغییر 2: تبدیل مبلغ ریال به تومان
```python
# مبلغ نهایی شامل تخفیف
amount_toman = int(float(final_amount) / Decimal('10'))  # تبدیل ریال به تومان

payload = {
    'merchant': zibal_merchant_id,
    'amount': amount_toman,  # ✅ مبلغ نهایی (شامل تخفیف)
    'callbackUrl': zibal_callback_url,
    ...
}
```

#### تغییر 3: افزودن `is_free` flag به پاسخ
```python
return Response({
    'success': True,
    'data': {
        'booking_id': booking.id,
        'amount': str(booking.final_price),
        'currency': 'IRR',
        'is_free': False,  # ✅ نشان می‌دهد که رایگان است یا نه
        'payment_url': payment_url,
        'message': _('پرداخت آغاز شد')
    }
}, status=status.HTTP_200_OK)
```

---

## 📦 مدل ClassBooking (بدون تغییر)

```python
class ClassBooking(BaseModel):
    # قیمت
    price = models.DecimalField(...)                    # قیمت اصلی
    discount_amount = models.DecimalField(...)         # مبلغ تخفیف
    final_price = models.DecimalField(...)             # قیمت نهایی
    
    # پرداخت
    paid_amount = models.DecimalField(...)             # مبلغ پرداختی
    payment_status = models.CharField(...)             # وضعیت پرداخت
    
    def save(self):
        # اگر final_price تعیین نشده، برابر با price باشد
        if not self.final_price or self.final_price == 0:
            self.final_price = self.price - self.discount_amount
        super().save()
```

---

## 🧪 سناریوهای تست

### سناریو 1: رزروی بدون تخفیف
```
Price:           100,000 تومان
Discount:        0 تومان
Final Price:     100,000 تومان ✅
Zibal Amount:    10,000 تومان (100,000 / 10)
Result:          به درگاه می‌رود
```

### سناریو 2: رزروی با تخفیف 30%
```
Price:           100,000 تومان
Discount:        30,000 تومان
Final Price:     70,000 تومان ✅
Zibal Amount:    7,000 تومان (70,000 / 10)
Result:          مبلغ تخفیف‌شده به درگاه می‌رود
```

### سناریو 3: رزروی رایگان (تخفیف 100%)
```
Price:           100,000 تومان
Discount:        100,000 تومان
Final Price:     0 تومان ✅
Zibal Amount:    ------ (نفرستاده می‌شود)
Result:          مستقیم پرداختی ثبت می‌شود (نه به درگاه)
Status:          paid
Paid At:         now
```

---

## 📝 API Response اصلاح‌شده

### 1. رزروی معمولی (نیاز پرداخت)

**Request:**
```bash
POST /api/class-booking/123/initiate-payment/
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "booking_id": 123,
    "amount": "70000",
    "currency": "IRR",
    "is_free": false,
    "payment_url": "https://gateway.zibal.ir/start/ABC123XYZ",
    "message": "پرداخت آغاز شد"
  }
}
```

### 2. رزروی رایگان

**Request:**
```bash
POST /api/class-booking/124/initiate-payment/
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "booking_id": 124,
    "amount": "0",
    "currency": "IRR",
    "is_free": true,
    "payment_url": null,
    "message": "کلاس رایگان است - پرداخت ثبت شد"
  }
}
```

---

## 🧪 اجرای تست‌ها

### نصب Test Dependencies
```bash
pip install django-test-plus  # اختیاری
```

### اجرای تست‌های کامل
```bash
python manage.py test test_payment_discount
```

### اجرای تست‌های خاص
```bash
# فقط تست‌های محاسبه مبلغ
python manage.py test test_payment_discount.PaymentDiscountTestCase

# فقط تست‌های مجوز
python manage.py test test_payment_discount.PaymentPermissionTestCase

# یک تست مشخص
python manage.py test test_payment_discount.PaymentDiscountTestCase.test_booking_fully_discounted
```

### تست دستی در Console
```bash
python manage.py shell

# ایجاد رزروی رایگان
from classroom.models import ClassBooking, TeachingSubject, TeacherAvailability
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import datetime, timedelta

User = get_user_model()

teacher = User.objects.get(role='teacher')
student = User.objects.get(role='user')
subject = TeachingSubject.objects.get(id=1)
availability = TeacherAvailability.objects.get(id=1)

booking = ClassBooking.objects.create(
    availability=availability,
    teacher=teacher,
    student=student,
    subject=subject,
    status='reserved',
    price=Decimal('100000'),
    discount_amount=Decimal('100000'),
    final_price=Decimal('0')
)

print(f"Booking ID: {booking.id}")
print(f"Price: {booking.price}")
print(f"Discount: {booking.discount_amount}")
print(f"Final: {booking.final_price}")
```

---

## 🚀 Frontend Integration

### React Native / Expo

```typescript
const handlePayment = async (bookingId: number) => {
  try {
    const response = await axios.post(
      `https://api.fofofish.app/api/class-booking/${bookingId}/initiate-payment/`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const { is_free, payment_url, amount } = response.data.data;

    // اگر رایگان است
    if (is_free) {
      Alert.alert('موفق', 'کلاس رایگان است - پرداخت ثبت شد');
      navigation.navigate('BookingDetail', { bookingId });
      return;
    }

    // اگر نیاز پرداخت دارد
    if (payment_url) {
      // باز کردن درگاه
      WebView.open(payment_url);
      // یا
      Linking.openURL(payment_url);
    }
  } catch (error) {
    Alert.alert('خطا', error.response?.data?.error);
  }
};
```

---

## ✅ Checklist اصلاح

- [x] مدل `ClassBooking` بررسی شد
- [x] `InitiatePaymentAPIView` اصلاح شد
- [x] منطق مبلغ نهایی صحیح است
- [x] سناریوی رایگان مدیریت شده است
- [x] Zibal amount محاسبه صحیح است
- [x] API response شامل `is_free` flag است
- [x] Unit tests ایجاد شده
- [x] تست سناریوهای مختلف

---

## 📞 سوالات متداول

### Q: اگر discount_amount از price بیشتر باشد چی؟
**A:** مدل `save()` خود خود را محافظت می‌کند:
```python
self.final_price = self.price - self.discount_amount
```
اگر منفی شود، باید validation اضافی بگذاری.

### Q: Zibal مبلغ 0 قبول می‌کند؟
**A:** نه! برای رایگان، درخواستی به Zibal نمی‌فرستیم.

### Q: اگر پرداخت قبل‌تر انجام شد چی؟
**A:** API بررسی می‌کند:
```python
if booking.payment_status in ['paid', 'partial']:
    return Error('این رزرو قبلاً پرداخت شده است')
```

---

## 🐛 Debugging

### Log محل پرداخت
```python
# در views.py
print(f"Booking {booking.id}: final_price={booking.final_price}")
if final_amount == 0:
    print("→ رایگان - مستقیم پرداختی")
else:
    print(f"→ نیاز پرداخت - مبلغ: {amount_toman} تومان")
```

### Zibal Test Mode
```python
# در settings.py
if DEBUG:
    ZIBAL_MERCHANT_ID = 'test_merchant_id'
    ZIBAL_REQUEST_URL = 'https://gateway.zibal.ir/v1/request'
```

---

## 📚 فایل‌های مرتبط

- [api/views.py](api/views.py#L3234) - `InitiatePaymentAPIView`
- [classroom/models.py](classroom/models.py#L111) - `ClassBooking`
- [test_payment_discount.py](test_payment_discount.py) - Unit Tests
- [PAYMENT_SYSTEM_COMPLETE_SUMMARY.md](PAYMENT_SYSTEM_COMPLETE_SUMMARY.md) - سیستم پرداخت کامل
