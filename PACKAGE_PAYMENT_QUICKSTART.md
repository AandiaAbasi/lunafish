# 🎓 Package Installment Payment System - Quick Start

**سیستم قسط‌بندی بسه‌های آموزشی - راهنمای سریع**

---

## 🚀 بدون کجا شروع کنیم؟

### 📖 اگر می‌خواهید بدانید این سیستم چیست:
👉 بخش را بخوانید: **[What is Package Installment?](PACKAGE_PAYMENT_API_GUIDE.md#-خلاصه-سیستم)**

### 🔌 اگر می‌خواهید API Endpoints را استفاده کنید:
👉 سند را دنبال کنید: **[PACKAGE_PAYMENT_API_GUIDE.md](PACKAGE_PAYMENT_API_GUIDE.md)**

### 💻 اگر می‌خواهید کد بنویسید:
👉 نمونه‌ها را ببینید: **[PACKAGE_PAYMENT_INTEGRATION_EXAMPLES.py](PACKAGE_PAYMENT_INTEGRATION_EXAMPLES.py)**

### 🏗️ اگر می‌خواهید معماری را درک کنید:
👉 سند را بخوانید: **[PACKAGE_INSTALLMENT_IMPLEMENTATION.md](PACKAGE_INSTALLMENT_IMPLEMENTATION.md)**

### ✅ اگر می‌خواهید تست کنید:
👉 اسکریپت را اجرا کنید: **[test_package_payment.py](test_package_payment.py)**

---

## ⚡ 5-Minute Overview

### 🎯 مسئله:
دانش‌آموزان می‌خواهند بسه‌های آموزشی را به قسط خریداری کنند، نه یکجا.

### ✅ حل:
```
دانش‌آموز ثبت‌نام میکند
        ↓
اقساط خودکار ایجاد میشوند
        ↓
دانش‌آموز هر قسط را در موقع مربوطه پرداخت می‌کند
        ↓
تنها اگر اقساط قبل از آن جلسه پرداخت شده، دسترسی دارد
        ↓
✅ همه خوشحال!
```

### 📱 3 API برای Frontend:

#### 1. بررسی دسترسی قبل از شرکت در جلسه:
```javascript
POST /api/packages/check-session-access/
{
  "enrollment_id": 5,
  "session_number": 3
}
```

#### 2. پرداخت قسط:
```javascript
POST /api/packages/process-payment/
{
  "enrollment_id": 5,
  "phone": "09123456789"
}
// Response: {payment_url: "https://gateway.zibal.ir/start/ABC123"}
// → User redirects to Zibal
```

#### 3. دریافت وضعیت (خودکار):
```
Zibal calls backend:
GET /api/packages/verify-payment/?trackId=ABC123&status=100
→ Payment confirmed ✅
```

---

## 📁 فایل‌های اصلی

| فایل | توضیح |
|------|--------|
| `api/package_service.py` | منطق تجاری |
| `api/views.py` | 5 API endpoint |
| `api/urls.py` | مسیرهای API |
| `api/classroom_serializers.py` | Serializers |
| `PACKAGE_PAYMENT_API_GUIDE.md` | 📖 API راهنما |
| `test_package_payment.py` | 🧪 تست‌ها |
| `PACKAGE_PAYMENT_INTEGRATION_EXAMPLES.py` | 💻 نمونه کدها |

---

## 🔥 استفاده سریع

### برای React Developer:

```javascript
import axios from 'axios';

// 1. بررسی دسترسی
const checkAccess = async (enrollmentId, sessionNumber) => {
  const res = await axios.post('/api/packages/check-session-access/', {
    enrollment_id: enrollmentId,
    session_number: sessionNumber
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });
  
  if (!res.data.can_access) {
    // نمایش دکمه پرداخت
    return false;
  }
  return true;
};

// 2. پرداخت
const initiatePayment = async (enrollmentId, phone) => {
  const res = await axios.post('/api/packages/process-payment/', {
    enrollment_id: enrollmentId,
    phone: phone
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });
  
  // کاربر را به Zibal ببرید
  window.location.href = res.data.payment_url;
};
```

### برای Django Developer:

```python
from api.package_service import PackageInstallmentService
from classroom.models import StudentPackageEnrollment

# بررسی دسترسی
enrollment = StudentPackageEnrollment.objects.get(id=5)
can_access, message = PackageInstallmentService.can_student_attend_session(
    enrollment,
    session_number=3
)

if can_access:
    # دانش‌آموز می‌تواند وارد شود
    pass
else:
    # پیام خطا: message
    pass
```

---

## 🧪 تست سریع

```bash
# تست‌های کامل
python test_package_payment.py

# یا در Python
from test_package_payment import run_full_test
run_full_test()
```

---

## 🎯 10 مراحل برای اجرا

### مرحله 1: بررسی فایل‌ها
```
✅ api/package_service.py وجود دارد
✅ api/views.py به‌روز شده است
✅ api/urls.py به‌روز شده است
✅ api/classroom_serializers.py به‌روز شده است
```

### مرحله 2: بررسی Models
```python
from classroom.models import (
    Package,
    PackageInstallment,
    StudentPackageEnrollment,
    StudentPackagePayment
)
```

### مرحله 3: تست API
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/packages/
```

### مرحله 4: بررسی دسترسی
```bash
curl -X POST -H "Authorization: Bearer TOKEN" \
  -d '{"enrollment_id": 1, "session_number": 3}' \
  http://localhost:8000/api/packages/check-session-access/
```

### مرحله 5: پرداخت
```bash
curl -X POST -H "Authorization: Bearer TOKEN" \
  -d '{"enrollment_id": 1, "phone": "09123456789"}' \
  http://localhost:8000/api/packages/process-payment/
```

### مرحله 6-10: استقرار
- مایگریشن (`python manage.py migrate`)
- تست محیط production
- مانیتورینگ (Sentry/New Relic)
- Backup (Database)
- سرویس‌ logs

---

## 🔐 نکات امنیتی

- ✅ JWT Authentication (تمام endpoints)
- ✅ User ownership checks (تنها داده‌های خود)
- ✅ HTTPS enforced (production)
- ✅ Zibal API verification (هر پرداخت)
- ✅ SQL Injection prevention (ORM)
- ✅ CSRF protection (Django middleware)

---

## 🐛 اگر خطایی رخ داد

### ❌ خطا: "Package not found"
```python
# Check:
Package.objects.filter(is_active=True, has_installment=True).count()
```

### ❌ خطا: "Enrollment not found"
```python
# Check:
StudentPackageEnrollment.objects.filter(student=request.user).count()
```

### ❌ خطا: "No pending installment"
```python
# Check:
enrollment.installment_payments.filter(payment_status__in=['pending', 'partial']).count()
```

### ❌ خطا: "Zibal error"
```python
# Check SETTINGS:
print(settings.ZIBAL_MERCHANT_ID)
print(settings.ZIBAL_REQUEST_URL)
print(settings.ZIBAL_VERIFY_URL)
```

---

## 📊 نمودار سریع

```
User Timeline:
├─ Day 1: ثبت‌نام در بسه
│         └─ Installments created
├─ Day 5: بررسی دسترسی → ❌ (قسط 1 معلق)
│         └─ Button: "Pay Now"
├─ Day 5: کلیک "Pay Now"
│         └─ Zibal gateway opens
├─ Day 5: پرداخت در Zibal
│         └─ Callback to backend
├─ Day 5: ✅ دسترسی فعال
│         └─ Can enter session
└─ Day 90: تمام اقساط پرداخت
           └─ Status = 'completed'
```

---

## 💡 بهترین روش‌ها

### ✅ DO:
```python
# 1. همیشه دسترسی را بررسی کنید
can_access, msg = PackageInstallmentService.can_student_attend_session(...)

# 2. Transaction استفاده کنید
with transaction.atomic():
    payment.payment_status = 'paid'
    payment.save()

# 3. Error handling داشته باشید
try:
    enrollment = StudentPackageEnrollment.objects.get(id=enrollment_id)
except StudentPackageEnrollment.DoesNotExist:
    return Response(..., status=404)
```

### ❌ DON'T:
```python
# 1. بدون authorization
# ❌ enrollment = StudentPackageEnrollment.objects.get(id=id)
# ✅ enrollment = StudentPackageEnrollment.objects.get(id=id, student=request.user)

# 2. بدون verification
# ❌ payment.payment_status = 'paid'  (فقط اگر Zibal تأیید کرد)

# 3. بدون error handling
# ❌ amount = verify_data['amount']
# ✅ amount = verify_data.get('amount', 0)
```

---

## 🎓 مثال کامل (Frontend)

### React Component:

```javascript
import React, { useState, useEffect } from 'react';

export const PaymentFlow = ({ enrollmentId }) => {
  const [canAccess, setCanAccess] = useState(null);
  const [phone, setPhone] = useState('');
  
  // 1. Check access on mount
  useEffect(() => {
    checkAccess();
  }, []);
  
  // 2. Check access function
  const checkAccess = async () => {
    const res = await fetch('/api/packages/check-session-access/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        enrollment_id: enrollmentId,
        session_number: 1
      })
    });
    
    const data = await res.json();
    setCanAccess(data.can_access);
  };
  
  // 3. Payment handler
  const handlePayment = async () => {
    const res = await fetch('/api/packages/process-payment/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        enrollment_id: enrollmentId,
        phone: phone
      })
    });
    
    const data = await res.json();
    
    if (data.success) {
      window.location.href = data.payment_url; // ← Go to Zibal
    }
  };
  
  // 4. Render
  if (canAccess === null) return <p>Checking access...</p>;
  
  if (!canAccess) {
    return (
      <div>
        <p>❌ Access denied - Pay to continue</p>
        <input 
          value={phone} 
          onChange={e => setPhone(e.target.value)}
          placeholder="Phone"
        />
        <button onClick={handlePayment}>Pay Now</button>
      </div>
    );
  }
  
  return <p>✅ Access granted - Enter session</p>;
};
```

---

## 📞 سوالات متداول

**Q: مدت زمان پرداخت چقدر است؟**
> 2-3 ثانیه (بعد از کلیک در Zibal)

**Q: آیا می‌توانم کمیسیون Zibal را تغییر دهم؟**
> نه (Zibal تنظیمات)

**Q: آیا می‌توانم پرداخت را بازگردانم؟**
> بله (manual در admin)

**Q: اگر دانش‌آموز بدون پرداخت وارد شود؟**
> `check-session-access` بررسی می‌کند → false → blocked

---

## 🚀 Ready to Deploy?

```bash
# Step 1: Check
python manage.py check

# Step 2: Migrate
python manage.py makemigrations && python manage.py migrate

# Step 3: Collect static
python manage.py collectstatic --noinput

# Step 4: Test
python manage.py test

# Step 5: Deploy
git push heroku main
# or
docker build -t myapp . && docker push myapp
# or
scp -r . user@server:/app/
```

---

## 📚 اسناد کامل

1. **API Guide:** [PACKAGE_PAYMENT_API_GUIDE.md](PACKAGE_PAYMENT_API_GUIDE.md)
2. **Implementation:** [PACKAGE_INSTALLMENT_IMPLEMENTATION.md](PACKAGE_INSTALLMENT_IMPLEMENTATION.md)
3. **Examples:** [PACKAGE_PAYMENT_INTEGRATION_EXAMPLES.py](PACKAGE_PAYMENT_INTEGRATION_EXAMPLES.py)
4. **Tests:** [test_package_payment.py](test_package_payment.py)
5. **Summary:** [PACKAGE_PAYMENT_COMPLETION_SUMMARY.md](PACKAGE_PAYMENT_COMPLETION_SUMMARY.md)

---

## ✨ خلاصه

```
✅ 5 API Endpoints
✅ Payment via Zibal
✅ Session Access Control
✅ Clean Architecture
✅ Production Ready

Ready to go! 🚀
```

---

**نسخه:** ۱.۰  
**تاریخ:** ۱ اسفند ۱۴۰۲  
**وضعیت:** ✅ Complete
